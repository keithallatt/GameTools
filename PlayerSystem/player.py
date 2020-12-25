from __future__ import annotations
from InventorySystem.inventory import Inventory, Item
from colorama import Back, Fore, Style
import numpy as np
import math
from ansiwrap import *
from typing import Type


class PointSystem:
    def __init__(self, name: str):
        self.point_system_name = name
        self.level = 0
        self.exp_per_level_coefficients = np.array([1.])

    def limit_for_level(self, level: int):
        pass

    def gain_points(self, points: int) -> int:
        pass

    def display_bar(self, bar=False, bar_length: int = 20):
        pass

    def set_according_to_level(self, level: int):
        pass


class ExpSys(PointSystem):
    def __init__(self, level: int = 1, exp: int = 0,
                 exp_per_level_coefficients: np.array = None):
        super().__init__("Experience")
        self.exp = exp
        self.level = level
        self.exp_per_level_coefficients = exp_per_level_coefficients
        if exp_per_level_coefficients is None:
            self.exp_per_level_coefficients = np.array([1., 1.003, -0.2, 0.8], dtype=np.float64)

        self.max_exp = self.limit_for_level(level)

    def set_according_to_level(self, level: int):
        self.level = level
        self.max_exp = self.limit_for_level(level)

    def limit_for_level(self, level: int):
        coefficients = self.exp_per_level_coefficients
        level_arr = np.repeat(level, coefficients.shape[0])
        exponents = np.arange(0, coefficients.shape[0])
        return int(np.round(np.sum(coefficients * (level_arr ** exponents))))

    def __str__(self):
        return f"{self.exp} / {self.max_exp} EXP"

    def gain_points(self, points):
        self.exp += points
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.set_according_to_level(self.level + 1)

        return self.level

    def display_bar(self, bar=False, bar_length: int = 20):
        if self.exp is None or self.max_exp is None:
            return ""
        if bar:
            return "|" + Fore.YELLOW + Back.YELLOW + \
                   "#" * (bar_length * self.exp // self.max_exp) + Style.RESET_ALL + \
                   " " * (bar_length - (bar_length * self.exp // self.max_exp)) + "|"
        else:
            return self.__str__()


class HealthSys(PointSystem):
    def __init__(self, level: int = 1, hp_per_level_coefficients: np.array = None):
        super().__init__("Health")
        self.hp_per_level_coefficients = hp_per_level_coefficients
        if hp_per_level_coefficients is None:
            self.hp_per_level_coefficients = np.array([8., 1., 0.5], dtype=np.float64)
        self.level = level
        self.hp = self.max_hp = self.limit_for_level(level)

    def set_according_to_level(self, level: int):
        self.level = level
        hp_up = self.limit_for_level(level) - self.max_hp
        self.hp += hp_up
        self.max_hp += hp_up

    def limit_for_level(self, level: int):
        coefficients = self.hp_per_level_coefficients
        level_arr = np.repeat(level, coefficients.shape[0])
        exponents = np.arange(0, coefficients.shape[0])
        return int(np.round(np.sum(coefficients * (level_arr ** exponents))))

    def __str__(self):
        return f"{self.hp} / {self.max_hp} HP"

    def gain_points(self, points):
        self.hp += points
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.hp < 0:
            self.hp = 0

    def display_bar(self, bar=False, bar_length: int = 20):
        if self.hp is None or self.max_hp is None:
            return ""
        if bar:

            ratio = self.hp / self.max_hp
            if ratio <= 0.2:
                color = Fore.RED + Back.RED
            elif ratio <= 0.5:
                color = Fore.LIGHTYELLOW_EX + Back.LIGHTYELLOW_EX
            else:
                color = Fore.GREEN + Back.GREEN

            return "|" + color + color + \
                   "#" * math.ceil(bar_length * self.hp / self.max_hp) + Style.RESET_ALL + \
                   " " * (bar_length - math.ceil(bar_length * self.hp / self.max_hp)) + "|"
        else:
            return self.__str__()


class PlayerException(Exception):
    def __init__(self, msg: str = None):
        super().__init__(msg)
        self.msg = msg


class PlayerSystem:
    """ Represents a playable character
        A lot of inspiration came from
        http://howtomakeanrpg.com/a/how-to-make-an-rpg-levels.html
    """
    def __init__(self,
                 level: int = 1,
                 point_systems: list[PointSystem] = None,
                 inventory: Inventory = None):
        self.point_systems = point_systems
        experience_systems = [
               p_sys for p_sys in point_systems if type(p_sys) is ExpSys
        ]
        if len(experience_systems) >= 1:
            self.exp_sys = experience_systems[0]
        else:
            self.exp_sys = None

        p_s_types = [
            type(p_s) for p_s in point_systems
        ]
        if len(p_s_types) != len(set(p_s_types)):
            raise PlayerException("More than one of same system type")

        if self.point_systems is None:
            self.point_systems = []
        for ps in self.point_systems:
            ps.set_according_to_level(level)

        if inventory is None:
            self.inventory = Inventory()
        else:
            self.inventory = inventory

    def __str__(self):
        level = None
        if self.exp_sys is not None:
            level = self.exp_sys.level

        max_len = 0
        str_repr = ""
        for ps in self.point_systems:
            max_len = max(max_len, ansilen(ps.display_bar(bar=True) + "  " + str(ps)))
            str_repr += ps.display_bar(bar=True) + "  " + str(ps)
            str_repr += "\n"

        str_repr = "\n".join(["-"*max_len, str_repr.strip(), "-"*max_len])

        if level is not None:
            str_repr = "-"*max_len + "\n|\tLevel "+str(level) + "\n" + str_repr

        if self.inventory is not None:
            str_repr += "\n\tInventory:\n" + str(self.inventory)

        return str_repr

    def _gain_points(self, points: int, system_type: Type):
        if not issubclass(system_type, PointSystem):
            raise PlayerException("Method called with system type not inherited from PointSystem")

        for point_sys in self.point_systems:
            if type(point_sys) == system_type:
                # do the thing
                level = point_sys.gain_points(points)
                if level is not None:
                    for iter_sys in self.point_systems:
                        iter_sys.set_according_to_level(level)

                break
        else:
            raise PlayerException("Gain Points called with system type not included in player")

    def _add_to_inventory(self, item: Item = None, payment: int = None):
        pass

    def _remove_from_inventory(self, item: Item = None, payment: int = None):
        pass


if __name__ == "__main__":
    pass