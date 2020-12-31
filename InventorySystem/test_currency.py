from collections import OrderedDict
from unittest import TestCase
import tempfile
import numpy as np
import json
import string
import random
# need MapSystem.map since suite outside inventory system folder
from InventorySystem.currency import PriceRegistry, Wallet, CurrencySystem, CurrencyException


class CurrencyTest(TestCase):
    def test_price_registry(self):
        """ Test the price registry to see if reading from a properly formatted JSON file
            is read correctly by the price registry."""
        letters = string.ascii_lowercase
        num_words = 200
        word_len = 15
        items = [''.join(random.choice(letters) for _ in range(word_len))
                 for __ in range(num_words)]

        # perform 500 tests.
        for _ in range(200):
            num_of = np.random.randint(1, len(items)+1)
            item_list = (list(set(np.random.choice(items, num_of))))

            item_dict = {}

            for item in item_list:
                item_dict.update({item: np.random.randint(1, 100)})

            tmp = tempfile.NamedTemporaryFile(delete=True)
            pr: PriceRegistry
            try:
                tmp.write(json.dumps(item_dict).encode('ascii'))
                tmp.seek(0)
                # create registry from file.
                pr = PriceRegistry(read_file=tmp)
            finally:
                tmp.close()  # deletes the file

            if pr is None:
                self.fail("Exception occurred in creating file and creating registry.")
            else:
                for item in item_dict:
                    if pr.read_from_registry(item) != item_dict[item]:
                        self.fail("Item '{0}' has price {1} but registry has price {2}".format(
                            item, item_dict[item], pr.read_from_registry(item)))

    def test_wallet(self):
        """ Test general wallet functionality """
        # test wallet addition
        for init_q in range(100):
            for add_q in range(100):
                wallet_init = Wallet(amount=init_q)
                wallet_add = Wallet(amount=add_q)

                wallet_init += wallet_add

                self.assertEqual(wallet_init.unstack(), init_q + add_q)

    def test_currency_exception(self):
        """ Test if certain operations raise exceptions as they should """
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
        """ Create and test currency system functions """
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
