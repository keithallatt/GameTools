from __future__ import annotations
from collections import OrderedDict
from typing import Union
import math


class CurrencyException(Exception):
    def __init__(self, cause: Union[Wallet, CurrencySystem] = None, msg: str = None):
        if msg is None:
            msg = "An error occurred with Currency System:\n"
            super(CurrencyException, self).__init__(msg)
        self.msg = msg
        self.cause = cause


class Wallet:
    def __init__(self, curr_sys: CurrencySystem = None, amount: int = 0):
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
        max_len = max([len(denomination) for denomination in self.curr_sys.denominations],
                      default=0) + 1
        return "\n".join(
            [
                denomination + ":" + " " * (max_len - len(denomination)) +
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
        lowest_denomination = self.curr_sys.denominations[-1]
        total_amount = self.unstack()

        new_wallet = OrderedDict({
            denomination: 0 for denomination in self.curr_sys.denominations
        })
        current_value = 0
        for denomination in self.curr_sys.denominations:
            amount = self.curr_sys.convert((lowest_denomination, total_amount - current_value),
                                           denomination, whole_number=True)
            current_value += self.curr_sys.convert((denomination, amount), lowest_denomination)
            new_wallet[denomination] = amount

        self.wallet = new_wallet

    def unstack(self):
        lowest_denomination = self.curr_sys.denominations[-1]
        amount = 0
        for denomination in self.curr_sys.denominations:
            amount += self.curr_sys.convert((denomination, self.wallet[denomination]),
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


class CurrencySystem:
    """ Represents a Currency system, like Gold, Silver and Copper pieces,
        where 1 gold = 7 silver, 1 silver = 13 copper etc. """
    def __init__(self, relative_denominations: OrderedDict[str, int] = None):
        # requires that relative_denominations is of the form
        # {
        #   name1: 1,
        #   name2: int(convert from name1 to name2)
        #   name3: int(convert from name2 to name3)
        # }

        # therefore for the example above, we have
        # {
        #   "Gold": 1,
        #   "Silver": 7,
        #   "Copper": 13
        # }

        if relative_denominations is None:
            self.denominations = ["Gold"]
            self.relative_denominations = {"Gold": 1}
        else:
            self.denominations = list(relative_denominations.keys())
            self.relative_denominations = relative_denominations

    def convert(self, currency1: tuple[str, int], denomination2: str, whole_number=False):
        denomination1, amount = currency1
        ind1 = list(self.relative_denominations.keys()).index(denomination1)
        ind2 = list(self.relative_denominations.keys()).index(denomination2)

        if ind1 == ind2:
            return amount

        while ind1 < ind2:
            ind1 += 1
            amount *= self.relative_denominations[self.denominations[ind1]]

        while ind1 > ind2:
            amount /= self.relative_denominations[self.denominations[ind1]]
            ind1 -= 1

        if whole_number:
            return math.floor(amount)
        return amount


if __name__ == "__main__":
    gold_silver = CurrencySystem(relative_denominations=OrderedDict({
        "Gold": 1,
        "Silver": 10
    }))

    w1 = Wallet(curr_sys=gold_silver, amount=101)
    w2 = Wallet(curr_sys=gold_silver, amount=100)

    print(w1)
    print()
    print(w2)
    print()
    print(w1 - w2)
