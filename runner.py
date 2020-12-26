# tests/runner.py
import unittest
import os
import sys
import re
from colorama import Fore
from io import StringIO
import tokenize

# import test modules
from InventorySystem.test_inventory import InventoryTest
from MapSystem.test_map import MapTest
from NPCSystem.test_npc import NPCTest


def statistics():
    def remove_comments_and_docstrings(source):
        """
        Modified slightly from:
        https://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
        """
        io_obj = StringIO(source)
        out = ""
        prev_tok_type = tokenize.INDENT
        last_line_no = -1
        last_col = 0
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            if start_line > last_line_no:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            if token_type == tokenize.COMMENT:
                pass
            elif token_type == tokenize.STRING:
                if prev_tok_type != tokenize.INDENT:
                    if prev_tok_type != tokenize.NEWLINE:
                        if start_col > 0:
                            out += token_string
            else:
                out += token_string
            prev_tok_type = token_type
            last_col = end_col
            last_line_no = end_line
        return [line for line in out.splitlines() if line.strip()]

    def count_lines(start, lines=0, files=0, header=True, begin_start=None):
        """
        Modified from:
        https://stackoverflow.com/questions/38543709/count-lines-of-code-in-directory-using-python
        """
        if header:
            print('{:>10} |{:>10} |{:>10} | {:<40}'.format('RAW', 'S.L.O.C.', 'TOTAL', 'FILE'))
            print('{:->11}|{:->11}|{:->11}|{:->40}'.format('', '', '', ''))

        for thing in os.listdir(start):
            thing = os.path.join(start, thing)
            if os.path.isfile(thing):
                if thing.endswith('.py') and not thing.endswith("__init__.py"):
                    with open(thing, 'r') as f:
                        newlines = f.readlines()
                        source_lines = remove_comments_and_docstrings("\n".join(newlines))
                        newlines = len(newlines)
                        source_lines_num = len(source_lines)

                        lines += source_lines_num
                        files += 1

                        pack_name = start.split(os.sep)[-1]

                        if begin_start is not None:
                            rel_dir_of_thing = pack_name + thing.replace(begin_start, '')
                        else:
                            rel_dir_of_thing = pack_name + thing.replace(start, '')

                        print('{:>10} |{:>10} |{:>10} | {:<40}'.format(
                            newlines, source_lines_num, lines,
                            Fore.MAGENTA+rel_dir_of_thing+Fore.RESET))

        for thing in os.listdir(start):
            thing = os.path.join(start, thing)
            if os.path.isdir(thing):
                lines, files = count_lines(thing, lines, files, header=False, begin_start=start)

        return lines, files

    working_dir = os.getcwd() + os.sep

    def add_module_path(sd):
        return working_dir + sd + os.sep + "__init__.py"

    folders = [
        subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(subdir))
    ]

    total_lines = 0
    total_files = 0

    length_of_dash = 76
    for folder in folders:
        print("-"*length_of_dash)
        print(Fore.RED + f"Counting {working_dir.split(os.sep)[-2] + os.sep + folder}" + Fore.RESET)
        print("-"*length_of_dash)
        total_lines, total_files = count_lines(start=working_dir + folder,
                                               lines=total_lines,
                                               files=total_files)
    print("-"*length_of_dash)

    print("Total number of files: " + str(total_files))
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
    str_io_stream = StringIO()

    result = unittest.TextTestRunner(verbosity=2, stream=str_io_stream).run(suite)

    stream_result = str_io_stream.getvalue()

    return result, stream_result


if __name__ == "__main__":
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
    print(Fore.RESET + test_result.replace(" ... ok",
                                           f" ... {Fore.GREEN}ok{Fore.RESET}") + Fore.RESET)
    print("Tests run: %s\nErrors: %s\nFailures: %s\n\n" % (run, errors, failures))

    statistics()

    sys.stdout = sys.__stdout__
    print(io_stream.getvalue())

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    to_file = ansi_escape.sub('', io_stream.getvalue())

    output_file.write(to_file)

    output_file.close()
