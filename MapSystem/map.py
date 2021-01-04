from random import shuffle


class MapException(Exception):
    """ General Map exception for narrower exception handing cases. """
    def __init__(self, map_obj, msg=None):
        """ General Map exception for narrower exception handing cases. """
        if msg is None:
            # Set some default useful error message
            msg = "An error occurred with Map:"
            super(MapException, self).__init__(msg)
        self.msg = msg
        self.map_obj = map_obj


class Map:
    """ General Map type object. Contains default cell type if not specified. """
    def __init__(self, width, height, *args):
        """ Generate a generic map of particular width and height. """
        self.width = width
        self.height = height
        self.dims = (width, height)
        self.args = args
        self.map = [[args[0] if len(args) > 0 else "default"
                     for _ in range(width)] for __ in range(height)]

        self.MAP_CHARS = {
            "default": "??",
            "WALKABLE": "  ",
            "WALL": u'\u2588' * 2,
        }

        self.WALKABLE = {
            "default": True,
            "WALKABLE": True,
            "WALL": False
        }

    def __str__(self):
        """ Draw the map. """
        return "\n".join(
            ["".join(
                [self.MAP_CHARS[x] for x in line]
            ) for line in self.map]
        )

    def array_to_string(self, line):
        """ Convert a list to a line of block characters. """
        return "".join([self.MAP_CHARS[x] for x in line])

    def declare_map_char_block(self, block: str, character: str, walkable: bool = False):
        """ Declare a new entry of the map character dictionary. """
        if block in self.MAP_CHARS.keys():
            raise MapException(None, msg="Re-declaring existing map character key")

        self.MAP_CHARS[block] = character
        self.WALKABLE[block] = walkable

    def set_map_char_block(self, block: str = "", character: str = "#"):
        """ Set entry of the map character dictionary. """
        if block not in self.MAP_CHARS.keys():
            raise MapException(None, msg="Character key non-existent")

        self.MAP_CHARS[block] = character

    def draw_rect_to_map(self, character, x_location, y_location, w, h):
        """ Draw a rectangle to the map, using a specific character. """
        for i in range(x_location, x_location + w):
            self.draw_to_map(character, i, y_location)
            self.draw_to_map(character, i, y_location + h - 1)
        for i in range(y_location, y_location + h):
            self.draw_to_map(character, x_location, i)
            self.draw_to_map(character, x_location + w - 1, i)

    def fill_rect_to_map(self, character, x_location, y_location, w, h):
        """ Fill a rectangle to the map, using a specific character. """
        for i in range(x_location, x_location + w):
            for j in range(y_location, y_location + h):
                self.draw_to_map(character, i, j)

    def draw_to_map(self, character_key, x_location, y_location):
        """ Draw a cell to the map, using a specific character. """
        if list(self.MAP_CHARS.keys()).index(character_key) != -1:
            # character is in the MAP_CHARS area
            # map_obj -> Map
            # map_obj.map -> list[list[int]]

            self.map[y_location][x_location] = character_key

    def draw_sub_map(self, sub_map, x_location, y_location):
        """ Draw a portion or all of a sub-map to the map. """
        for row in range(len(sub_map.map)):
            for col in range(len(sub_map.map[row])):
                try:
                    self.map[x_location+col][y_location+row] = sub_map.map[col][row]
                except IndexError:
                    # just continue off
                    pass

    def is_walkable(self, block):
        """ Return if the map deems a particular block type to be walkable. """
        return self.WALKABLE.get(block, False)


class MazeSystem(Map):
    """ A Maze map of size width by height in terms of cells (not tiles). """
    def __init__(self, width, height, *args):
        """ Generate a map of a maze with a particular width and height in terms
            of rows and columns of the actual maze, since the map requires tiles
            to provide the walkable area. """
        super().__init__(width + 1 - (width % 2), height + 1 - (height % 2), *args)

        self.map = self._gen_maze()

    def _gen_maze(self):
        """ Generate maze using an iterative stack based approach. """
        w, h = (self.width - 1) // 2, (self.height - 1) // 2

        visited = [[False for _ in range(w)] for __ in range(h)]
        cells = [(col, row) for col in range(w) for row in range(h)]

        # push -> stack.append
        # pop ->  stack.pop
        stack = []

        # start with (0,0)

        first_cell = cells.pop(0)

        visited[first_cell[0]][first_cell[1]] = True

        stack.append(first_cell)

        map_cells = [[1 if col % 2 == 0 or row % 2 == 0 else 0
                      for col in range(self.width)] for row in range(self.height)]

        def cell_to_map(x, y):
            return 2 * x + 1, 2 * y + 1

        def average_2_tuple(x1, y1, x2, y2):
            return (x1 + x2) // 2, (y1 + y2) // 2

        def north(x, y):
            return (x - 1, y) if x > 0 else None

        def east(x, y):
            return (x, y + 1) if y < w - 1 else None

        def south(x, y):
            return (x + 1, y) if x < h - 1 else None

        def west(x, y):
            return (x, y - 1) if y > 0 else None

        while len(stack) > 0:
            current_cell = stack.pop()

            neighbours = [north(*current_cell), east(*current_cell),
                          south(*current_cell), west(*current_cell)]

            neighbours = [n for n in neighbours if n is not None]
            neighbours = [n for n in neighbours if not visited[n[0]][n[1]]]

            if len(neighbours) > 0:
                stack.append(current_cell)
                shuffle(neighbours)
                next_cell = neighbours[0]
                map_wall = average_2_tuple(*cell_to_map(*current_cell), *cell_to_map(*next_cell))
                map_cells[map_wall[0]][map_wall[1]] = 0
                visited[next_cell[0]][next_cell[1]] = True
                stack.append(next_cell)

        return [
            [["WALKABLE", "WALL"][x]
             for x in line] for line in map_cells
        ]
