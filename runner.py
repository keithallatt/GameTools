# tests/runner.py
import unittest

# import your test modules
from InventorySystem.test_inventory import InventoryTest
from MapSystem.test_map import MapTest
from NPCSystem.test_npc import NPCTest

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromTestCase(InventoryTest))
suite.addTests(loader.loadTestsFromTestCase(MapTest))
suite.addTests(loader.loadTestsFromTestCase(NPCTest))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
