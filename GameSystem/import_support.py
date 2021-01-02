import subprocess
import sys
import os
import re


class ImportSupport:
    """ Collection of methods to find and install modules required for this project
        dynamically, as to allow this script to run at any time to verify the modules
        required. """
    @staticmethod
    def _continuous_input(prompt: str, acceptable_responses: list[str], ignore_case=True):
        """ Requests input repeatedly until a specific kind of message received. """
        if len(acceptable_responses) == 0:
            # if no acceptable responses, return the
            return input(prompt)

        # allows for case sensitive v.s. case insensitive.
        responses = {(accept_resp.lower() if ignore_case else accept_resp): accept_resp
                     for accept_resp in acceptable_responses}

        resp = input(prompt)

        # repeatedly ask for input until a response within the acceptable responses list is given
        while (resp.lower() if ignore_case else resp) not in list(responses.keys()):
            resp = input(prompt)

        # return the response as it appears in acceptable_responses
        return responses[resp.lower()]

    @staticmethod
    def _install(package):
        """ Attempt to install package using 'python -m pip install <...>' command.
            Returns the success of the installation. """
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return True
        except subprocess.CalledProcessError:
            # subprocess.check_call will either return if exit code 0,
            # or throw called process error.
            return False

    @staticmethod
    def _install_all_packages(modules_to_try):
        """ Attempt to install all packages. In the case of failure, end the program. """
        successful = True
        print("Importing modules:")
        for module in modules_to_try:
            try:
                # if you can import the module, it is installed.
                __import__(module)
                print(" >> "+module)
            except ImportError as e:
                # if it isn't installed, ask to install it.
                print("Failed to import", module, "\nAttempting to install.")
                response = ImportSupport._continuous_input(
                    "Install module "+module+" (y/n)? ", ['y', 'n'])
                if response == 'y':
                    successful = ImportSupport._install(e.name)
                else:
                    successful = False
        if successful:
            print("\nAll {0} modules are installed.".format(len(modules_to_try)))
        else:
            # if any modules are not installed and the user declines to install them
            # then the program won't run.
            print("\nMissing modules not installed.")
            exit(1)

    @staticmethod
    def _find_all_packages():
        """ Find all import statements of form:
            'import package',
            'import package as name', and
            'from package import things'
            """
        # since in a sub-folder
        working_dir = os.sep.join(os.getcwd().split(os.sep)[:-1]) + os.sep

        def add_module_path(sd):
            return working_dir + sd + os.sep + "__init__.py"

        folders = [
            working_dir+subdir for subdir in os.listdir(working_dir)
            if os.path.exists(add_module_path(subdir))
        ]

        import_re = re.compile(r'^\s*((import (\w+)( as \w+)?)|(from ([\w.]+) import (\w+|\*)))$')

        # don't allow repeats
        modules_to_import = set()

        for submodule in folders:
            files = os.listdir(submodule)
            for file in files:
                # don't read in hidden files or pycache files.
                if file == "__pycache__" or file.startswith("."):
                    continue

                contents = open(submodule + os.sep + file, 'r').readlines()

                for line in contents:
                    m = import_re.match(line)
                    if m is not None:
                        # group 3 and group 6 contain module for either type of import
                        # don't add imports within this project
                        # (such as InventorySystem.inventory or the like)
                        import_module = m.group(3) or m.group(6)
                        for package in folders:
                            package_name = package.split(os.sep)[-1]
                            if package_name in import_module:
                                break
                        else:
                            modules_to_import.add(import_module)

        modules_to_import = list(modules_to_import)

        modules_to_import.sort()

        return modules_to_import

    @staticmethod
    def find_and_install_packages():
        """ Use private methods to separately use introspective code inspection
            to read out which modules are necessary for the project, then pass
            that list of modules to be installed if necessary. """
        ImportSupport._install_all_packages(ImportSupport._find_all_packages())


if __name__ == "__main__":
    # find and install all required packages.
    # if packages are already installed, then they are imported easily to verify.
    ImportSupport.find_and_install_packages()
