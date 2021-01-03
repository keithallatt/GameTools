from __future__ import annotations
from InventorySystem.inventory import Inventory, Item, InventoryException
from InventorySystem.currency import Wallet, CurrencySystem
import numpy as np
import math
from ansiwrap import *
from typing import Type


class PlayerException(Exception):
    """ Basic exception for errors raised by the player / point system. """
    def __init__(self, msg: str = None):
        """ Basic exception for errors raised by the player / point system. """
        super().__init__(msg)
        self.msg = msg


class PointSystem:
    """ Represents a generalized point system.
        Can be used for experience (ExpSys)
        or health points (HealthSys)
        or magic, stamina, etc. """
    def __init__(self, name: str, level: int = 0, level_coefficients: np.array = None):
        """ Generate the point system by name and default parameters. """
        self.point_system_name = name
        self.level = level
        self.level_coefficients = level_coefficients
        if level_coefficients is None:
            self.level_coefficients = np.array([1.])

    def limit_for_level(self, level: int, cumulative: bool = False):
        """ Map level to a value which will specify the limit for the given level.
            If cumulative is true, then the return value should be the new limit.
            If cumulative is false, then the return value should be the limit increase. """
        pass

    def gain_points(self, points: int) -> int:
        """ Increase the count of points the point system is tracking. """
        pass

    def display_bar(self, bar_length: int = 20):
        """ Display the point system as a bar being filled. """
        pass

    def set_according_to_level(self, level: int):
        """ Set the point systems maximum point limit according to the level. """
        pass


class ExpSys(PointSystem):
    """ An Experience Point System for gaining experience to level up a character. """
    def __init__(self, level: int = 1, exp: int = 0,
                 level_coefficients: np.array = None):
        """ Create an experience system with default limit function
            [exp_per_level(L) = 1.0 + 1.003L - 0.2L^2 + 0.8L^3]. """
        super().__init__("Experience", level, np.array([1., 1.003, -0.2, 0.8], dtype=np.float64)
                         if level_coefficients is None else level_coefficients)
        self.exp = exp
        self.max_exp = self.limit_for_level(level)

    def set_according_to_level(self, level: int):
        """ Set the new level and calculate the new max limit. """
        self.level = level
        self.max_exp = self.limit_for_level(level)

    def limit_for_level(self, level: int, cumulative: bool = False):
        """ Calculate the new limit based on the level. """
        if cumulative:
            coefficients = self.level_coefficients
            level_arr = np.repeat(level, coefficients.shape[0])
            exponents = np.arange(0, coefficients.shape[0])
            return int(np.round(np.sum(coefficients * (level_arr ** exponents))))
        else:
            # temporary
            return self.limit_for_level(level, cumulative=True) - \
                   self.limit_for_level(level-1, cumulative=True)

    def __str__(self):
        """ Return as a ratio of current / max experience points. """
        return f"{self.exp} / {self.max_exp} EXP"

    def gain_points(self, points):
        """ Gain experience points, and level up as necessary. """
        self.exp += points
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.set_according_to_level(self.level + 1)

        return self.level

    def display_bar(self, bar_length: int = 20):
        """ Display experience points as a bar being filled. """
        if self.exp is None or self.max_exp is None:
            return ""
        # \u2588 is full block
        return '|'+u'\u2588' * (bar_length * self.exp // self.max_exp) + \
               " " * (bar_length - (bar_length * self.exp // self.max_exp)) + "|"


class HealthSys(PointSystem):
    """ Health Point system to determine the overall health of an NPC, player or enemy. """
    def __init__(self, level: int = 1, level_coefficients: np.array = None):
        """ Create an health point system with default limit function
            [hp_per_level(L) = 8.0 + 1.0L + 0.5L^2]. """
        super().__init__("Health", level, np.array([8., 1., 0.5], dtype=np.float64)
                         if level_coefficients is None else level_coefficients)
        self.hp = self.max_hp = self.limit_for_level(level)

    def set_according_to_level(self, level: int):
        """ Set the new level and calculate the new max limit. """
        self.level = level
        hp_up = self.limit_for_level(level) - self.max_hp
        self.hp += hp_up
        self.max_hp += hp_up

    def limit_for_level(self, level: int, cumulative: bool = False):
        """ Calculate the new limit based on the level. """
        if cumulative:
            coefficients = self.level_coefficients
            level_arr = np.repeat(level, coefficients.shape[0])
            exponents = np.arange(0, coefficients.shape[0])
            return int(np.round(np.sum(coefficients * (level_arr ** exponents))))
        else:
            return self.limit_for_level(level, cumulative=True) - \
                   self.limit_for_level(level-1, cumulative=True)

    def __str__(self):
        """ Return as a ratio of current / max hit points. """
        return f"{self.hp} / {self.max_hp} HP"

    def gain_points(self, points):
        """ Gain hit points, and cap at max / 0 as necessary. """
        self.hp += points
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.hp < 0:
            self.hp = 0

    def display_bar(self, bar_length: int = 20):
        """ Display experience points as a bar being filled. """
        if self.hp is None or self.max_hp is None:
            return ""

        return '|' + u'\u2588' * math.ceil(bar_length * self.hp / self.max_hp) + \
               " " * (bar_length - math.ceil(bar_length * self.hp / self.max_hp)) + "|"


class PlayerSystem:
    """ Represents a playable character
        A lot of inspiration came from
        <a href="http://howtomakeanrpg.com/a/how-to-make-an-rpg-levels.html">Here</a>.
    """
    def __init__(self,
                 level: int = 1,
                 point_systems: list[PointSystem] = None,
                 inventory: Inventory = None,
                 currency_system: CurrencySystem = None,
                 init_wallet: Wallet = None,
                 init_amount: int = 0):
        """ Create a player with many default parameters. """
        if point_systems is None:
            point_systems = []
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

        self.wallet = Wallet(curr_sys=currency_system, amount=init_amount)
        if init_wallet is not None:
            self.wallet = init_wallet

    def __str__(self):
        """ Represent player using the different point systems associated with the player. """
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
            inventory_repr = str(self.inventory)
            label = "Inventory:"

            w = (len(inventory_repr.split("\n")[0]) - len(label)) // 2

            str_repr += "\n" + " " * w + label + "\n" + inventory_repr

        return str_repr

    def _gain_points(self, points: int, system_type: Type):
        """ Add points to the point system of type system_type. """
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

    def _add_to_inventory(self, item: Item = None, payment: Wallet = None):
        """ Add an item to the players inventory. If payment is not None, then
            the player is paying for an item, if payment is None, then the item
            is being collected / picked up. """
        if payment is not None:
            # need to ensure that the user has enough payment.
            # need this wallet >= payment
            if payment > self.wallet:
                return False, "Insufficient funds"

            try:
                # try adding item to inventory
                self.inventory + item

                # if no exception was raised, then the item fits in the inventory
            except InventoryException:
                # if an exception was raise, cannot fit item in inventory.
                return False, "Insufficient space"

            # in this case, there is sufficient funds and sufficient space
            self.wallet -= payment
            self.inventory += item

    def _remove_from_inventory(self, item: Item = None, payment: Wallet = None):
        """ Remove an item to the players inventory. If payment is not None, then
            the player is getting paid for the item, if payment is None, then the
            item is being dropped. """
        pass
