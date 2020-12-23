from colorama import Fore, Back, Style, init
from random import randrange, shuffle
import sys


class RecursionLimit:
    def __init__(self, limit):
        self.limit = limit
        self.old_limit = sys.getrecursionlimit()

    def __enter__(self):
        sys.setrecursionlimit(self.limit)

    def __exit__(self, type, value, tb):
        sys.setrecursionlimit(self.old_limit)

init()

MAP_TYPE_BLANK = "map_type_blank"
MAP_TYPE_MAZE = "map_type_maze"
MAP_TYPE_OTHER = "map_type_other"

MAP_CHARS = {
    "default":
        " ",
    "MAP_CHAR_BLOCK_WALKABLE":
        " ",
    "MAP_CHAR_BLOCK_WALL":
        Fore.LIGHTWHITE_EX + Back.LIGHTWHITE_EX + "#" + Style.RESET_ALL,
}


def set_map_char_block(block: str = "",
                       fg: Fore = Fore.LIGHTWHITE_EX,
                       bg: Back = Back.LIGHTWHITE_EX,
                       clr: str = None,
                       chr: str = "#"):
    global MAP_CHARS

    if clr is not None:
        colors = {x.split("_")[0].lower(): (getattr(Fore, x), getattr(Back, x))
                       for x in dir(Fore) if x[0] != "_" and x != "RESET"}

        fg, bg = colors.get(clr.lower(), (fg, bg))

    if block not in MAP_CHARS.keys():
        raise MapException(None, msg="Color key non-existent")

    MAP_CHARS[block] = fg + bg + chr + Style.RESET_ALL


class MapException(Exception):
    def __init__(self, map_obj, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occured with Map:"
            super(MapException, self).__init__(msg)
        self.msg = msg
        self.map_obj = map_obj


class Map:
    def __init__(self, width, height, *args):
        self.width = width
        self.height = height
        self.dims = (width, height)
        self.args = args
        self.map = None


class MazeSystem(Map):
    """ A Maze map of size :arg width / :arg height """

    def __init__(self, width, height, *args):
        super().__init__(width * 2 + 1, height * 2 + 1, *args)
        limit = 1000
        max_limit = 10000
        while limit < max_limit:
            try:
                self.map = self._gen_maze(limit)
                break
            except RecursionError:
                limit += 100
        else:
            raise MapException("Failed Initialization", msg="Hit Upper Recursion Limit of 10000.")

    def _gen_maze(self, rl=1000):
        """ Recursion Limit 5000 is min to generate 50 by 50 maze most of the time """
        w, h = self.width // 2, self.height // 2

        vis = [[0] * w + [1] for _ in range(h)] + [[1] * (w + 1)]
        ver = [
                  ["10"] * w +
                  ["1"] for _ in range(h)] + [[]]
        hor = [
            ["11"] * w +
            ["1"] for _ in range(h + 1)]

        def walk(x, y):
            vis[y][x] = 1

            d = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]
            shuffle(d)
            for (xx, yy) in d:
                if vis[yy][xx]:
                    continue
                if xx == x:
                    hor[max(y, yy)][x] = "10"
                if yy == y:
                    ver[y][max(x, xx)] = "00"
                walk(xx, yy)

        with RecursionLimit(rl):
            walk(randrange(w), randrange(h))

        s = ""
        for (a, b) in zip(hor, ver):
            s += ''.join(a + ['\n'] + b + ['\n'])

        s = s.strip()

        return [[["MAP_CHAR_BLOCK_WALKABLE", "MAP_CHAR_BLOCK_WALL"][int(x)] for x in line] for line in s.split("\n")]

    def __str__(self):
        return "\n".join(
            ["".join(
                [MAP_CHARS[x] * 2 for x in line]
            ) for line in self.map]
        )


class BlankSystem(Map):
    def __init__(self, width, height, *args):
        super().__init__(width, height, *args)
        self.map = [[args[0] if len(args) > 0 else "default"
                     for col in range(width)] for row in range(height)]

    def __str__(self):
        return "\n".join(
            ["".join(
                [MAP_CHARS[x] * 2 for x in line]
            ) for line in self.map]
        )

    @classmethod
    def draw_rect_to_map(cls, map_obj, character, xloc, yloc, w, h):
        for i in range(xloc, xloc + w):
            cls.draw_to_map(map_obj, character, i, yloc)
            cls.draw_to_map(map_obj, character, i, yloc + h - 1)
        for i in range(yloc, yloc + h):
            cls.draw_to_map(map_obj, character, xloc, i)
            cls.draw_to_map(map_obj, character, xloc + w - 1, i)

    @classmethod
    def draw_to_map(cls, map_obj, character_key, xloc, yloc):
        if list(MAP_CHARS.keys()).index(character_key) != -1:
            # character is in the MAP_CHARS area
            # map_obj -> Map
            # map_obj.map -> list[list[int]]

            map_obj.map[xloc][yloc] = character_key

    @classmethod
    def draw_sub_map(cls, map_obj, sub_map, xloc, yloc):
        for row in range(len(sub_map.map)):
            for col in range(len(sub_map.map[row])):
                try:
                    map_obj.map[xloc+col][yloc+row] = sub_map.map[col][row]
                except IndexError:
                    # just continue off
                    pass


if __name__ == "__main__":
    k = 10
    sub_map = MazeSystem(k, k)
    print(sub_map)
