from unittest import TestCase

# need InventorySystem.inventory since suite outside inventory system folder
from InventorySystem.inventory import Item, InventorySystem, InventoryException, ItemFilter


class InventoryTest(TestCase):
    """ InventorySystem module test cases """
    def test_item(self):
        """ Test item integer multiplications and item item additions. """
        # test a range of multiplications of items
        for init_q in range(100):
            for multiply_q in range(100):
                foo = Item("foo", quantity=init_q)
                multiply_foo = foo * multiply_q

                self.assertEqual(multiply_foo.quantity, multiply_q * init_q)

        # test a range of addition of items
        for init_q in range(100):
            for add_q in range(100):
                if init_q != 3 or add_q != 3:
                    continue

                foo1 = Item("foo", quantity=init_q)
                foo2 = Item("foo", quantity=add_q)

                foo1 += foo2

                self.assertEqual(foo1.quantity, init_q + add_q)

    def test_inventory_exception(self):
        """ Test whether or not exceptions are raised by illegal operations """
        inv = InventorySystem(stack_limit=3,
                              max_slots=3,
                              item_filter=ItemFilter.FILTER_ACCEPT_ALL)
        foo = Item("foo")

        # test removing non existent item
        with self.assertRaises(InventoryException) as context:
            inv -= foo

        self.assertTrue('Cannot remove non-existent item' in
                        context.exception.msg)

        # test adding too many items
        with self.assertRaises(InventoryException) as context:
            inv += 10*foo

        self.assertTrue('Item added to full inventory' in
                        context.exception.msg)

    def test_inventory_system(self):
        """ Test inventory system for its ability to add multiple items to itself """
        # test adding different items, making sure all are added
        for foo_q in range(100):
            for bar_q in range(100):

                inv = InventorySystem(stack_limit=99,
                                      item_filter=ItemFilter.FILTER_ACCEPT_ALL)
                foo = Item("foo")
                bar = Item("bar")

                inv += foo_q * foo
                inv += bar_q * bar

                total_items = sum([x.quantity for x in inv._contents])
                self.assertEqual(total_items, foo_q + bar_q)
