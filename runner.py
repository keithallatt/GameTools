# tests/runner.py
import unittest
import os
from io import StringIO
import re

# import test modules
from InventorySystem.test_inventory import InventoryTest
from MapSystem.test_map import MapTest
from NPCSystem.test_npc import NPCTest


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


def statistics():
    working_dir = os.getcwd() + os.sep

    total_lines = 0
    folders = [
        "InventorySystem",
        "MapSystem",
        "NPCSystem",
        "PuzzleSystem",
        "CombatSystem"
    ]

    for folder in folders:
        print("-"*44)
        print(f"Counting {working_dir + folder}")
        print("-"*44)
        total_lines = count_lines(start=working_dir + folder, lines=total_lines)
    print("Total lines of code: " + str(total_lines))


def run_all_tests():
    # initialize the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add tests to the test suite
    suite.addTests(loader.loadTestsFromTestCase(InventoryTest))
    suite.addTests(loader.loadTestsFromTestCase(MapTest))
    suite.addTests(loader.loadTestsFromTestCase(NPCTest))

    # initialize a runner, pass it your suite and run it
    iostream = StringIO()

    result = unittest.TextTestRunner(verbosity=2, stream=iostream).run(suite)

    stream_result = iostream.getvalue()

    return result, stream_result


result, stream_result = run_all_tests()

pat = re.compile(r"<unittest\.runner\.TextTestResult run=(\d+) errors=(\d+) failures=(\d+)>")

m = pat.match(str(result))
run, errors, failures = m.groups()

print("-"*70)
print("Running test suite ... ")
print("-"*70)
print(stream_result)
print("Tests run: %s\nErrors: %s\nFailures: %s\n\n" % (run, errors, failures))


statistics()
