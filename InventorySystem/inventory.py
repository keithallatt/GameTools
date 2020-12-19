from colorama import Fore, Back, Style

class Item:
    def __init__(self, name: str, quantity: int = 1):
        self.name = name
        self.quantity = quantity

    def __str__(self):
        return self.name + " x"+str(self.quantity)

    def __eq__(self, other):
        return self.name == other.name

    def copy(self):
        return Item(self.name, self.quantity)


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

    def _add_item(self, it: Item):
        if it in self._contents:
            in_lst = self._get_items(self._contents, it)
            while len(in_lst > 0) and in_lst
            in_lst.quantity += it.quantity
        else:
            if self.max_slots is None or len(self._contents) < self.max_slots:
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

        l_end = "+-" + "-" * max([0]+[len(str(i)) for i in self._contents])
        presentation = "| "+"\n| ".join([str(i) for i in self._contents])
        if presentation == "| ":
            text_ = "Empty Inventory"
            presentation += Fore.MAGENTA + text_ + Style.RESET_ALL
            l_end = "+-" + "-" * len(text_)
        return l_end + "\n" + presentation + "\n" + l_end

    @staticmethod
    def _get_items(lst, val):
        return [x for x in lst if x == val]

    def shortname(self):
        shortname = "<InventorySystem: "

        for key, val in self.kwargs.items():
            shortname += "\n\t%s = %s," % (key, str(val))

        return shortname[:-1]+"\n>"


if __name__ == "__main__":
    inv = InventorySystem()
    apple = Item("Apple")
    orange = Item("Orange")

    print(inv)
    inv += orange
    inv += apple
    inv += apple
    inv += orange
    inv += orange
    print(inv)



