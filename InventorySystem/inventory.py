from __future__ import annotations
from ansiwrap import *
import copy
from typing import Union, Dict, Any, List
import warnings
import random
from InventorySystem.currency import Wallet, PriceRegistry
from GameSystem.json_pickler import JSONEncodable


class InventoryException(Exception):
    """ Basic exception for errors raised by the inventory system. """
    def __init__(self, inventory: Union[InventorySystem, Item, None], msg=None):
        """ Basic exception for errors raised by the inventory system. """
        if msg is None:
            msg = "An error occurred with Inventory"
            super(InventoryException, self).__init__(msg)
        self.msg = msg
        self.inv = inventory


class Item(JSONEncodable):
    """ An item used in an inventory system. """
    def __init__(self, name: str, **kwargs):
        """ Create an item with a name, and any one of the following keyword arguments. """
        self.quantity = kwargs.get("quantity", 1)
        kwargs.update({"quantity": self.quantity})

        self.stack_limit = kwargs.get("stack_limit", None)
        kwargs.update({"stack_limit": self.stack_limit})
        self.max_slots = kwargs.get("max_slots", None)
        kwargs.update({"max_slots": self.max_slots})

        self.category = kwargs.get("category", None)
        kwargs.update({"category": self.category})
        self.price = kwargs.get("price", None)
        if type(self.price) == int:
            # if provided a number:
            self.price = Wallet(amount=self.price)
        kwargs.update({"price": self.price})

        self.unit_weight = kwargs.get("unit_weight", None)
        kwargs.update({"unit_weight": self.unit_weight})

        if self.unit_weight is not None and self.unit_weight <= 0:
            raise InventoryException(self, msg="Item with non-positive weight defined.")

        self.name = " ".join([n.capitalize() for n in name.split(" ")])
        self.kwargs = kwargs

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

        return Item(self.name, **kw)

    def add_self_to_registry(self, registry: PriceRegistry):
        """ Add this item to the price registry using the current name and price. """
        registry.add_to_registry(self.name, self.price.unstack())

    def json_encode(self) -> dict:
        """ Encode into JSON. """
        return self.kwargs


class ItemCategory(JSONEncodable):
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


class ItemFilter(JSONEncodable):
    """ Filter for Inventory Systems. Default filter is a blanket block filter. """
    def __init__(self, filter_cats: Dict[Union[ItemCategory, None, Any], bool] = None,
                 accept_all: bool = False):
        """ None key in filter_cats corresponds to default behaviour. """
        self.filter_cats = {
            None: accept_all, Any: accept_all
        }
        if filter_cats is not None:
            self.filter_cats.update(filter_cats)

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

    def __str__(self):
        """ Return the string representation as a set of category names / Any / None
            and the corresponding acceptance or denial of items of that type. """
        return str({str(k): v for k, v in self.filter_cats.items()})

    def json_encode(self) -> dict:
        """  """
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


class InventorySystem(JSONEncodable):
    """ A flexible inventory system. """
    def __init__(self, **kwargs):
        """ Generate an inventory system (inventory page)
            based on the following keyword arguments. """
        self.kwargs = kwargs

        # Maximum number of inventory slots.
        self.max_slots = kwargs.get("max_slots", None)
        if self.max_slots is not None:
            self.max_slots = max(1, self.max_slots)
        self.kwargs.update({"max_slots": self.max_slots})

        # initialized as empty inventory
        self._contents = []
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

    def json_encode(self) -> dict:
        """ Serialize inventory into JSON. Not fully functional for nested custom classes. """
        return self.kwargs

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


class Inventory(JSONEncodable):
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

    def json_encode(self) -> dict:
        return {
            "all_pages_in_str": self.all_pages_in_str,
            "page_display": self.page_display,
            "pages": self.pages,
        }
