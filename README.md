```                                                                              
      █████                                █████████                 █          
     █ ░░░░█                                ░░░█░░░░░                █░         
    █ ░     █                                  █░                    █░         
    █░       ░  ████   █ ███  ███    ████      █░     ████    ████   █░  ████   
    █░         █ ░░░█  ██ ░░██ ░░█  █ ░░░█     █░    █ ░░░█  █ ░░░█  █░ █ ░░░█  
    █░   ████   ░   █░ █░░  █░░  █░ █░   █░    █░    █░   █░ █░   █░ █░ █░    ░ 
    █░    ░░█░   ████░ █░   █░   █░ ██████░    █░    █░   █░ █░   █░ █░  ██     
    █░      █░  █ ░░█░ █░   █░   █░ █░░░░░░    █░    █░   █░ █░   █░ █░   ░██   
    █░      █░ █ ░  █░ █░   █░   █░ █░         █░    █░   █░ █░   █░ █░     ░█  
     █     █ ░ █░  ██░ █░   █░   █░ █░   █     █░    █░   █░ █░   █░ █░ █    █░ 
      █████ ░   ███ █░ █░   █░   █░  ████ ░    █░     ████ ░  ████ ░ █░  ████ ░ 
       ░░░░░     ░░░ ░  ░    ░    ░   ░░░░      ░      ░░░░    ░░░░   ░   ░░░░  
```

This repository is designed to be a framework for text based game development, 
incorporating inventory systems, conversation systems (with NPCs) and the like.

A very useful resource in this project's development has been 
<a href="http://howtomakeanrpg.com">this website</a>.

The aim of the project is to allow a Python developer to easily prototype
games that run in the commandline, allowing the developer to create fully
functional games that can then go on to be modified later to be more 
efficient or fast, or potentially take the system to a graphical game. 

Python is not a great language for game development, but hopefully this tool
can be used to prototype games in Python because of its high level, readable 
code, and its flexibility to be used in a number of ways. 

If you choose to use this library, please read the section on unit tests. There 
is a specific way to format your tests in your module to have the test runner
find and run your test with all the predefined tests. 

<details><summary style="font-size:1.25em;">The Inventory System</summary>

### `inventory.py`


<details> 

### Item

``` python
Item(name: str,
     quantity: int,
     stack_limit: int,
     max_slots: int,
     category: ItemCategory,
     price: Union[int, Wallet],
     unit_weight: int)
```

Each item in game must have a non-empty name. Quantity defaults to 1, and 
all other parameters default to None. If `stack_limit` is defined and is 
greater than 0, then when this item is added to an inventory system, the 
inventory system will prioritize the item's stack limit over any other limit
that is defined. If `max_slots` is defined, then the number of inventory
slots taken up by this particular item cannot exceed that limit. If the 
`category` field is defined, then the item is organized into that particular
category, if not, the item is considered 'Generalized'. The price field is 
used primarily for exchange of items for currency. If no such price is given,
then a price can be looked up from a price registry. For weight based
inventory systems, the `unit_weight` field will define the weight each unit
of the item contributes to the inventory system. 


### ItemCategory

``` python
ItemCategory(name: str,
             stack_limit: int,
             max_slots: int)
```

Each item can belong to at most one category. If an item has no stack limit 
defined, then the `stack_limit` field for the category is used. If the category 
has a `max_slot` limit defined, then the number of inventory slots taken up by 
items of that category cannot exceed that limit.


### ItemFilter

``` python
ItemFilter(filter_cats: Dict[Union[ItemCategory, None, Any], bool])
```

An Item filter will determine which items can and cannot be added to a given 
`InventorySystem` object. The `None` key will determine if the filter accepts
generalized items, and the `Any` key will determine if the filter accepts 
categorized items. For all other keys, the value determines if items of that
particular category are accepted or not.


### InventorySystem

