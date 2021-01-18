from __future__ import annotations
from typing import Union
from copy import deepcopy
"""
Inspired by:
https://www.youtube.com/watch?v=jde1Jq5dF0E

PROTOTYPE
@author: Keith Allatt
@version: Jan 16 2021
"""


class MenuSystemPage:
    def __init__(self):
        self.dict = {}

    def __add__(self, other: str):
        """ Makes MenuSystemPage's mutable. """
        if other not in self.dict.keys():
            self.dict[other] = MenuSystemPage()

        return self

    def __getitem__(self, item: Union[str, tuple]):
        if type(item) == str:
            if item not in self.dict.keys():
                self.dict.update({item: MenuSystemPage()})
            return self.dict[item]
        if len(item) == 0:
            raise Exception("Get on empty list")
        if len(item) == 1:
            return self.dict[item[0]]
        return self.dict[item[0]][item[1:]]

    def __setitem__(self, key: Union[str, tuple], value: Union[MenuSystemPage, str]):
        if type(key) == str:
            if type(value) == str:
                self.dict = self.__add__(value).dict
            elif type(value) == MenuSystemPage:
                self.dict[key] = value
        elif len(key) == 0:
            raise Exception("Get on empty list")
        elif len(key) == 1:
            value.super_menu = self
            self[key[0]] = value
        else:
            self[key[0]][key[1:]] = value

    def __str__(self):
        return "{"+", ".join(
            [f"{k}: {str(v)}" if v.dict != {} else f"{k}" for k, v in self.dict.items()])+"}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class BasicInputMenuSystemNavigator:
    def __init__(self, menu):
        self.menu = menu
        self.menu_path = ()

    def get_current(self):
        if self.menu_path != ():
            return self.menu[self.menu_path]
        else:
            return self.menu

    def see(self):
        print(list(self.get_current().dict.keys()))

    def choose(self, string):
        if string in self.get_current().dict.keys():
            if self.get_current().dict[string].dict == {}:
                print(f"Called: <{string}>")
            else:
                self.menu_path += (string,)

    def back_level(self):
        if self.menu_path != ():
            self.menu_path = self.menu_path[:-1]


if __name__ == '__main__':
    menu_sys = MenuSystemPage()
    menu_sys += "Menu1"
    menu_sys["Menu2"]["Menu2.1"]["Menu2.1.1"]["new"] += "MenuSysABC"

    print(menu_sys)

    basic = BasicInputMenuSystemNavigator(menu_sys)

    basic.see()
    # new walrus operator!
    while (input_text := input("> ")) != "quit":
        if input_text == "..":
            basic.back_level()
        elif input_text != ".":
            basic.choose(input_text)
        basic.see()
