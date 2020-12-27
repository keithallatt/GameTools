import subprocess
import sys
import os
import re


def continuous_input(prompt: str, acceptable_responses: list[str]):
    resp = input(prompt)
    while resp not in acceptable_responses:
        resp = input(prompt)
    return resp


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def install_all_packages(modules_to_try):
    successful = True
    for module in modules_to_try:
        try:
            __import__(module)
        except ImportError as e:
            successful = False
            print("Failed to import", module, "\nAttempting to install.")
            response = continuous_input("Install module "+module+" (y/n)? ", ['y', 'n'])
            if response == 'y':
                install(e.name)
                successful = True
            else:
                successful = False
    if successful:
        print("All modules are installed.")
    else:
        print("Missing modules not installed.")
        exit(1)

def find_all_packages():
    # since in a sub-folder
    working_dir = os.sep.join(os.getcwd().split(os.sep)[:-1]) + os.sep

    def add_module_path(sd):
        return working_dir + sd + os.sep + "__init__.py"

    folders = [
        working_dir+subdir for subdir in os.listdir(working_dir)
        if os.path.exists(add_module_path(subdir))
    ]

    import_regex = re.compile(r'^\s*((import (\w+))|(from ([\w\.]+) import (\w+|\*)))$')

    modules_to_import = set()

    for submodule in folders:
        files = os.listdir(submodule)
        for file in files:
            if file == "__pycache__" or file.startswith("."):
                continue

            contents = open(submodule + os.sep + file, 'r').readlines()

            for line in contents:
                m = import_regex.match(line)
                if m is not None:
                    # group 3 and group 5 contain module for either type of import
                    # don't add imports within this project
                    # (such as InventorySystem.inventory or the like)
                    import_module = m.group(3) or m.group(5)
                    for package in folders:
                        package_name = package.split(os.sep)[-1]
                        if package_name in import_module:
                            break
                    else:
                        modules_to_import.add(import_module)

    return list(modules_to_import)


if __name__ == "__main__":
    modules = find_all_packages()
    install_all_packages(modules)
