""" Create a JSON pickler designed specifically for GameTools classes. """
import os
import json
import importlib
import inspect
import sys


class JSONEncodable:
    """ If a class inherits from JSONEncodable, then they can be JSON serialized. """
    def json_encode(self) -> dict:
        """ Encode object into JSON serializable dictionary. """
        return {}

    @classmethod
    def json_decode(cls, obj_json):
        """ Decode JSON serializable dictionary into object. """
        pass


class JSONEncoder(json.JSONEncoder):
    """ JSONEncoder with support for GameTools defined classes. """
    def default(self, it):
        super_classes = it.__class__.__mro__
        super_classes = [
            s.__name__ for s in super_classes
        ]
        if "JSONEncodable" in super_classes:
            it: JSONEncodable
            json_encoding = {"__class_name__": it.__class__.__name__, "JSONEncodable": True}
            json_encoding.update(it.json_encode())

            return json_encoding
        else:
            return super().default(it)


class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=JSONDecoder.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(dct):
        """ Convert dictionary from JSON decode into object of type defined in GameTools. """
        if "JSONEncodable" in dct.keys():
            class_name = dct['__class_name__']

            working_dir = os.sep.join(os.getcwd().split(os.sep)[:-1]) + os.sep

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
                for file in os.listdir(working_dir + folder):
                    if not file.endswith("__init__.py") and file.endswith(".py"):
                        file_path = folder + os.sep + file
                        module_path = folder + "." + file[:-3]

                        list_of_names.append(module_path)
                        importlib.import_module(module_path, file_path)

            list_of_names.sort()

            for module in list_of_names:
                current_module = sys.modules[module]

                class_members = inspect.getmembers(current_module, inspect.isclass)
                class_members = [m for m in class_members if m[1].__module__ == module]

                for klass in class_members:
                    name, cls_obj = klass

                    if name == class_name:
                        return cls_obj.json_decode(dct)
            return dct
        else:
            return dct


if __name__ == '__main__':
    import InventorySystem.inventory as inventory

    shield_cat = inventory.ItemCategory(name="Shields")
    weapons_cat = inventory.ItemCategory(name="Weapons")
    food_cat = inventory.ItemCategory(name="Food")

    filters = inventory.ItemFilter.generate_filters([[shield_cat], [weapons_cat], [food_cat]])

    inv_sys_objs = [
        inventory.InventorySystem(item_filter=filter)
        for filter in filters
    ]

    inv = inventory.Inventory(pages=inv_sys_objs)

    inv += inventory.Item("Bow", quantity=3, stack_limit=1, category=weapons_cat)
    inv += inventory.Item("Sword", quantity=2, stack_limit=1, category=weapons_cat)
    inv += inventory.Item("Shield", quantity=2, stack_limit=1, category=shield_cat)
    inv += inventory.Item("Apples", quantity=59, category=food_cat)

    pickled_obj = inv

    freeze = json.dumps(pickled_obj, cls=JSONEncoder, indent=2)
    print(freeze)
    thawed = json.loads(freeze, cls=JSONDecoder)

    #/print("Freeze thawed correctly:", pickled_obj == thawed)

    #print(thawed)