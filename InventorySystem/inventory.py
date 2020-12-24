from __future__ import annotations
from colorama import Fore, Back, Style, init
from ansiwrap import *
import jsonpickle
import json
import copy
import pprint
import re
from typing import Union, Dict, Any, List
import warnings
import random

init()


class Item:
    """ An item used in an inventory system """
    def __init__(self, name: str, **kwargs):
        self.kwargs = kwargs
        self.quantity = kwargs.get("quantity", 1)
        self.color = kwargs.get("color", None)
        self.category = kwargs.get("category", None)
        self.price = kwargs.get("price", None)
        self.unit_weight = kwargs.get("unit_weight", None)
        if self.unit_weight is not None and self.unit_weight <= 0:
            raise InventoryException(self, msg="Item with non-positive weight defined.")
        self.name = " ".join([n.capitalize() for n in name.split(" ")])

    def __str__(self):
        fields = self.fields()
        fields = list(filter(lambda x: x is not None, fields))
        return " ".join(fields)

    def __eq__(self, other):
        """ Equal items have the same name, may only differ by quantity """
        if self.color != other.color:
            return False
        if self.category is None and other.category is not None:
            return False
        if self.category is not None and other.category is None:
            return False
        # either both none, or both categories. if both none, then this condition is false anyways
        if self.category != other.category:
            return False
        if self.price != other.price:
            return False
        if self.unit_weight != other.unit_weight:
            return False
        return self.name == other.name

    def __mul__(self, other: int):
        return self.copy(quantity=self.quantity * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other: Item):
        if self.name != other.name:
            raise InventoryException(self, msg="Item addition on different items")

        return self.copy(quantity=self.quantity + other.quantity)

    @staticmethod
    def align(item_list):
        """ Items aligned on each field, assuming all items in the list have the
            same kwargs defined """
        if len(item_list) == 0:
            return []

        # assumes all are formatted the same
        item_strings = [list(filter(lambda x: len(x) > 0, it.fields())) for it in item_list]

        # get length of each field in list.
        feature_lens = [max([ansilen(item_strings[n][i])+1 for n in range(len(item_strings))])
                        for i in range(len(item_strings[0]))]
        # generate padded fields and join together.
        item_strings = [" ".join([it_str[i] + " "*(feature_lens[i] - ansilen(it_str[i]))
                        for i in range(len(feature_lens))]) for it_str in item_strings]

        return item_strings

    def fields(self):
        return [
            (self.color if self.color is not None else self.category.before_str()
             if self.category is not None else "") + self.name + Style.RESET_ALL,
            (Fore.RED if self.quantity == 0 else "") + "x" + str(self.quantity) +
            (Style.RESET_ALL if self.quantity == 0 else ""),
            (str(self.unit_weight) + "g" if self.unit_weight is not None else ""),
            ("$" + str(self.price) if self.price is not None else "")
        ]

    def copy(self, **kwargs):
        """
        Different from copy.deepcopy / copy.copy. Allows a copy to be made
        while changing certain parameters, keeping all unspecified fields
        """
        kw = self.kwargs.copy()
        kw.update(kwargs)

        return Item(self.name, **kw)


class ItemCategory:
    """ Category for items. Each item can belong to multiple categories, but it is
        recommended that only one be used. """
    def __init__(self, name: str, fg: Fore = Fore.RESET, bg: Back = Back.RESET):
        self.name = name
        self.fg = fg
        self.bg = bg

    def before_str(self):
        return self.fg + self.bg

    def __str__(self):
        return self.name + " Category"

    def __eq__(self, other):
        """ Equality of all fields. """
        if other is None:
            return False
        return self.name == other.name and self.fg == other.fg and self.bg == other.bg

    def __hash__(self):
        return hash(str(self.name + self.fg + self.bg))


