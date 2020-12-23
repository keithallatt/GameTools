# GameTools

This repository is designed to be a framework for text based game development, 
incorporating inventory systems, conversation systems (with NPCs) and the like.


## InventorySystem

```
Inventory(max_slots: int, 
          stack_limit: int, 
          remove_on_0: bool, 
          remove_ansi: bool,
          weight_based: bool,
          weight_limit: int)
```

All options in the inventory system are accessible solely through keyword
arguments. If nothing is specified, there is no maximum for any stack, nor
the amount of stacks. Therefore any item can be added to the inventory, and
any number (within the maximum limit of integers). Both values must be positive,
and so if a non-positive value is entered, the inventory defaults to 1.

The `remove_on_0` option by default is set to true. If `remove_on_0` is set to
false, then when all items are removed, the item still appears in the 
inventory and shows as `ItemName x0`. This option is useful for inventories
with a set number of slots where items are fed in such that each slot is filled,
allowing only certain items to appear. 

The `remove_ansi` option by default is set to false. If `remove_ansi` is set to
true, then all string representations of the inventory have ANSI escape codes 
removed.

The `weight_based` option by default is set to false. if `weight_based` is set
to true, then adding and storing items is dependent on unit weight of each item
and ignores any options set by `stack_limit` or `max_slots`. If the weight 
limit (`weight_limit`), and the unit weight of every item is integral (an 
integer), then the inventory system approximates a slot based inventory system 
where each item can take up a different number of slots.

### Example Inventories

<h4><u>'Minecraft' style</u></h4>

In Minecraft, there are 36 slots, in which each can (usually) contain 64 items.

Therefore, to specify a Minecraft style inventory, we'd write:

```
inv = Inventory(max_slots=36, stack_limit=64)  
```

<h4><u>'Rule of 99' style</u></h4>

In a 'Rule of 99' style inventory, any number of items can be stored, but only
99 of any given type (99, 50, 100, any fixed number really). 

Therefore, to specify a 'Rule of 99' style inventory, we'd write:

```
inv = Inventory(stack_limit=99)
```

<h4><u>'Set in Stone' style</u></h4>

In a 'Set in Stone' style inventory, all item slots belong to one specific item.
This could be health potions, or ammunition for an FPS game, or maybe a wallet
of some kind. In this sense, there is no way to empty a slot, it still takes 
up a slot even when you have 0 of the item, or if there is only ever one item.

Therefore, to specify a 'Set in Stone' style inventory, with `n` slots, we'd
write:

```
inv = Inventory(max_slots=n, remove_on_0=False)
```

<h4><u>'Weight based' style</u></h4>

Like in Fallout 3, or Oblivion, this inventory style takes into account the 
weight of each item, where each item can have any positive real-valued weight.

The inventory can continue to accept new items until adding a new item would
cause the total weight of the inventory's capacity to exceed the weight limit.

Therefore, to specify a 'weight based' inventory with weight limit `L`, 
we'd write:

```
inv = Inventory(weight_based=True, weight_limit=L)
```

<h4><u>'Slot based' style</u></h4>

In a 'Slot basedd' style inventory, all items take up a specific number of slots.
For example an item could take up 1, 2, 3, or any other number of slots.
In Subnautica, an element of the inventory system came down to the dimension of
the item model, such as a 2 by 2 slot coverage v.s. a 2 by 3, or even 3 by 3.
In this style, that restriction is not there, since in this system, position is
irrelevant.

This system is a specific kind of weight-based system, and therefore is defined
the same way, the only difference being all weights must be integers. 


