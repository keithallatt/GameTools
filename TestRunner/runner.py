# tests/runner.py
import unittest
import os
import sys
import re
from io import StringIO
import tokenize
import inspect
import importlib
import textwrap
from pathlib import Path

length_of_dash = 84


def add_module_path(working_dir, sd):
    """ Provided sd is a folder within the working directory, and that folder is
        a Python3+ module, format the filename of the __init__.py file. """
    return working_dir + sd + os.sep + "__init__.py"


def remove_comments_and_docstrings(source_code):
    """ Modified slightly from: <a href="
        https://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
        ">Here.</a> Removes comments and docstrings from source code, to allow count_lines to
         accurately count the number of lines of code. """
    io_obj = StringIO(source_code)
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
    """ Modified slightly from: <a href="
        https://stackoverflow.com/questions/38543709/count-lines-of-code-in-directory-using-python
        ">Here.</a> Counts number of source lines of code and raw number of lines in each file. """

    if start.endswith("__pycache__"):
        return lines, source_loc, files

    if show_header:
        print('{:>10} |{:>10} |{:>10} |{:>10} | {:<20}'.format(
            'Raw', 'Source', 'Total', 'Source', 'File'))
        print('{:->11}\u253C{:->11}\u253C{:->11}\u253C{:->11}\u253C{:->36}'.format(
            '', '', '', '', ''))

    in_package = 0
    for thing in os.listdir(start):
        thing = os.path.join(start, thing)
        if os.path.isfile(thing):
            if thing.endswith('.py'):
                if thing.endswith("__init__.py"):
                    # see if the file is worth reading
                    # if there is nothing by whitespace in this file, then ignore it.
                    if len([line for line in open(thing, 'r').readlines() if
                            len(line.strip()) > 0]) == 0:
                        continue

                with open(thing, 'r') as f:
                    newlines = f.readlines()
                    source_code_no_comments = \
                        remove_comments_and_docstrings("\n".join(newlines))
                    newlines = len(newlines)
                    source_lines_num = len(source_code_no_comments)

                    source_loc += source_lines_num
                    in_package += source_lines_num
                    lines += newlines
                    files += 1

                    if begin_start is not None:
                        rel_dir_of_thing = "." + thing.replace(begin_start, '')
                    else:
                        rel_dir_of_thing = "." + thing.replace(start, '')

                    if not condense:
                        print('{:>10} |{:>10} |{:>10} |{:>10} | {:<20}'.format(
                            newlines, source_lines_num, lines,
                            source_loc, rel_dir_of_thing))

    if condense:
        print('{:>10} |{:>10} |{:>10} |{:>10} | {:<30}'.format(
            lines, source_loc, lines, in_package, start.split(os.sep)[-1]))

    for thing in os.listdir(start):
        thing = os.path.join(start, thing)
        if os.path.isdir(thing):
            lines, source_loc, files = count_lines(thing, lines, source_loc,
                                                   files, show_header=False,
                                                   begin_start=start, condense=condense)

    return lines, source_loc, files


def statistics(source: str, condensed: bool = False):
    """ Generate statistics about the project, such as the number of files scanned,
        the number of lines of text, and the number of source lines of code. """
    working_dir = source
    if working_dir[-1] != os.sep:
        working_dir += os.sep

    folders = [
        subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(working_dir, subdir))
    ]

    total_lines = 0
    total_files = 0
    source_lines = 0

    header = True
    first = True

    for folder in folders:
        if condensed and first:
            print('{:->11}\u252C{:->11}\u252C{:->11}\u252C{:->48}'.format('', '', '', ''))
            first = False
        elif not condensed:
            if first:
                print("-" * length_of_dash)
                first = False
            else:
                print('{:->11}\u2534{:->11}\u2534{:->11}\u2534{:->48}'.format('', '', '', ''))

            print(f"Counting {working_dir.split(os.sep)[-2] + os.sep + folder}")
            print('{:->11}\u252C{:->11}\u252C{:->11}\u252C{:->48}'.format('', '', '', ''))

        count_lines_result = count_lines(start=working_dir + folder, lines=total_lines,
                                         source_loc=source_lines, files=total_files,
                                         show_header=header, condense=condensed)
        total_lines, source_lines, total_files = count_lines_result

        if condensed and header:
            header = False

    print('{:->11}\u2534{:->11}\u2534{:->11}\u2534{:->48}'.format('', '', '', ''))

    print("Total number of files: " + str(total_files))
    print("Total lines in files: " + str(total_lines))
    print("Total lines of code: " + str(source_lines))


def run_all_tests(source: str):
    """ Run all unit tests as found. """
    # working dir needs to be **/GameTools/
    working_dir = source
    if working_dir[-1] != os.sep:
        working_dir += os.sep

    # get all folders which constitute a python module
    folders = [
        subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(working_dir, subdir))
    ]

    # find all python files in those modules that are of the form
    # test_<class_name>.py and add to a list of names
    list_of_names = []
    for folder in folders:
        for file in os.listdir(working_dir + folder):
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

    # Expecting to be run in TestRunner package
    source_path = Path(__file__).resolve()
    source_dir = str(source_path.parent.parent)

    if source_dir not in sys.path:
        sys.path.append(source_dir)

    output_file = open("runner_results.txt", 'w')
    io_stream = StringIO()

    # capture all output so it can be preprocessed and saved to file.
    sys.stdout = io_stream

    runner_result, test_result = run_all_tests(source=source_dir)

    m = re.match(r"<unittest\.runner\.TextTestResult run=(\d+) errors=(\d+) failures=(\d+)>",
                 str(runner_result))
    run, errors, failures = m.groups()

    statistics(condensed=condensed_flag, source=source_dir)

    print("-" * length_of_dash)
    print("Running test suite ... ")
    print("-" * length_of_dash)
    print(test_result)
    print("Tests run: %s\nErrors: %s\nFailures: %s\n\n" % (run, errors, failures))
    print("-" * length_of_dash)

    sys.stdout = sys.__stdout__

    output = io_stream.getvalue()

    output_lines = output.split("\n")

    output_lines = [line.rstrip() for line in output_lines]

    output_lines = ["-" * length_of_dash if line.replace("-", "").strip() == ""
                    and len(line.strip()) > 0 else line for line in output_lines]

    output_lines = sum([textwrap.wrap(line, width=length_of_dash) for line in output_lines], [])
    output_lines = ("\n".join(output_lines).replace("ok", "ok\n")).split("\n")

    output_lines = [line + " " * (length_of_dash - len(line)) for line in output_lines]

    def output_line_format(line):
        return [u"\u251C-", "-\u2524"] if line.startswith("----") else ["\u2502 ", " \u2502"]

    output_lines = [line.join(output_line_format(line)) for line in output_lines]
    output_lines = [output_lines[0].replace("\u251C", "\u250C").replace("\u2524", "\u2510")] + \
        output_lines[1:-1] + \
                   [output_lines[-1].replace("\u251C", "\u2514").replace("\u2524", "\u2518")]

    output = "\n".join(output_lines).replace("-", "\u2500")

    print(output)

    output_file.write(output)

    output_file.close()
