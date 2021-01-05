from __future__ import annotations
from ansiwrap import *
import copy
from typing import Union, Dict, Any, List, IO
import warnings
import random
import GameSystem.json_pickler as jp
from collections import OrderedDict
import math
from io import TextIOWrapper
import json


class InventoryException(Exception):
    """ Basic exception for errors raised by the inventory system. """
    def __init__(self, inventory: Union[InventorySystem, Item, None], msg=None):
        """ Basic exception for errors raised by the inventory system. """
        if msg is None:
            msg = "An error occurred with Inventory"
            super(InventoryException, self).__init__(msg)
        self.msg = msg
        self.inv = inventory


class CurrencyException(Exception):
    """ Currency related exception. Allows a more narrow scope for error handling. """
    def __init__(self, cause: Union[Wallet, CurrencySystem] = None, msg: str = None):
        """ Currency related exception. Allows a more narrow scope for error handling. """
        if msg is None:
            msg = "An error occurred with Currency System:\n"
            super(CurrencyException, self).__init__(msg)
        self.msg = msg
        self.cause = cause


class Item(jp.JSONEncodable):
    """ An item used in an inventory system. """
    def __init__(self, name: str, **kwargs):
        """ Create an item with a name, and any one of the following keyword arguments. """
        self.quantity = kwargs.get("quantity", 1)

        self.stack_limit = kwargs.get("stack_limit", None)
        self.max_slots = kwargs.get("max_slots", None)

        self.category = kwargs.get("category", None)
        self.price = kwargs.get("price", None)
        if type(self.price) == int:
            # if provided a number:
            self.price = Wallet(amount=self.price)

        self.unit_weight = kwargs.get("unit_weight", None)

        if self.unit_weight is not None and self.unit_weight <= 0:
            raise InventoryException(self, msg="Item with non-positive weight defined.")

        self.name = " ".join([n.capitalize() for n in name.split(" ")])

        self.kwargs = {}
        self.kwargs.update({"quantity": self.quantity})
        self.kwargs.update({"stack_limit": self.stack_limit})
        self.kwargs.update({"max_slots": self.max_slots})
        self.kwargs.update({"category": self.category})
        self.kwargs.update({"price": self.price})
        self.kwargs.update({"unit_weight": self.unit_weight})
        self.kwargs.update({"name": self.name})

    def __str__(self):
        """ Join all provided fields as space separated list of fields."""
        fields = self.fields()
        fields = list(filter(lambda x: x is not None, fields))
        return " ".join(fields)

    def __eq__(self, other):
        """ Equal items have the same name, may only differ by quantity. """
        if other is None:
            return False

        for kwarg in self.kwargs.keys():
            if kwarg != 'quantity':
                if self.kwargs[kwarg] != other.kwargs[kwarg]:
                    return False

        return self.name == other.name

    def __ne__(self, other):
        """ Must be defined, much like rmul. """
        return not self.__eq__(other)

    def __mul__(self, other: int):
        """ Multiplication by integer multiplies quantity. """
        return self.copy(quantity=self.quantity * other)

    def __rmul__(self, other):
        """ Multiplication between integer and item is commutative. """
        return self.__mul__(other)

    def __add__(self, other: Item):
        """ Add items in different stacks together."""
        if self != other:
            raise InventoryException(self, msg="Item addition on different items")
        return self.copy(quantity=self.quantity + other.quantity)

    def fields(self):
        """ Return a list of fields required to display the item as part of
            an inventory system, including ansi colors around particular fields. """
        return [
            self.name,
            ("~" if self.quantity == 0 else "") +
            ("x" + str(self.quantity) if self.quantity != 1 else ""),
            (str(self.unit_weight) + "g" if self.unit_weight is not None else ""),
            (" ".join(str(self.price).split("\n")) if self.price is not None else "")
        ]

    def copy(self, **kwargs):
        """ Different from copy.deepcopy / copy.copy. Allows a copy to be made
            while changing certain parameters, keeping all unspecified fields. """
        kw = self.kwargs.copy()
        kw.update(kwargs)

        return Item(**kw)

    def add_self_to_registry(self, registry: PriceRegistry):
        """ Add this item to the price registry using the current name and price. """
        registry.add_to_registry(self.name, self.price.unstack())

    def json_encode(self) -> dict:
        """ Encode into JSON. """
        return self.kwargs

    @classmethod
    def json_decode(cls, obj_json: dict):
        """ Decode JSON into an item. """

        name = obj_json['name']
        obj_json.pop('name')

        return Item(name, **obj_json)

    @staticmethod
    def align(item_list):
        """ Items aligned on each field, assuming all items in the list have the
            same kwargs defined. """
        if len(item_list) == 0:
            return []

        # assumes all are formatted the same (fields() should give same length lists)
        item_strings = [[field.strip() + ("  " if ansilen(field) > 0 else "")
                         for field in it.fields()] for it in item_list]

        # get length of each field in list.
        feature_lens = [max([ansilen(item_strings[n][i]) for n in range(len(item_strings))])
                        for i in range(max([len(item_strings[n])
                                            for n in range(len(item_strings))]))]
        # generate padded fields and join together.
        item_strings = ["".join([it_str[i] + " "*(feature_lens[i] - ansilen(it_str[i]))
                        for i in range(len(feature_lens))]) for it_str in item_strings]

        return item_strings