``` python
InventorySystem(max_slots: int, 
                stack_limit: int, 
                remove_on_0: bool, 
                weight_based: bool,
                weight_limit: int)
```


For lack of confusion, it is best to use solely keyword arguments.
If nothing is specified, there is no maximum for any stack, nor
the amount of stacks. Therefore, any item can be added to the inventory, and
any number (within the maximum limit of integers). Both values must be positive,
and so if a non-positive value is entered, the inventory defaults to 1.

The `remove_on_0` option by default is set to true. If `remove_on_0` is set to
false, then when all items are removed, the item still appears in the 
inventory and shows as `ItemName x0`. This option is useful for inventories
with a set number of slots where items are fed in such that each slot is filled,
allowing only certain items to appear. 

The `weight_based` option by default is set to false. if `weight_based` is set
to true, then adding and storing items is dependent on unit weight of each item
and ignores any options set by `stack_limit` or `max_slots`. If the weight 
limit (`weight_limit`), and the unit weight of every item is integral (an 
integer), then the inventory system approximates a slot based inventory system 
where each item can take up a different number of slots.


<details><summary style="font-size:1.25em;">Examples</summary>


<h4><u>'Minecraft' style</u></h4>

In Minecraft, there are 36 slots, in which each can (usually) contain 64 items.

Therefore, to specify a Minecraft style inventory, we'd write:

``` python
minecraft_inv = InventorySystem(max_slots=36, stack_limit=64)  
```

<h4><u>'Rule of 99' style</u></h4>

In a 'Rule of 99' style inventory, any number of items can be stored, but only
99 of any given type (99, 50, 100, any fixed number really). 

Therefore, to specify a 'Rule of 99' style inventory, we'd write:

``` python
rule_of_99_inv = InventorySystem(stack_limit=99)
```

<h4><u>'Set in Stone' style</u></h4>

In a 'Set in Stone' style inventory, all item slots belong to one specific item.
This could be health potions, or ammunition for an FPS game, or maybe a wallet
of some kind. In this sense, there is no way to empty a slot, it still takes 
up a slot even when you have 0 of the item, or if there is only ever one item.

Therefore, to specify a 'Set in Stone' style inventory, with `n` slots, we'd
write:

``` python
set_in_stone_inv = InventorySystem(max_slots=n, remove_on_0=False)
```

<h4><u>'Weight based' style</u></h4>

Like in Fallout 3, or Oblivion, this inventory style takes into account the 
weight of each item, where each item can have any positive real-valued weight.

The inventory can continue to accept new items until adding a new item would
cause the total weight of the inventory's capacity to exceed the weight limit.

Therefore, to specify a 'weight based' inventory with weight limit `L`, 
we'd write:

``` python
weight_based_inv = InventorySystem(weight_based=True, weight_limit=L)
```

<h4><u>'Slot based' style</u></h4>

In a 'Slot based' style inventory, all items take up a specific number of slots.
For example an item could take up 1, 2, 3, or any other number of slots.
In Subnautica, an element of the inventory system came down to the dimension of
the item model, such as a 2 by 2 slot coverage v.s. a 2 by 3, or even 3 by 3.
In this style, that restriction is not there, since in this system, position is
irrelevant.

This system is a specific kind of weight-based system, and therefore is defined
the same way, the only difference being all weights must be integers. 

</details>


### Inventory

``` python
Inventory(pages: list[InventorySystem],
          all_pages_in_str: bool,
          page_display: int)
```

The inventory class groups a list of `InventorySystem` objects together to form 
a comprehensive inventory system. The use of `ItemFilter` objects on each 
inventory system allows automatic sorting and `ItemCategory` tags allow
conditional settings such as stack limit or max slot limits. 

</details><!--- End inventory.py -->


### `currency.py`

<details> 

### CurrencySystem

``` python
CurrencySystem(relative_denominations: OrderedDict[str, int])
```

