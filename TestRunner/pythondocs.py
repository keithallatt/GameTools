import os
import importlib
import sys
import inspect
from bs4 import BeautifulSoup
import re


class PythonDocs:
    # Percent width
    method_column_width = 20

    """ HTML version of the help function, but a focus on the docstrings. """
    @staticmethod
    def generate_python_docstrings(thing):
        """ Get docstrings from object but return an empty string if no docstrings exist. """
        if thing.__doc__ is not None:
            # rudimentary grammar check
            doc = thing.__doc__
            if doc.strip() != "":
                if not doc.strip().endswith("."):
                    print("No '.' ending:", thing)
                if not doc.strip()[0] == doc.strip()[0].upper():
                    print("No capitalization:", thing)
            else:
                print("Missing docstring:", thing)

            return doc
        else:
            if str(thing).find("class") == -1:
                print("Missing docstring:", str(thing)[:str(thing).index("at")].strip()+">")
            else:
                print("Class missing docstring:", thing)
            return ""

    @staticmethod
    def generate_class_python_docs(cls, superclass=None):
        """ Generate the portion of the Python Docs relating to this particular class. """
        class_name, class_ref = cls
        class_members = inspect.getmembers(class_ref, predicate=inspect.isfunction)
        class_members += inspect.getmembers(class_ref, predicate=inspect.ismethod)
        class_members = [m for m in class_members if m[1].__module__ == class_ref.__module__]

        subclass_members = inspect.getmembers(class_ref, predicate=inspect.isclass)
        subclass_members = [m for m in subclass_members if m[1].__module__ == class_ref.__module__]

        if superclass is not None:
            new_superclass = superclass + "." + class_name
        else:
            new_superclass = class_name

        yield "<div class=\"class_name\">" + new_superclass + "</div>\n"
        yield "<div>" + PythonDocs.generate_python_docstrings(class_ref) + "</div>\n"
        yield "<br />"

        if len(class_members) != 0:
            yield "<table style=\"width:100%\">\n"
            yield "<tr><th style=\"width:" + str(PythonDocs.method_column_width)+"%\">"
            yield "Method name"
            yield "</th><th>"
            yield "Description"
            yield "</th></tr>\n"

            class_members.sort(key=lambda x: x[0])

            for method in class_members:
                yield "<tr>\n"
                yield "<th style=\"width:" + str(PythonDocs.method_column_width)+"%\">\n"
                yield method[0] + "\n</th>\n<td>\n"
                yield PythonDocs.generate_python_docstrings(method[1])
                yield "</td>\n</tr>\n"

            yield "</table><br />\n"

        if len(subclass_members) != 0:
            for subclass in subclass_members:
                if superclass is not None:
                    new_superclass = superclass+"."+class_name
                else:
                    new_superclass = class_name
                for line in PythonDocs.generate_class_python_docs(subclass, new_superclass):
                    yield line

        yield "<br />"

    @staticmethod
    def generate_file_python_docs(parent_level_up: int = 0):
        """ Generate Python Docs for this project. """
        working_dir = os.sep.join(os.getcwd().split(os.sep)[:-parent_level_up]) + os.sep

        def add_module_path(sd):
            """ Provided sd is a folder within the current working directory, and that folder is
                a Python3+ module, format the filename of the __init__.py file. """
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
                if not file.endswith("__init__.py") and file.endswith(".py"):
                    file_path = folder + os.sep + file
                    module_path = folder + "." + file[:-3]

                    list_of_names.append(module_path)
                    importlib.import_module(module_path, file_path)

        list_of_names.sort()

        for module in list_of_names:
            current_module = sys.modules[module]

            yield "<div class=\"module_name\">" + module + "</div><br />\n"

            class_members = inspect.getmembers(current_module, inspect.isclass)
            class_members = [m for m in class_members if m[1].__module__ == module]

            function_members = inspect.getmembers(current_module, inspect.isfunction)
            function_members = [m for m in function_members if m[1].__module__ == module]

            method_members = inspect.getmembers(current_module, inspect.ismethod)
            method_members = [m for m in method_members if m[1].__module__ == module]

            if len(function_members) != 0:
                yield "<table style=\"width:100%\">\n"
                yield "<tr><th style=\"width:" + str(PythonDocs.method_column_width)+"%\">"
                yield "Functions"
                yield "</th><th>"
                yield "Description"
                yield "</th></tr>\n"

                for method in function_members:
                    yield "<tr>\n"
                    yield "<th style=\"width:" + str(PythonDocs.method_column_width)+"%\">\n"
                    yield method[0] + "\n</th>\n<td>\n"
                    yield PythonDocs.generate_python_docstrings(method[1])
                    yield "</td>\n</tr>\n"

                yield "</table><br />\n"

            if len(method_members) != 0:
                yield "<table style=\"width:100%\">\n"
                yield "<tr><th style=\"width:" + str(PythonDocs.method_column_width)+"%\">"
                yield "Methods"
                yield "</th><th>"
                yield "Description"
                yield "</th></tr>\n"

                for method in method_members:
                    yield "<tr>\n"
                    yield "<th style=\"width:" + str(PythonDocs.method_column_width)+"%\">\n"
                    yield method[0] + "\n</th>\n<td>\n"
                    yield PythonDocs.generate_python_docstrings(method[1])
                    yield "</td>\n</tr>\n"

                yield "</table><br />\n"

            for cls in class_members:
                for thing in PythonDocs.generate_class_python_docs(cls):
                    yield thing

            yield "<br />\n"

    @staticmethod
    def generate_css_python_docs():
        """ Generate the CSS required for the Python Docs html file. """
        yield "body {background-color: #f5f5dc;}\n"
        yield "table, th, td { border: 1px solid black; }\n"
        yield "td {\npadding-top: 5px; \npadding-right: 5px;"
        yield "\npadding-bottom: 5px;\npadding-left: 10px;\n}\n"
        yield ".module_name { color: #56563e; font-size: 20pt; font-weight: bold;}\n"
        yield ".class_name { color: #56563e; font-size: 15pt; font-weight: bold;}\n"

    @staticmethod
    def generate_python_docs(parent_level_up: int = 0):
        """ Write the CSS and HTML to file to view the Python Docs. """
        with open("python_doc_out.html", 'w') as output_html:
            html_string = "<!DOCTYPE html>\n<html>\n<head>\n<style>"
            for chunk in PythonDocs.generate_css_python_docs():
                try:
                    html_string += chunk
                except TypeError:
                    print(chunk)
            html_string += "\n</style>\n</head>\n<body>"
            for chunk in PythonDocs.generate_file_python_docs(parent_level_up=parent_level_up):
                try:
                    html_string += chunk
                except TypeError:
                    print(chunk)
            html_string += "\n</body>"

            r = re.compile(r'^(\s*)', re.MULTILINE)

            formatted = BeautifulSoup(html_string, 'html.parser').prettify()
            output_html.write(r.sub(r'\1\1', formatted))


if __name__ == "__main__":
    PythonDocs.generate_python_docs(parent_level_up=1)
