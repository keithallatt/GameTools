from unittest import TestCase
# need InventorySystem.inventory since suite outside inventory system folder
from InventorySystem.inventory import Item, InventorySystem, InventoryException, ItemFilter, Wallet, CurrencySystem, CurrencyException
import numpy as np
from collections import OrderedDict


class InventoryTest(TestCase):
    """ InventorySystem module test cases. """
    def test_item(self):
        """ Test item integer multiplications and item item additions. """
        # test a range of multiplications of items
        for init_q in range(50):
            for multiply_q in range(50):
                foo = Item("foo", quantity=init_q)
                multiply_foo = foo * multiply_q

                self.assertEqual(multiply_foo.quantity, multiply_q * init_q)

        # test a range of addition of items
        for init_q in range(50):
            for add_q in range(50):
                if init_q != 3 or add_q != 3:
                    continue

                foo1 = Item("foo", quantity=init_q)
                foo2 = Item("foo", quantity=add_q)

                foo1 += foo2

                self.assertEqual(foo1.quantity, init_q + add_q)

    def test_inventory_exception(self):
        """ Test whether or not exceptions are raised by illegal operations. """
        inv = InventorySystem(stack_limit=3,
                              max_slots=3,
                              item_filter=ItemFilter(accept_all=True))
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
        """ Test inventory system for its ability to add multiple items to itself. """
        # test adding different items, making sure all are added
        for foo_q in range(50):
            for bar_q in range(50):

                inv = InventorySystem(stack_limit=99,
                                      item_filter=ItemFilter(accept_all=True))
                foo = Item("foo")
                bar = Item("bar")

                inv += foo_q * foo
                inv += bar_q * bar

                total_items = sum([x.quantity for x in inv._contents])
                self.assertEqual(total_items, foo_q + bar_q)

    def test_wallet(self):
        """ Test general wallet functionality. """
        # test wallet addition
        for init_q in range(100):
            for add_q in range(100):
                wallet_init = Wallet(amount=init_q)
                wallet_add = Wallet(amount=add_q)

                wallet_init += wallet_add

                self.assertEqual(wallet_init.unstack(), init_q + add_q)

    def test_currency_exception(self):
        """ Test if certain operations raise exceptions as they should. """
        for init_q in range(100):
            with self.assertRaises(CurrencyException) as context:
                wallet_init = Wallet(amount=init_q)
                wallet_sub = Wallet(amount=init_q + np.random.randint(1, 10))
                wallet_init -= wallet_sub

            self.assertTrue('Cannot have indebted wallet' in
                            context.exception.msg)

        with self.assertRaises(CurrencyException) as context:
            CurrencySystem(relative_denominations=OrderedDict({}))
        self.assertTrue('Cannot have empty currency system' in
                        context.exception.msg)

        for base_denomination in range(2, 100):
            with self.assertRaises(CurrencyException) as context:
                CurrencySystem(relative_denominations=OrderedDict({"Base": base_denomination}))

            self.assertTrue('Cannot have most valued denomination worth != 1' in
                            context.exception.msg)

    def test_currency_system(self):
        """ Create and test currency system functions. """
        for _ in range(100):
            num_denominations = np.random.randint(2, 10)
            denominations = [chr(ord('A')+i) + str(i+1) for i in range(num_denominations)]
            rel_am = [1] + [np.random.randint(2, 21) for _ in range(num_denominations - 1)]
            relative_denominations = OrderedDict({denominations[i]: rel_am[i]
                                                  for i in range(num_denominations)})

            curr_sys = CurrencySystem(relative_denominations=relative_denominations)

            for i in range(num_denominations):
                for j in range(num_denominations):
                    w_i = Wallet(curr_sys=curr_sys)
                    w_j = Wallet(curr_sys=curr_sys)

                    w_i.add_currency(denominations[i], 1)
                    w_j.add_currency(denominations[j], 1)

                    self.assertEqual(i < j,  w_i.unstack() > w_j.unstack())
                    self.assertEqual(i > j,  w_i.unstack() < w_j.unstack())
                    self.assertEqual(i == j, w_i.unstack() == w_j.unstack())
