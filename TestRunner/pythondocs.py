import os
import importlib
import sys
import inspect


class PythonDocs:
    @staticmethod
    def generate_python_docstrings(thing):
        """ Get docstrings from object but return an empty string if no docstrings exist. """
        if thing.__doc__ is not None:
            return thing.__doc__
        else:
            return ""

    @staticmethod
    def generate_class_python_docs(cls):
        """ Generate the portion of the Python Docs relating to this particular class. """
        class_name, class_ref = cls
        class_members = inspect.getmembers(class_ref, predicate=inspect.isfunction)
        class_members = [m for m in class_members if m[1].__module__ == class_ref.__module__]

        yield "<div class=\"class_name\">" + class_name + "</div>\n"
        yield "<div>" + PythonDocs.generate_python_docstrings(class_ref) + "</div>\n"

        if len(class_members) != 0:
            yield "<table style=\"width:100%\">\n"
            yield "<tr><th style=\"width:33%\">"
            yield "Method name"
            yield "</th><th>"
            yield "Description"
            yield "</th></tr>\n"

            for method in class_members:
                yield "<tr>\n"
                yield "<th style=\"width:33%\">\n" + method[0] + "\n</th>\n"
                yield "<td>\n"
                yield PythonDocs.generate_python_docstrings(method[1])
                yield "</td>\n"
                yield "</tr>\n"

            yield "</table><br />\n"

    @staticmethod
    def generate_file_python_docs(parent_level_up: int = 0):
        """ Generate Python Docs for this project. """
        working_dir = os.sep.join(os.getcwd().split(os.sep)[:-parent_level_up]) + os.sep

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
                if not file.endswith("__init__.py") and file.endswith(".py"):
                    file_path = folder + os.sep + file
                    module_path = folder + "." + file[:-3]

                    list_of_names.append(module_path)
                    importlib.import_module(module_path, file_path)

        for module in list_of_names:
            current_module = sys.modules[module]

            yield "<div class=\"module_name\">" + module + "</div><br />\n"

            class_members = inspect.getmembers(current_module, inspect.isclass)
            class_members = [m for m in class_members if m[1].__module__ == module]
            for cls in class_members:
                for thing in PythonDocs.generate_class_python_docs(cls):
                    yield thing

            yield "<br />\n"

    @staticmethod
    def generate_css_python_docs():
        """ Generate the CSS required for the Python Docs html file. """
        yield "body {background-color: #f5f5dc;}\n"
        yield "table, th, td { border: 1px solid black; }\n"
        yield "td {\n\tpadding-top: 5px; \n\tpadding-right: 5px;"
        yield "\n\tpadding-bottom: 5px;\n\tpadding-left: 10px;\n}\n"
        yield ".module_name { color: #56563e; font-size: 20pt; font-weight: bold;}\n"
        yield ".class_name { color: #56563e; font-size: 15pt; font-weight: bold;}\n"

    @staticmethod
    def generate_python_docs(parent_level_up: int = 0):
        """ Write the CSS and HTML to file to view the Python Docs. """
        with open("python_doc_out.html", 'w') as output_html:
            output_html.write("<!DOCTYPE html>\n<html>\n<head>\n<style>\n")
            for chunk in PythonDocs.generate_css_python_docs():
                try:
                    output_html.write(chunk)
                except TypeError:
                    print(chunk)
            output_html.write("\n</style>\n</head>\n<body>")
            for chunk in PythonDocs.generate_file_python_docs(parent_level_up=parent_level_up):
                try:
                    output_html.write(chunk)
                except TypeError:
                    print(chunk)
            output_html.write("\n</body>")


if __name__ == "__main__":
    PythonDocs.generate_python_docs(parent_level_up=1)
