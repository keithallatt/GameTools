from unittest import TestCase
# need InventorySystem.inventory since suite outside inventory system folder
from InventorySystem.inventory import Item, InventorySystem, InventoryException, FILTER_ACCEPT_ALL
from colorama import Fore


class InventoryTest(TestCase):
    def test_item(self):
        # test a range of multiplications of items
        for init_q in range(10):
            for mult_q in range(10):
                foo = Item("foo", quantity=init_q, color=Fore.BLUE)
                mult_foo = foo * mult_q

                self.assertEqual(mult_foo.quantity, mult_q*init_q)

        # test a range of addition of items
        for init_q in range(10):
            for add_q in range(10):
                foo1 = Item("foo", quantity=init_q)
                foo2 = Item("foo", quantity=add_q)

                foo1 += foo2

                self.assertEqual(foo1.quantity, init_q + add_q)


    def test_inventory_exception(self):
        inv = InventorySystem(stack_limit=3, max_slots=3, item_filter=FILTER_ACCEPT_ALL)
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
        # test adding different items, making sure all are added
        for foo_q in range(5):
            for bar_q in range(3):

                inv = InventorySystem(stack_limit=3, max_slots=3, item_filter=FILTER_ACCEPT_ALL)
                foo = Item("foo")
                bar = Item("bar")

                inv += foo_q * foo
                inv += bar_q * bar

                total_items = sum([x.quantity for x in inv._contents])
                self.assertEqual( total_items, foo_q + bar_q)



