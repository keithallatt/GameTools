from __future__ import annotations
from colorama import Fore, Style, init
from ansiwrap import *
import jsonpickle, json
import copy
import pprint
import re

init()


class Item:
    """ An item used in an inventory system """
    def __init__(self, name: str, **kwargs):
        self.kwargs = kwargs
        self.quantity = kwargs.get("quantity", 1)
        self.color = kwargs.get("color", None)
        self.price = kwargs.get("price", None)
        self.name = name

    def __str__(self):
        str_repr = self.name + " x" + str(self.quantity)
        if self.color is not None:
            str_repr = self.color + str_repr + Style.RESET_ALL
        if self.price is not None:
            str_repr += " $" + str(self.price)
        return str_repr

    def __eq__(self, other):
        return self.name == other.name

    def __mul__(self, other: int):
        return self.copy(quantity=self.quantity * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other: Item):
        if self.name != other.name:
            raise InventoryException("Item addition on different items")

        return self.copy(quantity=self.quantity + other.quantity)

    def align(self, item_list):
        max_name_length = max([0]+[len(x.name) for x in item_list])
        max_quantity_length = max([0]+[len(str(x.quantity)) for x in item_list])
        max_price_length = max([0]+[len(str(x.price)) for x in item_list
                                    if x.price is not None])

        name = self.name.ljust(max_name_length)
        quantity = str(self.quantity).ljust(max_quantity_length)
        price = str(self.price).ljust(max_price_length)

        return name + "   x" + quantity + ("   $" + price if self.price is not None else "")

    def copy(self, **kwargs):
        """
        Different from copy.deepcopy / copy.copy. Allows a copy to be made
        while changing certain parameters, keeping all unspecified fields
        """
        return Item(self.name,
                    quantity=kwargs.get("quantity", self.quantity),
                    color=kwargs.get("color", self.color),
                    price=kwargs.get("price", self.price))


class InventoryException(Exception):
    """Basic exception for errors raised by the inventory system"""

    def __init__(self, inventory, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occured with Inventory:\n%s" % inventory.pprint_inv()
            super(InventoryException, self).__init__(msg)
        self.msg = msg
        self.inv = inventory


class InventorySystem:
    """ A flexible inventory system """
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.max_slots = kwargs.get("max_slots", None)
        if self.max_slots is not None:
            self.max_slots = max(1, self.max_slots)
        self.kwargs.update({"max_slots": self.max_slots})

        self._contents = []
        self.kwargs.update({"num_items": len(self._contents)})

        self.stack_limit = kwargs.get("stack_limit", None)
        if self.stack_limit is not None:
            self.stack_limit = max(1, self.stack_limit)
        self.kwargs.update({"stack_limit": self.stack_limit})

        self.remove_on_0 = kwargs.get("remove_on_0", True)
        self.kwargs.update({"remove_on_0": self.remove_on_0})

        self.remove_ansi = kwargs.get("remove_ansi", True)
        self.kwargs.update({"remove_ansi": self.remove_ansi})

    def _add_item(self, it: Item, new_slot=False):
        if it is None or it.name.strip() == "":
            return self

        if it in self._contents and not new_slot:
            in_lst = self._get_items(self._contents, it)
            to_add = it.quantity
            while len(in_lst) > 0 and to_add > 0:
                next_it, in_lst = in_lst[0], in_lst[1:]
                can_add = to_add
                if self.stack_limit is not None:
                    can_add = min(to_add, self.stack_limit - next_it.quantity)
                to_add -= can_add
                next_it.quantity += can_add

            if to_add > 0:
                # add new slot
                self._add_item(it.copy(quantity=to_add), new_slot=True)
        else:
            if self.max_slots is None or len(self._contents) < self.max_slots:
                to_add = it.quantity
                color = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE][
                    hash(it.name.strip()) % 4]
                if self.stack_limit is not None and to_add > self.stack_limit:
                    self._contents.append(it.copy(quantity=self.stack_limit))

                    self._add_item(it.copy(quantity=to_add - self.stack_limit))
                else:
                    self._contents.append(it.copy())
            else:
                raise InventoryException(self,
                                         msg="Item added to full inventory")
        self.kwargs.update({"num_items": len(self._contents)})
        return self

    def _remove_item(self, it: Item):
        if it not in self._contents:
            raise InventoryException(self,
                                     msg="Cannot remove non-existent item")
        it_lst = self._get_items(self._contents, it, all_opts=True)
        it_lst.sort(key=lambda it: it.quantity)

        to_remove = it.quantity

        while len(it_lst) > 0 and to_remove > 0:
            next_it, it_lst = it_lst[0], it_lst[1:]
            can_remove = min(next_it.quantity, to_remove)
            next_it.quantity -= can_remove
            to_remove -= can_remove

        if to_remove > 0:
            raise InventoryException(self,
                                     msg="Cannot remove more items")

        if self.remove_on_0:
            self._contents = [x for x in self._contents if x.quantity != 0]

        return self

    def _get_items(self, lst, val, all_opts=False):
        return [x for x in lst if x == val and
                (self.stack_limit is None or x.quantity < self.stack_limit
                 or (x.quantity == self.stack_limit and all_opts))]

    def pprint_inv(self):
        return pprint.pformat(json.loads(inv.serialize_json_pickle()))

    def serialize_json_pickle(self):
        return jsonpickle.encode(self)

    def set_stack_limit(self, stack_limit):
        all_contents = self._contents
        self.stack_limit = stack_limit
        self._contents = []
        for item in all_contents:
            self._add_item(item)

    def set_max_slots(self, max_slots):
        all_contents = self._contents
        self.max_slots = max_slots
        self._contents = []
        for item in all_contents:
            self._add_item(item)

    def num_slots(self):
        return len(self._contents)

    def get_slots(self):
        """ return a copy of the contents """
        return self._contents[::]

    def __add__(self, other: Item):
        return copy.deepcopy(self)._add_item(other)

    def __sub__(self, other: Item):
        return copy.deepcopy(self)._remove_item(other)

    def __str__(self):
        self._contents.sort(key=lambda item: item.quantity, reverse=True)
        self._contents.sort(key=lambda item: item.name)

        item_lst_str = [
            i.align(self._contents)
            for i in self._contents
        ]
        l_end = "+-" + "-" * max(
            [0] + [ansilen(i) for i in item_lst_str])
        presentation = "| " + "\n| ".join(item_lst_str)
        if presentation == "| ":
            text_ = "Empty Inventory"
            presentation += Fore.MAGENTA + text_ + Style.RESET_ALL
            l_end = "+-" + "-" * len(text_)

        if self.remove_ansi:
            # ANSI code regex
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            presentation = ansi_escape.sub('', presentation)


        return l_end + "\n" + presentation + "\n" + l_end


if __name__ == "__main__":
    inv = InventorySystem(stack_limit=5)