A currency system keeps track of the different denominations and the relative
value of each denomination. The system is designed to work with denominations
whose values are a whole number multiple of the next most valuable denomination.
The values in `relative_denominations` are said whole number multiple, while
the value associated with the most valuable denomination must always be 1.
The system can be used with non-integral relative denominations, but if the 
Wallet class's `auto_stack` method returns a wallet with a different unstacked 
value, then an exception is raised. If the value of any denomination is valued 
as a non-integral amount of the lowest valued denomination, then the system
may fail to provide an accurate and consistent valuation.

<details><summary style="font-size:1.25em;">Examples</summary>
<h4><u>U.S.D. denominations</u></h4>

To take a few denominations from the United States' denominations, consider
a simplified currency system involving the U.S. single dollar bill, 5 dollar
bill, 20 and 100 dollar bill.

As it takes five single dollar bills to be worth a 5 dollar bill, four 5 dollar 
bills to be worth a 20 dollar bill, and five 20 dollar bills to be worth a 100 
dollar bill, we would define this currency system as follows.

``` python
usd_curr_sys = CurrencySystem(OrderedDict({
    "100 Dollar Bill": 1,
    "20 Dollar Bill": 5,
    "5 Dollar Bill": 4,
    "1 Dollar Bill": 5,
}))
```

<h4><u>Precious metals' denominations</u></h4>
 
In a more fantasy / medieval themed game, perhaps the usage of gold, silver,
and copper pieces may be more appropriate. For instance, let us say that a
gold piece is worth 100 silver pieces, while each silver pieces is worth 50
copper pieces. This in turn meaning each gold piece is work 5,000 copper 
pieces. To define this currency system, we'd define it as follows.

``` python
precious_curr_sys = CurrencySystem(OrderedDict({
    "Gold Pieces": 1,
    "Silver Pieces": 100,
    "Copper Pieces": 50,
}))
```

</details>

### PriceRegistry

``` python
PriceRegistry(registry: dict[str, int],
              read_file: TextIOWrapper,
              read_file_path: str)
```

A price registry is used throughout a game model, its primary function being
to store a list of items, and their corresponding list prices. By taking this
value and multiplying by a constant `0 < d < 1`, we can create the discounted
price that said item can be sold for, therefore preventing items from being
worth more when sold than when bought, preventing buy / sell positive feedback
loops. Either a filepath or the opened file object can be used to read in the
registry. If no file is provided, then an empty registry is created. In the 
event that the registry is saved to file with no read file provided at 
creation nor at time of saving, an exception is raised.

### Wallet

``` python
Wallet(curr_sys: CurrencySystem, 
       amount: int)
```

A wallet object uses the specified currency system to store an amount of
currency. For instance, a player character may have one or many wallets
with different currency systems, to allow for non-transferable currencies. 
Each wallet by default will auto stack when currency is added. 

</details><!--- End currency.py -->


</details><!--- End Inventory System -->

___

<details><summary style="font-size:1.25em;"><del>The Map System</del></summary>
</details>

___

<details><summary style="font-size:1.25em;"><del>The Player System</del></summary>
</details>

___

<details><summary style="font-size:1.25em;"><del>The Game System</del></summary>
</details>

___

<details><summary style="font-size:1.25em;">Unit Test</summary>

To create a unit test in your module, create a file `test_<module name>.py`. 
The criteria for `TestRunner/runner.py` finding and running your test case
is by having the filename start with `test_` and end with the python `.py` file 
extension.

In said test case file, any classes that inherit from `unittest.TestCase` will 
be loaded into the test suite and run. 

As part of the `runner.py` file, all python source files, excluding empty
`__init__.py` files, will have their code reviewed, and have the total lines
of code (with comments and docstrings) as well as the number of source lines
of code (no comments or docstrings) counted and summed to give some statistics
about the project. Namely, the number of files, total and source lines of code,
and the results of the unit tests.

</details><!--- End Unit Test -->


---
