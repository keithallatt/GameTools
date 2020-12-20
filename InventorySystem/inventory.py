from colorama import Fore, Style, init
from ansiwrap import *
import jsonpickle, json
import copy
import pprint

init()


class Item:
    def __init__(self, name: str, **kwargs):
        self.kwargs = kwargs
        self.quantity = kwargs.get("quantity", 1)
        self.color = kwargs.get("color", [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE][hash(name) % 4])
        self.name = name

    def __str__(self):
        str_repr = self.name
        if self.quantity != 1:
            str_repr += " x" + str(self.quantity)
        if self.color is not None:
            str_repr = self.color + str_repr + Style.RESET_ALL
        return str_repr

    def __eq__(self, other):
        return self.name == other.name

    def __mul__(self, other: int):
        return self.copy(quantity=self.quantity * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def copy(self, **kwargs):
        """
        Different from copy.deepcopy / copy.copy. Allows a copy to be made
        while changing certain parameters, keeping all unspecified fields
        """
        return Item(self.name,
                    quantity=kwargs.get("quantity", self.quantity),
                    color=kwargs.get("color", self.color))


class InventoryException(Exception):
    """Basic exception for errors raised by the inventory system"""

    def __init__(self, inventory, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occured with Inventory:\n%s" % inventory.pprint_inv()
            super(InventoryException, self).__init__(msg)
        self.msg = msg
        self.inv = inv


class InventorySystem:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.max_slots = kwargs.get("max_slots", None)
        self.kwargs.update({"max_slots": self.max_slots})

        self._contents = []
        self.kwargs.update({"num_items": len(self._contents)})

        self.stack_limit = kwargs.get("stack_limit", None)
        self.kwargs.update({"stack_limit": self.stack_limit})

        self.remove_on_0 = kwargs.get("remove_on_0", True)
        self.kwargs.update({"remove_on_0": self.remove_on_0})

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
        return pprint.pformat(json.loads(inv.serialize_jsonpickle()))

    def __add__(self, other: Item):
        return copy.deepcopy(self)._add_item(other)

    def __sub__(self, other: Item):
        return copy.deepcopy(self)._remove_item(other)

    def __str__(self):
        self._contents.sort(key=lambda item: item.quantity, reverse=True)
        self._contents.sort(key=lambda item: item.name)

        l_end = "+-" + "-" * max(
            [0] + [ansilen(str(i)) for i in self._contents])
        presentation = "| " + "\n| ".join([str(i) for i in self._contents])
        if presentation == "| ":
            text_ = "Empty Inventory"
            presentation += Fore.MAGENTA + text_ + Style.RESET_ALL
            l_end = "+-" + "-" * len(text_)
        return l_end + "\n" + presentation + "\n" + l_end

    def serialize_jsonpickle(self):
        return jsonpickle.encode(self)


if __name__ == "__main__":
    inv = InventorySystem()
    apple = Item("Apple", color=Fore.RED)
    orange = Item("Orange", color=Fore.YELLOW)

    text = input("> ")
    while text != "quit":
        try:
            words = text.split(" ")
            if len(words) >= 3:
                num = int(words[1])
                item = words[2]
                if words[0] == "give":
                    inv += Item(item, quantity=num)
                elif words[0] == "take":
                    inv -= Item(item, quantity=num)
            print(inv)
        except InventoryException as e:
            print(e.msg)

        text = input("> ")


