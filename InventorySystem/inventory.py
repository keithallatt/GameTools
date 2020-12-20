from colorama import Fore, Style, init
from ansiwrap import *
init()


class Item:
    def __init__(self, name: str, quantity: int = 1, color: Fore = None):
        self.name = name
        self.quantity = quantity
        self.color = color

    def __str__(self):
        str_repr = self.name
        if self.quantity > 1:
            str_repr += " x" + str(self.quantity)
        if self.color is not None:
            str_repr = self.color + str_repr + Style.RESET_ALL
        return str_repr

    def __eq__(self, other):
        return self.name == other.name

    def __mul__(self, other: int):
        return Item(self.name, self.quantity * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def copy(self):
        return Item(self.name, self.quantity, self.color)


class InventoryException(Exception):
    """Basic exception for errors raised by the inventory system"""

    def __init__(self, inv, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occured with Inventory %s" % inv.shortname()
        super(InventoryException, self).__init__(msg)
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

    def _add_item(self, it: Item, new_slot=False):
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
                self._add_item(Item(it.name, to_add), new_slot=True)
        else:
            if self.max_slots is None or len(self._contents) < self.max_slots:
                to_add = it.quantity
                if self.stack_limit is not None and to_add > self.stack_limit:
                    self._contents.append(Item(it.name, self.stack_limit))
                    self._add_item(Item(it.name, to_add - self.stack_limit))
                else:
                    self._contents.append(it.copy())
            else:
                raise InventoryException(self,
                                         msg="Item added to full inventory")
        self.kwargs.update({"num_items": len(self._contents)})
        return self

    def __add__(self, other: Item):
        return self._add_item(other)

    def __str__(self):
        self._contents.sort(key=lambda item: item.quantity, reverse=True)
        self._contents.sort(key=lambda item: item.name)

        l_end = "+-" + "-" * max([0] + [ansilen(str(i)) for i in self._contents])
        presentation = "| " + "\n| ".join([str(i) for i in self._contents])
        if presentation == "| ":
            text_ = "Empty Inventory"
            presentation += Fore.MAGENTA + text_ + Style.RESET_ALL
            l_end = "+-" + "-" * len(text_)
        return l_end + "\n" + presentation + "\n" + l_end

    def _get_items(self, lst, val):
        return [x for x in lst if x == val and (self.stack_limit is None or
                                                x.quantity < self.stack_limit)]

    def shortname(self):
        shortname = "<InventorySystem: "

        for key, val in self.kwargs.items():
            shortname += "\n\t%s = %s," % (key, str(val))

        return shortname[:-1] + "\n>"


if __name__ == "__main__":
    inv = InventorySystem(stack_limit=5, max_slots=4)
    apple = Item("Apple", 2,  color=Fore.RED)
    orange = Item("Orange", 2, color=Fore.YELLOW)

    inv += apple
    inv += orange

    print(inv.shortname(), inv, sep="\n")
