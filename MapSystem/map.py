from random import randrange, shuffle
import sys


class RecursionLimit:
    """ Set the recursion limit higher if need be.
        If set too high, errors at the C level could occur """
    def __init__(self, limit):
        """ set limit and remember old limit (typically 1000) """
        self.limit = limit
        self.old_limit = sys.getrecursionlimit()

    def __enter__(self):
        """ Set limit to new value """
        sys.setrecursionlimit(self.limit)

    def __exit__(self, _type, value, tb):
        """ Set limit to what it was prior to entering as context """
        sys.setrecursionlimit(self.old_limit)


MAP_TYPE_BLANK = "map_type_blank"
MAP_TYPE_MAZE = "map_type_maze"
MAP_TYPE_OTHER = "map_type_other"

MAP_CHARS = {
    "default": "?",
    "MAP_CHAR_BLOCK_WALKABLE": " ",
    "MAP_CHAR_BLOCK_WALL": "#",
}


def set_map_char_block(block: str = "", character: str = "#"):
    """ Set entry of MAP_CHARS """
    global MAP_CHARS

    if block not in MAP_CHARS.keys():
        raise MapException(None, msg="Color key non-existent")

    MAP_CHARS[block] = character


class MapException(Exception):
    """ General Map exception for narrower exception handing cases """
    def __init__(self, map_obj, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occurred with Map:"
            super(MapException, self).__init__(msg)
        self.msg = msg
        self.map_obj = map_obj


class Map:
    """ General Map type object """
    def __init__(self, width, height, *args):
        self.width = width
        self.height = height
        self.dims = (width, height)
        self.args = args
        self.map = None

    def __str__(self):
        """ Draw the map """
        return "\n".join(
            ["".join(
                [MAP_CHARS[x] * 2 for x in line]
            ) for line in self.map]
        )


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
        """ Generate maze with a recursion limit rl """
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

        return [
            [["MAP_CHAR_BLOCK_WALKABLE", "MAP_CHAR_BLOCK_WALL"][int(x)]
             for x in line] for line in s.split("\n")
        ]


class BlankSystem(Map):
    """ Represents a blank map, fully customizable """
    def __init__(self, width, height, *args):
        """ Create a blank map """
        super().__init__(width, height, *args)
        self.map = [[args[0] if len(args) > 0 else "default"
                     for _ in range(width)] for __ in range(height)]

    @classmethod
    def draw_rect_to_map(cls, map_obj, character, x_location, y_location, w, h):
        """ draw a rectangle to the map, using a specific character """
        # TODO: make fill rect method
        for i in range(x_location, x_location + w):
            cls.draw_to_map(map_obj, character, i, y_location)
            cls.draw_to_map(map_obj, character, i, y_location + h - 1)
        for i in range(y_location, y_location + h):
            cls.draw_to_map(map_obj, character, x_location, i)
            cls.draw_to_map(map_obj, character, x_location + w - 1, i)

    @classmethod
    def draw_to_map(cls, map_obj, character_key, x_location, y_location):
        """ draw a cell to the map, using a specific character """
        if list(MAP_CHARS.keys()).index(character_key) != -1:
            # character is in the MAP_CHARS area
            # map_obj -> Map
            # map_obj.map -> list[list[int]]

            map_obj.map[x_location][y_location] = character_key

    @classmethod
    def draw_sub_map(cls, map_obj, sub_map, x_location, y_location):
        """ draw a portion or all of a sub-map to the map """
        for row in range(len(sub_map.map)):
            for col in range(len(sub_map.map[row])):
                try:
                    map_obj.map[x_location+col][y_location+row] = sub_map.map[col][row]
                except IndexError:
                    # just continue off
                    pass


if __name__ == "__main__":
    # TODO: Make classes more object oriented and encapsulated.
    k = 10
    maze_map = MazeSystem(k, k)
    print(maze_map)
