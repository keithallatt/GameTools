# tests/runner.py
import unittest
import os
import sys
import re
from io import StringIO
import tokenize
import inspect
import importlib


def statistics(condensed=False):
    """ Generate statistics about the project.
         - Number of files scanned,
         - Number of lines of text,
         - Number of source lines of code
    """
    def remove_comments_and_docstrings(source):
        """ Modified slightly from:
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

    def count_lines(start, lines=0, source_loc=0, files=0,
                    show_header=True, begin_start=None, condense=False):
        """ Modified from:
        https://stackoverflow.com/questions/38543709/count-lines-of-code-in-directory-using-python
        """

        if start.endswith("__pycache__"):
            return lines, source_loc, files

        if show_header:
            print('{:>10} |{:>10} |{:>10} | {:<40}'.format('RAW', 'S.L.O.C.', 'TOTAL', 'FILE'))
            print('{:->11}|{:->11}|{:->11}|{:->40}'.format('', '', '', ''))

        for thing in os.listdir(start):
            thing = os.path.join(start, thing)
            if os.path.isfile(thing):
                if thing.endswith('.py'):
                    if thing.endswith("__init__.py"):
                        # see if the file is worth reading
                        if len([line for line in open(thing, 'r').readlines() if
                               len(line.strip()) > 0]) == 0:
                            continue

                    with open(thing, 'r') as f:
                        newlines = f.readlines()
                        source = remove_comments_and_docstrings("\n".join(newlines))
                        newlines = len(newlines)
                        source_lines_num = len(source)

                        source_loc += source_lines_num
                        lines += newlines
                        files += 1

                        pack_name = start.split(os.sep)[-1]

                        if begin_start is not None:
                            rel_dir_of_thing = pack_name + thing.replace(begin_start, '')
                        else:
                            rel_dir_of_thing = pack_name + thing.replace(start, '')

                        if not condense:
                            print('{:>10} |{:>10} |{:>10} | {:<40}'.format(
                                newlines, source_lines_num, lines,
                                rel_dir_of_thing))

        if condense:
            print('{:>10} |{:>10} |{:>10} | {:<40}'.format(
                lines, source_loc, lines, start))

        for thing in os.listdir(start):
            thing = os.path.join(start, thing)
            if os.path.isdir(thing):
                lines, source_loc, files = count_lines(thing, lines, source_loc,
                                                       files, show_header=False,
                                                       begin_start=start, condense=condense)

        return lines, source_loc, files

    working_dir = os.sep.join(os.getcwd().split(os.sep)[:-1]) + os.sep

    def add_module_path(sd):
        """ Provided sd is a folder within the current working directory, and that folder is
            a Python3+ module, format the filename of the __init__.py file """
        return working_dir + sd + os.sep + "__init__.py"

    folders = [
        subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(subdir))
    ]

    total_lines = 0
    total_files = 0
    source_lines = 0

    length_of_dash = 76

    header = True

    for folder in folders:
        if not condensed:
            print("-"*length_of_dash)
            print(f"Counting {working_dir.split(os.sep)[-2] + os.sep + folder}")
            print("-"*length_of_dash)

        count_lines_result = count_lines(start=working_dir + folder, lines=total_lines,
                                         source_loc=source_lines, files=total_files,
                                         show_header=header, condense=condensed)
        total_lines, source_lines, total_files = count_lines_result

        if condensed and header:
            header = False

    print("-"*length_of_dash)

    print("Total number of files: " + str(total_files))
    print("Total lines in files: " + str(total_lines))
    print("Total lines of code: " + str(source_lines))


def run_all_tests():
    # working dir needs to be */GameTools
    working_dir = os.sep.join(os.getcwd().split(os.sep)[:-1]) + os.sep

    def add_module_path(sd):
        """ Provided sd is a folder within the current working directory, and that folder is
            a Python3+ module, format the filename of the __init__.py file """
        return working_dir + sd + os.sep + "__init__.py"

    # get all folders which constitute a python module
    folders = [
        subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(subdir))
    ]

    # find all python files in those modules that are of the form
    # test_<class_name>.py and add to a list of names
    list_of_names = []
    for folder in folders:
        for file in os.listdir(working_dir+folder):
            if file.startswith("test_") and file.endswith(".py"):
                file_path = folder + os.sep + file
                module_path = folder + "." + file[:-3]

                list_of_names.append(module_path)
                importlib.import_module(module_path, file_path)

    # find all classes that extend unittest.case.TestCase and add to a list
    class_tests = []
    for module in list_of_names:
        current_module = sys.modules[module]

        class_members = inspect.getmembers(current_module, inspect.isclass)

        for cls in class_members:
            if unittest.case.TestCase in cls[1].__bases__:
                class_tests.append(cls[1])

    # initialize the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add tests to the test suite from the list from before
    for test_cls in class_tests:
        suite.addTests(loader.loadTestsFromTestCase(test_cls))

    # initialize a runner, pass it your suite and run it
    str_io_stream = StringIO()

    result = unittest.TextTestRunner(verbosity=2, stream=str_io_stream).run(suite)

    stream_result = str_io_stream.getvalue()

    return result, stream_result


if __name__ == "__main__":
    condensed_flag = "--condensed" in sys.argv[1:] or "-c" in sys.argv[1:]

    output_file = open("runner_results.txt", 'w')
    io_stream = StringIO()

    #sys.stdout = io_stream

    runner_result, test_result = run_all_tests()

    m = re.match(r"<unittest\.runner\.TextTestResult run=(\d+) errors=(\d+) failures=(\d+)>",
                 str(runner_result))
    run, errors, failures = m.groups()

    statistics(condensed=condensed_flag)

    print("-"*70)
    print("Running test suite ... ")
    print("-"*70)
    print(test_result)
    print("Tests run: %s\nErrors: %s\nFailures: %s\n\n" % (run, errors, failures))

    sys.stdout = sys.__stdout__
    print(io_stream.getvalue().replace("ok", "ok\n"))

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    to_file = ansi_escape.sub('', io_stream.getvalue())

    output_file.write(to_file)

    output_file.close()