class ItemFilter:
    def __init__(self, filter_cats: Dict[Union[ItemCategory, None, Any], bool] = None):
        """ None key in filter_cats corresponds to default behaviour. """
        self.filter_cats = {
            None: False, Any: False
        }
        if filter_cats is not None:
            self.filter_cats.update(filter_cats)

    def accept(self, item: Item):
        return self.filter_cats.get(item.category,
                                    self.filter_cats[None if item.category is None else Any])

    def accepts(self, item_category: ItemCategory):
        return self.filter_cats.get(item_category,
                                    self.filter_cats[None if item_category is None else Any])

    def get_categories(self):
        cats = []
        for k, v in self.filter_cats.items():
            if k is not Any:
                if v:
                    cats.append(k)
        return cats

    def get_restricted(self):
        cats = []
        for k, v in self.filter_cats.items():
            if k is not Any:
                if not v:
                    cats.append(k)
        return cats

    def is_generalized(self):
        return self.filter_cats[None]

    def is_categorized(self):
        return self.filter_cats[Any]

    def is_all_encompassing(self):
        return self.filter_cats[None] and self.filter_cats[Any] and \
               False not in list(self.filter_cats.values())

    @classmethod
    def generate_filters(cls, filter_list: List[List[Union[ItemCategory, None]]]):
        all_cats = sum(filter_list, start=[])
        all_cats_set = set(all_cats)
        if len(all_cats) != len(all_cats_set):
            raise InventoryException(None, msg="Cannot generate from non-pairwise disjoint lists")

        last_filter = {Any: True, None: True}

        for filter_cat in filter_list:
            last_filter.update({cat: False for cat in filter_cat})

        defined_filters = [{cat: True for cat in filter_cat} for filter_cat in filter_list]
        defined_filters.append(last_filter)

        return [ItemFilter(f) for f in defined_filters]

    def __str__(self):
        return str({str(k): v for k, v in self.filter_cats.items()})


class InventoryException(Exception):
    """Basic exception for errors raised by the inventory system"""
    def __init__(self, inventory: Union[InventorySystem, Item, None], msg=None):
        if msg is None:
            msg = "An error occurred with Inventory:\n%s" % inventory.pprint_inv()
            super(InventoryException, self).__init__(msg)
        self.msg = msg
        self.inv = inventory


