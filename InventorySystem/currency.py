from __future__ import annotations
from collections import OrderedDict
from typing import Union, IO
import math
from io import TextIOWrapper
import os
import json
import warnings


class CurrencyException(Exception):
    """ Currency related exception. Allows a more narrow scope for error handling. """
    def __init__(self, cause: Union[Wallet, CurrencySystem] = None, msg: str = None):
        if msg is None:
            msg = "An error occurred with Currency System:\n"
            super(CurrencyException, self).__init__(msg)
        self.msg = msg
        self.cause = cause


class PriceRegistry:
    """ Represents a unified list for any shopkeeper npc to use to buy items from the player """
    def __init__(self, registry: dict[str, int] = None,
                 read_file: Union[TextIOWrapper, Union[IO, IO[bytes]]] = None,
                 read_file_path: str = None):  # file path to open itself
        """ Create a price registry from file. """
        # read_file -> direct file / text io object to read from
        if read_file is None and read_file_path is not None:
            try:
                read_file = open(read_file_path, 'r')
            except FileNotFoundError:
                read_file = None

        if read_file is not None and read_file_path is None:
            read_file_path = read_file.name

        self.read_file = read_file
        self.read_file_path = read_file_path

        self.registry = registry
        if registry is None:
            self.registry = {}

        if read_file is not None:
            try:
                self.registry = json.loads(read_file.read())
            except json.decoder.JSONDecodeError:
                warnings.warn(f"Registry file {read_file_path} corrupted.")
                self.registry = {}
            finally:
                read_file.close()

    def __str__(self):
        """ Represent the registry as a list of items and prices """
        return "\n".join([k + " -> " + str(v) for k, v in self.registry.items()])

    def add_to_registry(self, item_name: str, item_price: int):
        """ Add a new entry to the registry """
        self.registry.update({item_name: item_price})

    def save_to_file(self):
        """ Save the registry to file """
        with open(self.read_file_path, 'w') as file:
            file.write(json.dumps(self.registry, indent=4, sort_keys=True))
            file.close()

    def read_from_registry(self, item_name: str):
        """ Retrieve the entry from the registry """
        return self.registry.get(item_name, None)


class Wallet:
    """ Represents a wallet that can store amounts of a
        denomination defined by a CurrencySystem. """
    def __init__(self, curr_sys: CurrencySystem = None, amount: int = 0):
        """ Create a wallet with a given currency system and initial amount stored. """
        if amount < 0:
            raise CurrencyException(msg="Cannot have indebted wallet.")
        if curr_sys is None:
            curr_sys = CurrencySystem()
        self.wallet = {denomination: 0 for denomination in curr_sys.denominations}
        lowest_denomination = curr_sys.denominations[-1]
        self.wallet[lowest_denomination] = amount
        self.curr_sys = curr_sys
        self.auto_stack()

    def __str__(self):
        """ Return as block, where each line represents a certain denomination and the amount
            the wallet contains of that denomination. """
        max_len = max([len(denomination) for denomination in self.curr_sys.denominations],
                      default=0)
        return "\n".join(
            [
                denomination + ": " + " " * (max_len - len(denomination)) +
                str(self.wallet[denomination]) for denomination in self.curr_sys.denominations
            ]
        )

    def add_currency(self, denomination, amount, auto_stack=True):
        """ Adds amount of denomination to wallet, returns True on successful addition,
            False on unsuccessful addition. """
        try:
            self.wallet[denomination] += amount
            if auto_stack:
                self.auto_stack()
            return True
        except KeyError:
            return False

    def auto_stack(self):
        """ Stack currency from highest value to lowest value. Inverse of unstack method. """
        lowest_denomination = self.curr_sys.denominations[-1]
        total_amount = self.unstack()

        new_wallet = OrderedDict({
            denomination: 0 for denomination in self.curr_sys.denominations
        })

        current_value = 0
        for denomination in self.curr_sys.denominations:
            amount = self.curr_sys.convert(lowest_denomination,
                                           total_amount - current_value,
                                           denomination,
                                           whole_number=True)
            current_value += self.curr_sys.convert(denomination,
                                                   amount,
                                                   lowest_denomination)
            new_wallet[denomination] = amount

        self.wallet = new_wallet

    def unstack(self):
        """ Return the amount this wallet is worth in it's lowest valued denomination.
            Inverse of auto_stack method."""
        lowest_denomination = self.curr_sys.denominations[-1]
        amount = 0
        for denomination in self.curr_sys.denominations:
            amount += self.curr_sys.convert(denomination,
                                            self.wallet[denomination],
                                            lowest_denomination)

        return amount

    def __add__(self, other: Wallet):
        return Wallet(curr_sys=self.curr_sys, amount=(self.unstack() + other.unstack()))

    def __sub__(self, other: Wallet):
        return Wallet(curr_sys=self.curr_sys, amount=(self.unstack() - other.unstack()))

    def __gt__(self, other):
        return self.unstack().__gt__(other.unstack())

    def __lt__(self, other):
        return self.unstack().__lt__(other.unstack())

    def __ge__(self, other):
        return self.unstack().__ge__(other.unstack())

    def __le__(self, other):
        return self.unstack().__le__(other.unstack())

    def __eq__(self, other):
        return self.unstack().__eq__(other.unstack())

    def __ne__(self, other):
        return self.unstack().__ne__(other.unstack())


class CurrencySystem:
    """ Represents a Currency system, like Gold, Silver and Copper pieces,
        where 1 gold = 7 silver, 1 silver = 13 copper etc. """
    def __init__(self, relative_denominations: OrderedDict[str, int] = None):
        """
        For all denominations other than the highest valued denomination (first entry),
        the value associated with that key is the amount of that denomination that is
        equivalent in worth the next most valued denomination.
        I.e. 1 * key(denomination[i])
             is equivalent to
             value(denomination[i+1]) * key(denomination[i+1])
        """
        if relative_denominations is None:
            self.denominations = ["Gold"]
            self.relative_denominations = {"Gold": 1}
        else:
            self.denominations = list(relative_denominations.keys())
            self.relative_denominations = relative_denominations

        if len(self.relative_denominations) == 0:
            raise CurrencyException(msg="Cannot have empty currency system",
                                    cause=self)
        if self.relative_denominations[list(self.relative_denominations.keys())[0]] != 1:
            raise CurrencyException(msg="Cannot have most valued denomination worth != 1",
                                    cause=self)

    def convert(self, denomination1: str, amount: int, denomination2: str, whole_number=False):
        """ Convert the amount of denomination1 into the relative amount of denomination 2.
            If whole_number is true, then round the value down to the largest integer less
            than the true amount. """
        # if the denominations are the same, then don't make a conversion
        if denomination1 == denomination2:
            return amount

        ind1 = list(self.relative_denominations.keys()).index(denomination1)
        ind2 = list(self.relative_denominations.keys()).index(denomination2)

        # if denomination1 is a more valuable denomination
        while ind1 < ind2:
            ind1 += 1
            amount *= self.relative_denominations[self.denominations[ind1]]

        # if denomination2 is a more valuable denomination
        while ind1 > ind2:
            amount /= self.relative_denominations[self.denominations[ind1]]
            ind1 -= 1

        # round if necessary
        if whole_number:
            return math.floor(amount)

        return amount


if __name__ == "__main__":
    mock_project = "MockProject"
    mock_dir = os.sep.join(os.getcwd().split(os.sep)[:-1]) + os.sep + mock_project + os.sep
    mock_registry = mock_dir + "Registry.json"

    pr = PriceRegistry(read_file_path=mock_registry)
    print(pr)

    pr.save_to_file()