class ItemCategory(jp.JSONEncodable):
    """ Category for items. Each item can belong to multiple categories, but it is
        recommended that only one be used. """
    def __init__(self, name: str, **kwargs):
        """ Define a new category. Can include stack limits or max slot capacities. """
        self.name = name
        self.stack_limit = kwargs.get("stack_limit", None)
        self.max_slots = kwargs.get("max_slots", None)

    def __str__(self):
        """ Return string representation of the category. """
        return self.name + " Category"

    def __eq__(self, other):
        """ Equality of all fields. """
        if other is None:
            return False
        return self.name == other.name

    def __hash__(self):
        """ Return hash of string representation. """
        return hash(str(self))

    def json_encode(self) -> dict:
        """ Return as dictionary to allow JSON encoding. """
        return {
            "name": self.name,
            "stack_limit": self.stack_limit,
            "max_slots": self.max_slots
        }

    @classmethod
    def json_decode(cls, obj_json):
        return ItemCategory(**obj_json)


class ItemFilter(jp.JSONEncodable):
    """ Filter for Inventory Systems. Default filter is a blanket block filter. """
    def __init__(self, filter_cats: Dict[Union[ItemCategory, None, Any], bool] = None,
                 accept_all: bool = False):
        """ None key in filter_cats corresponds to default behaviour. """
        self.filter_cats = {
            None: accept_all, Any: accept_all
        }
        if filter_cats is not None:
            self.filter_cats.update(filter_cats)

    def __str__(self):
        """ Return the string representation as a set of category names / Any / None
            and the corresponding acceptance or denial of items of that type. """
        return str({str(k): v for k, v in self.filter_cats.items()})

    def __eq__(self, other):
        if type(other) == ItemFilter:
            return self.filter_cats == other.filter_cats
        else:
            return False

    def accept(self, item: Item):
        """ Returns whether the described item filter accepts the item based on its category. """
        return self.filter_cats.get(item.category,
                                    self.filter_cats[None if item.category is None else Any])

    def accepts(self, item_category: ItemCategory):
        """ Returns whether the item filter accepts any item of the given category. """
        return self.filter_cats.get(item_category,
                                    self.filter_cats[None if item_category is None else Any])

    def get_categories(self):
        """ Return the set of categories for which this filter will accept. """
        cats = []
        for k, v in self.filter_cats.items():
            if k is not Any:
                if v:
                    cats.append(k)
        return cats

    def get_restricted(self):
        """ Return the set of categories for which this filter will deny. """
        cats = []
        for k, v in self.filter_cats.items():
            if k is not Any:
                if not v:
                    cats.append(k)
        return cats

    def is_generalized(self):
        """ Return whether this filter accepts items with no category (generalized item). """
        return self.filter_cats[None]

    def is_categorized(self):
        """ Return whether this filter will accept any item that is categorized. """
        return self.filter_cats[Any]

    def is_all_encompassing(self):
        """ Return if this filter accepts all items (all-encompassing). """
        return self.filter_cats[None] and self.filter_cats[Any] and \
            False not in list(self.filter_cats.values())

    def json_encode(self) -> dict:
        """ Encode filter into list of accepted categories and rejected categories. """
        hashable = {
            "accepts": [],
            "rejects": []
        }

        for k, v in self.filter_cats.items():
            # k is Any, None or Item Category
            k_repr = k
            if k is Any:
                k_repr = '<Any>'
            elif k is ItemCategory:
                k_repr = k.json_encode()
            if v:
                hashable['accepts'].append(k_repr)
            else:
                hashable['rejects'].append(k_repr)
        return hashable

    @classmethod
    def json_decode(cls, obj_json):
        accepts = obj_json['accepts']
        rejects = obj_json['rejects']

        filter_cats = {}

        for acceptance in accepts:
            if type(acceptance) == str:
                if acceptance == '<Any>':
                    category = Any
                else:
                    raise Exception
            else:
                category = acceptance

            filter_cats.update({category: True})
        for reject in rejects:
            if type(reject) == str:
                if reject == '<Any>':
                    category = Any
                else:
                    raise Exception
            else:
                category = reject

            filter_cats.update({category: False})

        return ItemFilter(filter_cats)

    @classmethod
    def generate_filters(cls, filter_list: List[List[Union[ItemCategory, None]]]):
        """ Generate a list of filters such that for each element of filter_list,
            there is a filter such that that filter accepts all item categories in
            that particular element. Complete the set of filters that accepts all
            items not accepted by any other filter.
            This has the property that every item is accepted by exactly one filter
            in the generated list. """
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


