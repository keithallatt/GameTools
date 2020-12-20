# GameTools

This repository is designed to be a framework for text based game development, 
incorporating inventory systems, conversation systems (with NPCs) and the like.


## InventorySystem

```
Inventory(max_slots: int, 
          stack_limit: int, 
          remove_on_0: bool, 
          remove_ansi: bool)
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

### Example Inventories

<h4><u>Minecraft style</u></h4>

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

