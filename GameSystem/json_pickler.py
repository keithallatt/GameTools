""" Create a JSON pickler designed specifically for GameTools classes. """
import json


class JSONEncodable:
    """  """
    def json_encode(self) -> dict:
        return {}

    def json_decode(self, obj_json):
        pass


class JSONEncoder(json.JSONEncoder):
    def default(self, it):
        super_classes = it.__class__.__mro__
        super_classes = [
            s.__name__ for s in super_classes
        ]
        if "JSONEncodable" in super_classes:
            it: JSONEncodable
            json_encoding = {"__class_name__": it.__class__.__name__}
            json_encoding.update(it.json_encode())

            return json_encoding
        else:
            return super().default(it)


class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        return super().object_hook(dct)


if __name__ == '__main__':
    from InventorySystem.inventory import *
    from InventorySystem.currency import *
    it_cat = ItemCategory("Foo Category")
    foo = Item("Foo", category=it_cat)
    bar = Item("Bar", category=it_cat)
    baz = Item("Baz", category=it_cat)
    it_fil = ItemFilter({it_cat: True})

    inv_sys = InventorySystem(item_filter=it_fil)

    inv = Inventory(pages=[inv_sys])

    inv += foo * 2
    inv += bar * 3
    inv += baz * 2

    indent_level = 4

    print(json.dumps(inv, cls=JSONEncoder, indent=indent_level))