class InventorySystem:
    """ A flexible inventory system """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

        # Maximum number of inventory slots.
        self.max_slots = kwargs.get("max_slots", None)
        if self.max_slots is not None:
            self.max_slots = max(1, self.max_slots)
        self.kwargs.update({"max_slots": self.max_slots})

        # initialized as empty inventory
        self._contents = []
        self.kwargs.update({"num_items": len(self._contents)})

        # maximum number of items per stack
        self.stack_limit = kwargs.get("stack_limit", None)
        if self.stack_limit is not None:
            self.stack_limit = max(1, self.stack_limit)
        self.kwargs.update({"stack_limit": self.stack_limit})

        # option to remove items from inventory stack list when 0 of item are in stack
        self.remove_on_0 = kwargs.get("remove_on_0", True)
        self.kwargs.update({"remove_on_0": self.remove_on_0})

        # remove ANSI escape sequences for terminals that don't support ANSI.
        self.remove_ansi = kwargs.get("remove_ansi", False)
        self.kwargs.update({"remove_ansi": self.remove_ansi})

        # if the system is weight based,
        # stack limit / max slots are ignored
        self.weight_based = kwargs.get("weight_based", False)
        self.kwargs.update({"weight_based": self.weight_based})

        # if the system is weight based, what is the limit.
        self.weight_limit = kwargs.get("weight_limit", 0)
        self.kwargs.update({"weight_limit": self.weight_limit})

        self.item_filter = kwargs.get("item_filter", ItemFilter())
        self.kwargs.update({"item_filter": self.item_filter})

        if self.weight_based and self.weight_limit <= 0:
            warnings.warn("Weight based system with non-positive weight limit")
        elif self.weight_based:
            # in this part, weight limit is ok
            if self.stack_limit is not None:
                warnings.warn("Weight based system with stack limit defined")
            if self.max_slots is not None:
                warnings.warn("Weight based system with maximum slot capacity limit")

    def _add_item(self, it: Item, new_slot=False):
        """ Add an item / a number of items to the inventory.
            Raises an InventoryException if item addition fails. """
        if it is None or it.name.strip() == "":
            return self

        if not self.item_filter.accept(it):
            return self

        if self.weight_based and self.weight_limit > 0:
            # if the system is weight based.
            # stack limit is effectively infinite
            # max slots num is effectively infinite.
            weight_in_inv = sum([x.unit_weight * x.quantity for x in self._contents])
            possible_additional_weight = self.weight_limit - weight_in_inv
            possible_to_add = min(possible_additional_weight // it.unit_weight, it.quantity)

            if possible_to_add != it.quantity:
                raise InventoryException(self, msg="Item added to full inventory")

            if it in self._contents:
                # if stack already exists
                self._contents[self._contents.index(it)] += it
            else:
                # if need new stack
                self._contents.append(it)
        else:
            # if it is slot based / stack based
            if it in self._contents and not new_slot:
                in_lst = self._get_items(self._contents, it)
                to_add = it.quantity
                # while we can add more items to the stacks already in the inventory
                while len(in_lst) > 0 and to_add > 0:
                    next_it, in_lst = in_lst[0], in_lst[1:]
                    can_add = to_add
                    if self.stack_limit is not None:
                        can_add = min(to_add, self.stack_limit - next_it.quantity)
                    to_add -= can_add
                    next_it.quantity += can_add

                # if still more items left and all previous stacks are full,
                if to_add > 0:
                    # add new slot
                    self._add_item(it.copy(quantity=to_add), new_slot=True)
            else:
                if self.max_slots is None or len(self._contents) < self.max_slots:
                    # adding new stacks.
                    to_add = it.quantity
                    if self.stack_limit is not None and to_add > self.stack_limit:
                        self._contents.append(it.copy(quantity=self.stack_limit))
                        self._add_item(it.copy(quantity=to_add - self.stack_limit))
                    else:
                        self._contents.append(it.copy())
                else:
                    raise InventoryException(self, msg="Item added to full inventory")

        self.kwargs.update({"num_items": len(self._contents)})
        return self

    def _remove_item(self, it: Item):
        """ Remove an item / a number of items from the inventory.
            Raises an InventoryException if item removal fails. """
        if it not in self._contents:
            raise InventoryException(self, msg="Cannot remove non-existent item")
        it_lst = self._get_items(self._contents, it, full_stacks=True)
        # sort by quantity low to high, to remove from smallest stacks first
        it_lst.sort(key=lambda x: x.quantity)

        to_remove = it.quantity

        while len(it_lst) > 0 and to_remove > 0:
            next_it, it_lst = it_lst[0], it_lst[1:]
            can_remove = min(next_it.quantity, to_remove)
            next_it.quantity -= can_remove
            to_remove -= can_remove

        # if we could not remove all items
        if to_remove > 0:
            raise InventoryException(self,
                                     msg="Cannot remove more items")

        if self.remove_on_0:
            self._contents = [x for x in self._contents if x.quantity != 0]

        return self

    def _get_items(self, lst, val, full_stacks=False):
        """ Return all items of kind `val`, full_stacks determining if full stacks are included """
        return [x for x in lst if x == val and
                (self.stack_limit is None or x.quantity < self.stack_limit
                 or (x.quantity == self.stack_limit and full_stacks))]

    def pprint_inv(self):
        """ Use pretty print module to print inventory structure """
        return pprint.pformat(json.loads(self.serialize_json_pickle()))

    def serialize_json_pickle(self):
        """ Serialize inventory into json """
        return jsonpickle.encode(self, make_refs=False)

    def set_stack_limit(self, stack_limit):
        """ Set new stack limit. Throws exception if new stack limit * max slots < current items
            stored in inventory. Increasing stack limit never causes exception """
        all_contents = self._contents
        self.stack_limit = stack_limit
        self._contents = []
        for item in all_contents:
            self._add_item(item)

    def set_max_slots(self, max_slots):
        """ Set new max number of slots limit. Throws exception if
            new max slots limit * stack limit < current items stored in inventory.
            Increasing max slots limit never causes exception """
        all_contents = self._contents
        self.max_slots = max_slots
        self._contents = []
        for item in all_contents:
            self._add_item(item)

    def num_slots(self):
        """ Returns number of slots currently used """
        return len(self._contents)

    def get_slots(self):
        """ return a copy of the contents """
        return self._contents[::]

    def __add__(self, other: Union[Item, list[Item]]):
        """ Add a single item or a list of items to the inventory """
        if type(other) == Item:
            return copy.deepcopy(self)._add_item(other)
        else:
            inv_copy = copy.deepcopy(self)
            for item in other:
                inv_copy._add_item(item)
            return inv_copy

    def __sub__(self, other: Union[Item, list[Item]]):
        """ Remove a single item or a list of items to the inventory """
        if type(other) == Item:
            return copy.deepcopy(self)._remove_item(other)
        else:
            inv_copy = copy.deepcopy(self)
            for item in other:
                inv_copy._remove_item(item)
            return inv_copy

    def __str__(self):
        """ Display inventory as a list of items with their parameters. """

        self._contents.sort(key=lambda item: item.quantity, reverse=True)
        self._contents.sort(key=lambda item: item.name)
        self._contents.sort(key=lambda item: item.name if item.category is None
                            else item.category.name)

        inv_name = ""
        if self.item_filter is not None:
            # get all categories
            categories = [c.before_str() + c.name + Style.RESET_ALL
                          for c, v in self.item_filter.filter_cats.items()
                          if v and c is not None and c is not Any]

            if self.item_filter.filter_cats[None]:
                categories += ["General"]
            if self.item_filter.filter_cats[Any]:
                categories = ["Categorized"]
            if self.item_filter.filter_cats[None] and self.item_filter.filter_cats[Any]:
                categories = ["All" if self.item_filter.is_all_encompassing() else "Other"]

            inv_name = "| " + " & ".join(categories)

        item_lst_str = Item.align(self._contents)

        text_ = "Empty Inventory"

        width = max(
            [ansilen(inv_name), (ansilen(text_)+1 if len(self._contents) == 0 else 0)] +
            [ansilen(i) for i in item_lst_str])

        l_end = "+-" + "-" * width + "+"
        presentation = "| " + "\n| ".join(item_lst_str)
        if presentation == "| ":
            presentation += Fore.MAGENTA + text_ + Style.RESET_ALL

        if self.remove_ansi:
            # ANSI code regex
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            presentation = ansi_escape.sub('', presentation)

        return "\n".join([l_end,
                          inv_name + " " * (len(l_end) - ansilen(inv_name) - 1) + "|",
                          l_end,
                          "\n".join([p + " " * (len(l_end) - ansilen(p) - 1) + "|"
                                     for p in presentation.split("\n")]), l_end])


class Inventory:
    """ Collection of Inventory Systems. """
    def __init__(self, **kwargs):
        self.pages = list(kwargs.get("pages", []))
        self.all_pages_in_str = True
        self.page_display = 0

        all_cats = sum([
            inv_sys.item_filter.get_categories() for inv_sys in self.pages
        ], start=[])

        all_cats_set = set(all_cats)

        if len(all_cats_set) != len(all_cats):
            # at least 2 pages share a category they accept
            warnings.warn("Multiple pages accept similar items.")

        if len([inv_sys for inv_sys in self.pages if inv_sys.item_filter.is_generalized()]) > 1:
            warnings.warn("Multiple pages are generalized.")

        if len([inv_sys for inv_sys in self.pages if inv_sys.item_filter.is_categorized()]) > 1:
            warnings.warn("Multiple pages are categorized.")

        if len([inv_sys for inv_sys in self.pages
                if inv_sys.item_filter.is_all_encompassing()]) >= 1 and len(self.pages) > 1:
            warnings.warn("Multiple pages defined with an all encompassing page.")

        for inv_sys in [inv_sys for inv_sys in self.pages if inv_sys.item_filter.is_categorized()]:
            restrictions = inv_sys.item_filter.get_restricted()

            inner_break = False
            for cat in all_cats_set:
                if cat is not None and cat not in restrictions:
                    warnings.warn(f"Inventory System does not restrict other systems' acceptances.")
                    inner_break = True
                    break
            if inner_break:
                break

        # last check to ensure nothing has gone wrong
        for category in list(all_cats_set) + [ItemCategory("random:"+str(random.random()))]:
            num_accepting = 0
            for inv_sys in self.pages:
                if inv_sys.item_filter.accepts(category):
                    num_accepting += 1

            if num_accepting > 1:
                warnings.warn(f"Multiple inventory systems accept category {category}.")

    def __str__(self):
        if not self.all_pages_in_str:
            return str(self.pages[self.page_display])

        max_lines = max([len(str(page).split("\n")) for page in self.pages], default=0)

        widths = [len(str(page).split("\n")[0]) for page in self.pages]

        page_str_s = [
            str(self.pages[i]).split("\n") + [
                " " * widths[i] for _ in range(max_lines - len(str(self.pages[i]).split("\n")))
            ] for i in range(len(self.pages))
        ]

        return "\n".join([
            " ".join([page_str_s[page_num][line] for page_num in range(len(self.pages))])
            for line in range(max_lines)
        ])

    def __add__(self, other: Union[List[Item], Item]):
        inv_copy = copy.deepcopy(self)
        if type(other) == Item:
            # add a single item
            other = [other]
        for it in other:
            it_cat = it.category
            for i in range(len(inv_copy.pages)):
                if inv_copy.pages[i].item_filter.accepts(it_cat):
                    inv_copy.pages[i] += it
                    continue
        return inv_copy

    def __sub__(self, other: Union[List[Item], Item]):
        inv_copy = copy.deepcopy(self)
        if type(other) == Item:
            # remove a single item
            other = [other]
        for it in other:
            it_cat = it.category
            for i in range(len(inv_copy.pages)):
                if inv_copy.pages[i].item_filter.accepts(it_cat):
                    inv_copy.pages[i] -= it
        return inv_copy


FILTER_ACCEPT_ALL = ItemFilter({None: True, Any: True})


if __name__ == "__main__":
    food_cat = ItemCategory("Food", fg=Fore.GREEN)
    materials_cat = ItemCategory("Materials", fg=Fore.LIGHTBLUE_EX)
    key_items_cat = ItemCategory("Key Items", fg=Fore.LIGHTMAGENTA_EX)

    filters = ItemFilter.generate_filters([[food_cat, materials_cat], [key_items_cat]])
    inv_sys_s = [InventorySystem(item_filter=f) for f in filters]

    apple = Item("Apple", category=food_cat)
    orange = Item("Orange", category=food_cat)
    grape = Item("Grape", category=food_cat)
    wood = Item("Wood", category=materials_cat)
    stone = Item("Stone", category=materials_cat)
    marble = Item("Marble", category=materials_cat)
    dirt = Item("Dirt")
    key = Item("Shiny Key", category=key_items_cat)

    item_list_ = [apple, orange, grape, wood, stone, dirt, marble, key]

    inv = Inventory(pages=inv_sys_s)

    inv += item_list_

    print(inv)
