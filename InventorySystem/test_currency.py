from unittest import TestCase
import tempfile
import numpy as np
import json
import string
import random
# need MapSystem.map since suite outside inventory system folder
from InventorySystem.currency import PriceRegistry, Wallet, CurrencySystem
import InventorySystem.currency as curr_sys


class CurrencyTest(TestCase):
    def test_price_registry(self):

        letters = string.ascii_lowercase
        num_words = 200
        word_len = 15
        items = [''.join(random.choice(letters) for _ in range(word_len))
                 for __ in range(num_words)]

        for i in range(500):
            num_of = np.random.randint(1, len(items)+1)
            item_list = (list(set(np.random.choice(items, num_of))))

            item_dict = {}

            for item in item_list:
                item_dict.update({item: np.random.randint(1, 100)})

            tmp = tempfile.NamedTemporaryFile(delete=True)
            pr = None
            try:
                # do stuff with temp
                item_json = json.dumps(item_dict)

                item_encoded = item_json.encode('ascii')

                tmp.write(item_encoded)
                tmp.seek(0)

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
        pass

    def test_currency_system(self):
        pass
