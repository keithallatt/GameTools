# tests/runner.py
import unittest
import os
import sys
import re
from colorama import Fore
from io import StringIO

# import test modules
from InventorySystem.test_inventory import InventoryTest
from MapSystem.test_map import MapTest
from NPCSystem.test_npc import NPCTest


def statistics():
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

                        pack_name = start.split(os.sep)[-1]

                        if begin_start is not None:
                            rel_dir_of_thing = pack_name + thing.replace(begin_start, '')
                        else:
                            rel_dir_of_thing = pack_name + thing.replace(start, '')

                        print('{:>10} |{:>10} | {:<20}'.format(
                            newlines, lines, Fore.MAGENTA+rel_dir_of_thing+Fore.RESET))

        for thing in os.listdir(start):
            thing = os.path.join(start, thing)
            if os.path.isdir(thing):
                lines = count_lines(thing, lines, header=False, begin_start=start)

        return lines

    working_dir = os.getcwd() + os.sep

    def add_module_path(sd):
        return working_dir + sd + os.sep + "__init__.py"

    folders = [
        subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(subdir))
    ]

    total_lines = 0

    for folder in folders:
        print("-"*44)
        print(Fore.RED + f"Counting {working_dir.split(os.sep)[-2] + os.sep + folder}" + Fore.RESET)
        print("-"*44)
        total_lines = count_lines(start=working_dir + folder, lines=total_lines)
        print("-"*44)

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
    io_stream = StringIO()

    result = unittest.TextTestRunner(verbosity=2, stream=io_stream).run(suite)

    stream_result = io_stream.getvalue()

    return result, stream_result


output_file = open("runner_results.txt", 'w')
io_stream = StringIO()

sys.stdout = io_stream

runner_result, test_result = run_all_tests()

pat = re.compile(r"<unittest\.runner\.TextTestResult run=(\d+) errors=(\d+) failures=(\d+)>")

m = pat.match(str(runner_result))
run, errors, failures = m.groups()

print("-"*70)
print(Fore.MAGENTA+"Running test suite ... " + Fore.RESET)
print("-"*70)
print(Fore.RESET + test_result.replace(" ... ok", f" ... {Fore.GREEN}ok{Fore.RESET}") + Fore.RESET)
print("Tests run: %s\nErrors: %s\nFailures: %s\n\n" % (run, errors, failures))

if int(failures) > 0 or int(errors) > 0:
    exit(0)

statistics()

sys.stdout = sys.__stdout__
print(io_stream.getvalue())

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
to_file = ansi_escape.sub('', io_stream.getvalue())

output_file.write(to_file)

output_file.close()