class InventorySystem(jp.JSONEncodable):
    """ A flexible inventory system. """
    def __init__(self, **kwargs):
        """ Generate an inventory system (inventory page)
            based on the following keyword arguments. """
        self.kwargs = {}

        # Maximum number of inventory slots.
        self.max_slots = kwargs.get("max_slots", None)
        if self.max_slots is not None:
            self.max_slots = max(1, self.max_slots)
        self.kwargs.update({"max_slots": self.max_slots})

        # initialized as empty inventory
        self._contents = []
        self.kwargs.update({"_contents": self._contents})
        self.kwargs.update({"num_items": 0})

        # maximum number of items per stack
        self.stack_limit = kwargs.get("stack_limit", None)
        if self.stack_limit is not None:
            self.stack_limit = max(1, self.stack_limit)
        self.kwargs.update({"stack_limit": self.stack_limit})

        # option to remove items from inventory stack list when 0 of item are in stack
        self.remove_on_0 = kwargs.get("remove_on_0", True)
        self.kwargs.update({"remove_on_0": self.remove_on_0})

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

    def __add__(self, other: Union[Item, list[Item]]):
        """ Add a single item or a list of items to the inventory. """
        if type(other) == Item:
            return copy.deepcopy(self)._add_item(other)
        else:
            inv_copy = copy.deepcopy(self)
            for item in other:
                inv_copy._add_item(item)
            return inv_copy

    def __sub__(self, other: Union[Item, list[Item]]):
        """ Remove a single item or a list of items to the inventory. """
        if type(other) == Item:
            return copy.deepcopy(self)._remove_item(other)
        else:
            inv_copy = copy.deepcopy(self)
            for item in other:
                inv_copy._remove_item(item)
            return inv_copy

    def __eq__(self, other):
        if type(other) == InventorySystem:
            eq_kw = True
            for key in self.kwargs.keys():
                if key == "_contents":
                    self.get_contents().sort(key=lambda it: it.name)
                    other.get_contents().sort(key=lambda it: it.name)
                    eq_kw = eq_kw if self.get_contents() == other.get_contents() else False
                else:
                    eq_kw = eq_kw if self.kwargs[key] == other.kwargs.get(key, None) else False

            return eq_kw
        else:
            return False

    def __str__(self):
        """ Display inventory as a list of items with their parameters. """
        self._contents.sort(key=lambda item: item.quantity, reverse=True)
        self._contents.sort(key=lambda item: item.name)
        self._contents.sort(key=lambda item: item.name if item.category is None
                            else item.category.name)

        inv_name = ""
        if self.item_filter is not None:
            # get all categories
            categories = [c.name
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
            presentation += text_

        return "\n".join([l_end,
                          inv_name + " " * (len(l_end) - ansilen(inv_name) - 1) + "|",
                          l_end,
                          "\n".join([p + " " * (len(l_end) - ansilen(p) - 1) + "|"
                                     for p in presentation.split("\n")]), l_end])

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
            # if the system is stack and slot based.
            stack_limit = it.stack_limit
            if stack_limit is None and it.category is not None:
                stack_limit = it.category.stack_limit
            if stack_limit is None:
                stack_limit = self.stack_limit

            if it in self._contents and not new_slot:
                # if the item being added exists in the inventory page but we have
                # not specified to create a new stack (say, because of a stack
                # limit being hit)
                in_lst = self._get_items(self._contents, it)
                to_add = it.quantity
                # while we can add more items to the stacks already in the inventory
                while len(in_lst) > 0 and to_add > 0:
                    next_it, in_lst = in_lst[0], in_lst[1:]
                    can_add = to_add

                    if stack_limit is not None:
                        can_add = min(to_add, stack_limit - next_it.quantity)
                    to_add -= can_add
                    next_it.quantity += can_add

                # if still more items left and all previous stacks are full,
                if to_add > 0:
                    # add new slot
                    self._add_item(it.copy(quantity=to_add), new_slot=True)
            else:
                # either the item doesn't already exist or we are specifically adding a new stack
                # max slot conditions

                # make sure that the number of slots used in the inventory is not at it's maximum
                msc_inv_sys = self.max_slots is None or \
                                              len(self._contents) < self.max_slots
                # make sure the number of slots occupied by items of the same category type
                # is less than the category's max slot limit
                msc_cat = it.category is None or it.category.max_slots is None or \
                    len(list(filter(lambda x: x.category == it.category,
                                    self._contents))) < it.category.max_slots
                # make sure the number of slots occupied by the same item is less than the items
                # max slot limit.
                msc_item = it.max_slots is None or \
                    len(list(filter(lambda x: x.name == it.name, self._contents))) < it.max_slots

                if msc_inv_sys and msc_cat and msc_item:
                    # adding new stacks.
                    to_add = it.quantity

                    if stack_limit is not None and to_add > stack_limit:
                        self._contents.append(it.copy(quantity=stack_limit))
                        self._add_item(it.copy(quantity=to_add - stack_limit))
                    else:
                        self._contents.append(it.copy())
                else:
                    raise InventoryException(self, msg="Item added to full inventory")

        num_items = sum([
            x.quantity for x in self._contents
        ])

        self.kwargs.update({"num_items": num_items})
        self.kwargs.update({"_contents": self._contents})
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
        """ Return all items of kind `val`, full_stacks determining if full stacks are included. """
        return [x for x in lst if x == val and
                (self.stack_limit is None or x.quantity < self.stack_limit
                 or (x.quantity == self.stack_limit and full_stacks))]

    def get_contents(self):
        return self._contents

    def set_stack_limit(self, stack_limit):
        """ Set new stack limit. Throws exception if new stack limit * max slots < current items
            stored in inventory. Increasing stack limit never causes exception. """
        all_contents = self._contents
        self.stack_limit = stack_limit
        self._contents = []
        for item in all_contents:
            self._add_item(item)

    def set_max_slots(self, max_slots):
        """ Set new max number of slots limit. Throws exception if
            new max slots limit * stack limit < current items stored in inventory.
            Increasing max slots limit never causes exception. """
        all_contents = self._contents
        self.max_slots = max_slots
        self._contents = []
        for item in all_contents:
            self._add_item(item)

    def num_slots(self):
        """ Returns number of slots currently used. """
        return len(self._contents)

    def get_slots(self):
        """ Return a copy of the contents. """
        return self._contents[::]

    def json_encode(self) -> dict:
        """ Serialize inventory into JSON. Not fully functional for nested custom classes. """
        return self.kwargs

    @classmethod
    def json_decode(cls, obj_json):
        """ Turn dictionary back into Inventory System. """
        inv_sys = InventorySystem(**obj_json)
        for item in obj_json["_contents"]:
            inv_sys += item
        return inv_sys


class Inventory(jp.JSONEncodable):
    """ Collection of Inventory Systems. """
    def __init__(self, **kwargs):
        """ Create an inventory (collection of inventory pages). """
        self.pages = list(kwargs.get("pages", [
            InventorySystem(item_filter=ItemFilter(accept_all=True))
        ]))
        self.all_pages_in_str = bool(kwargs.get("all_pages_in_str", True))
        self.page_display = int(kwargs.get("page_display", 0))

        # all categories accepted by all pages of the inventory.
        all_cats = sum([
            inv_sys.item_filter.get_categories() for inv_sys in self.pages
        ], start=[])

        all_cats_set = set(all_cats)

        if len(all_cats_set) != len(all_cats):
            # at least 2 pages share a category they accept
            warnings.warn("Multiple pages accept similar items.")

        if len([inv_sys for inv_sys in self.pages if inv_sys.item_filter.is_generalized()]) > 1:
            # at least 2 pages accept generalized items
            warnings.warn("Multiple pages are generalized.")

        if len([inv_sys for inv_sys in self.pages if inv_sys.item_filter.is_categorized()]) > 1:
            # at least 2 pages accept any categorized items
            warnings.warn("Multiple pages are categorized.")

        if len([inv_sys for inv_sys in self.pages
                if inv_sys.item_filter.is_all_encompassing()]) >= 1 and len(self.pages) > 1:
            # all encompassing page exists while other pages exist as well.
            warnings.warn("Multiple pages defined with an all encompassing page.")

        for inv_sys in [inv_sys for inv_sys in self.pages if inv_sys.item_filter.is_categorized()]:
            restrictions = inv_sys.item_filter.get_restricted()
            inner_break = False
            for cat in all_cats_set:
                if cat is not None and cat not in restrictions:
                    # two categories accept the same kinds of items (or partial overlap)
                    warnings.warn(f"Inventory System does not restrict other systems' acceptances.")
                    inner_break = True
                    break
            if inner_break:
                break

        # last check to ensure nothing has gone wrong (blanket warning)
        # this is in place in case the above more specific cases don't catch an issue
        # in this case, debugging the issue is more difficult.
        for category in list(all_cats_set) + [ItemCategory("random:"+str(random.random()))]:
            num_accepting = 0
            for inv_sys in self.pages:
                if inv_sys.item_filter.accepts(category):
                    num_accepting += 1

            if num_accepting > 1:
                warnings.warn(f"Multiple inventory systems accept category {category}.")

    def __str__(self):
        """ Return the string representation of an inventory (can display multiple
            pages or a single page at a time. """
        if not self.all_pages_in_str:
            return str(self.pages[self.page_display]) + "\n " + \
                   str(self.page_display+1) + "/" + str(len(self.pages))

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
        """ Add a single item or list of items to the inventory. """
        inv_copy = copy.deepcopy(self)
        if type(other) == Item:
            # add a single item
            other = [other]
        for it in other:
            it_cat = it.category
            for i in range(len(inv_copy.pages)):
                if inv_copy.pages[i].item_filter.accepts(it_cat):
                    inv_copy.pages[i] += it

                    # TODO: allow multiple pages and proper item addition to different systems.
                    #  - can probably accomplish using additional method in InventorySystem
                    #    and a try/catch which catches InventoryExceptions on +=

                    break
        return inv_copy

    def __sub__(self, other: Union[List[Item], Item]):
        """ Remove items from the inventory. """
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

    def __eq__(self, other):
        if type(other) == Inventory:
            if self.all_pages_in_str != other.all_pages_in_str:
                return False
            if self.all_pages_in_str != other.all_pages_in_str:
                return False
            for page in self.pages:
                if page not in other.pages:
                    return False
            for page in other.pages:
                if page not in self.pages:
                    return False
            return True
        else:
            return False

    def json_encode(self) -> dict:
        return {
            "all_pages_in_str": self.all_pages_in_str,
            "page_display": self.page_display,
            "pages": self.pages,
        }

    @classmethod
    def json_decode(cls, obj_json):
        return Inventory(**obj_json)


class PriceRegistry(jp.JSONEncodable):
    """ Represents a unified list for any shopkeeper npc to use to buy items from the player. """
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
        """ Represent the registry as a list of items and prices. """
        return "\n".join([k + " -> " + str(v) for k, v in self.registry.items()])

    def __eq__(self, other):
        if type(other) == PriceRegistry:
            return self.registry == other.registry
        else:
            return False

    def add_to_registry(self, item_name: str, item_price: int):
        """ Add a new entry to the registry. """
        self.registry.update({item_name: item_price})

    def read_from_registry(self, item_name: str):
        """ Retrieve the entry from the registry. """
        return self.registry.get(item_name, None)

    def json_encode(self) -> dict:
        """ Encode registry as JSON, so return registry of strings and integers. """
        return {"registry": self.registry}

    @classmethod
    def json_decode(cls, obj_json):
        return PriceRegistry(registry=obj_json['registry'])


class Wallet(jp.JSONEncodable):
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

    def __add__(self, other: Wallet):
        """ Returns self + other in terms of currency amounts. """
        return Wallet(curr_sys=self.curr_sys, amount=(self.unstack() + other.unstack()))

    def __sub__(self, other: Wallet):
        """ Returns self - other in terms of currency amounts. """
        return Wallet(curr_sys=self.curr_sys, amount=(self.unstack() - other.unstack()))

    def __gt__(self, other):
        """ Returns self > other in terms of currency amounts. """
        return self.unstack().__gt__(other.unstack())

    def __lt__(self, other):
        """ Returns self < other in terms of currency amounts. """
        return self.unstack().__lt__(other.unstack())

    def __ge__(self, other):
        """ Returns self >= other in terms of currency amounts. """
        return self.unstack().__ge__(other.unstack())

    def __le__(self, other):
        """ Returns self <= other in terms of currency amounts. """
        return self.unstack().__le__(other.unstack())

    def __eq__(self, other):
        """ Returns self == other in terms of currency amounts. """
        if type(other) == Wallet:
            return self.unstack().__eq__(other.unstack())
        else:
            return False

    def __ne__(self, other):
        """ Returns self != other in terms of currency amounts. """
        return self.unstack().__ne__(other.unstack())

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

        # ensure old value and new value are the same.

        if self.unstack() != self.unstack(wallet=new_wallet):
            raise CurrencyException(msg="Auto stack method created differently valued wallet.")

        self.wallet = new_wallet

    def unstack(self, wallet=None):
        """ Return the amount this wallet is worth in it's lowest valued denomination.
            Inverse of auto_stack method. """
        if wallet is None:
            wallet = self.wallet
        lowest_denomination = self.curr_sys.denominations[-1]
        amount = 0
        for denomination in self.curr_sys.denominations:
            amount += self.curr_sys.convert(denomination,
                                            wallet[denomination],
                                            lowest_denomination)

        return amount

    def json_encode(self) -> dict:
        """ Encode wallet as JSON dictionary. """
        return {
            "curr_sys": self.curr_sys.json_encode(),
            "wallet": self.wallet
        }

    @classmethod
    def json_decode(cls, obj_json):

        curr_sys = CurrencySystem.json_decode(obj_json['curr_sys'])
        wallet = obj_json['wallet']

        ret_val = Wallet(curr_sys=curr_sys)

        for k, v in wallet.items():
            ret_val.add_currency(k, v)

        return ret_val


class CurrencySystem(jp.JSONEncodable):
    """ Represents a Currency system, like Gold, Silver and Copper pieces,
        where 1 gold = 7 silver, 1 silver = 13 copper etc. """
    def __init__(self, relative_denominations: OrderedDict[str, int] = None):
        """
        For all denominations other than the highest valued denomination (first entry),
        the value associated with that key is the amount of that denomination that is
        equivalent in worth the next most valued denomination.
        I.e. 1 * key(denomination[i]) is equivalent to
             value(denomination[i+1]) * key(denomination[i+1]).
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

    def __eq__(self, other):
        if type(other) == CurrencySystem:
            return self.relative_denominations == other.relative_denominations
        else:
            return False

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

    def json_encode(self) -> dict:
        """ Encode currency system as JSON serializable dictionary. """
        return {
            "relative_denominations": dict(
                {
                    t[0]:
                        {
                            "rel_val": t[1],
                            "index": i
                        }
                    for t, i in zip(self.relative_denominations.items(),
                                    range(len(self.denominations)))
                }
            )
        }

    @classmethod
    def json_decode(cls, obj_json):
        """ Decode JSON serializable dictionary into currency system.  """
        od = OrderedDict()

        rel_den_dct = obj_json['relative_denominations']

        denominations = [
            (k, v['rel_val'], v['index']) for k, v in rel_den_dct.items()
        ]

        denominations.sort(key=lambda x: x[2])

        for denomination in denominations:
            od.update({denomination[0]: denomination[1]})

        return CurrencySystem(relative_denominations=od)
