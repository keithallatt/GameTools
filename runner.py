# tests/runner.py
import unittest
import os


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


def count_lines(start, lines=0, header=True, begin_start=None):
    if header:
        print('{:>10} |{:>10} | {:<20}'.format('ADDED', 'TOTAL', 'FILE'))
        print('{:->11}|{:->11}|{:->20}'.format('', '', ''))

    for thing in os.listdir(start):
        thing = os.path.join(start, thing)
        if os.path.isfile(thing):
            if thing.endswith('.py'):
                with open(thing, 'r') as f:
                    newlines = f.readlines()
                    newlines = len(newlines)
                    lines += newlines

                    if begin_start is not None:
                        reldir_of_thing = '.' + thing.replace(begin_start, '')
                    else:
                        reldir_of_thing = '.' + thing.replace(start, '')

                    print('{:>10} |{:>10} | {:<20}'.format(
                            newlines, lines, reldir_of_thing))

    for thing in os.listdir(start):
        thing = os.path.join(start, thing)
        if os.path.isdir(thing):
            lines = count_lines(thing, lines, header=False, begin_start=start)

    return lines

"""
total_lines = 0
total_lines += count_lines(start="/Users/kallatt/GitHub/GameTools/InventorySystem")
total_lines += count_lines(start="/Users/kallatt/GitHub/GameTools/MapSystem")
total_lines += count_lines(start="/Users/kallatt/GitHub/GameTools/NPCSystem")
total_lines += count_lines(start="/Users/kallatt/GitHub/GameTools/PuzzleSystem")
total_lines += count_lines(start="/Users/kallatt/GitHub/GameTools/CombatSystem")
print("Total lines of code: "+str(total_lines))
#"""
