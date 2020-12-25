from __future__ import annotations
from collections import OrderedDict
import math


class Wallet:
    def __init__(self, curr_sys: CurrencySystem = None, amount: int = 0):
        self.curr_sys = curr_sys
        if curr_sys is None:
            curr_sys = CurrencySystem()
        self.wallet = {denomination: 0 for denomination in curr_sys.denominations}
        lowest_denomination = curr_sys.denominations[-1]
        self.wallet[lowest_denomination] = amount

    def __str__(self):
        max_len = max([len(denomination) for denomination in self.curr_sys.denominations],
                      default=0) + 1
        return "\n".join(
            [
                denomination + ":" + " " * (max_len - len(denomination)) +
                str(self.wallet[denomination]) for denomination in self.curr_sys.denominations
            ]
        )

    def add_currency(self, denomination, amount, auto_stack=False):
        """ Adds amount of denomination to wallet, returns True on successful addition,
            False on unsuccessful addition. """
        try:
            self.wallet[denomination] += amount
            if auto_stack:
                self.wallet = self.curr_sys.auto_stack(self).wallet
            return True
        except KeyError:
            return False


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

    @staticmethod
    def unstack(wallet: Wallet):
        self = wallet.curr_sys
        lowest_denomination = self.denominations[-1]
        amount = 0
        for denomination in self.denominations:
            amount += self.convert((denomination, wallet.wallet[denomination]), lowest_denomination)

        return amount

    @staticmethod
    def auto_stack(wallet: Wallet):
        self = wallet.curr_sys
        lowest_denomination = self.denominations[-1]
        total_amount = CurrencySystem.unstack(wallet)

        new_wallet = Wallet(curr_sys=self)

        for denomination in self.denominations:
            amount = self.convert((lowest_denomination, total_amount -
                                   CurrencySystem.unstack(new_wallet)),
                                  denomination, whole_number=True)
            new_wallet.add_currency(denomination, amount)

        return new_wallet
