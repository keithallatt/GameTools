from __future__ import annotations
import _curses
import curses
from MapSystem.map import Map
from pynput import keyboard
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from threading import Thread
import os
import time
from typing import Callable, Union, List, Tuple

"""
If not running in Pycharm: (curses library)
 - Click 'Run' menu
 - Click 'Edit Configurations...'
 - Check 'Emulate terminal in output console'
"""


def ascii_art(text: str, font: str = "Arial.ttf", font_size: int = 15,
              x_margin: int = 0, y_margin: int = 0, x_padding: int = 1, y_padding: int = 1,
              shadow_char: str = u'\u2591', fill_char: str = u'\u2588', back_char: str = u' ',
              double_width: bool = False, trim: bool = True, shadow: Union[int, str] = 0):
    """ Draw Ascii Art of text of a particular font and font size. """

    if type(shadow) == str:
        shadow = {
            'small_lr': 0b10,
            'small_ll': 0b1000,
            'small_ul': 0b100000,
            'small_ur': 0b10000000,
            'normal_lr': 0b111,
            'normal_ll': 0b11100,
            'normal_ul': 0b1110000,
            'normal_ur': 0b11000001,
        }.get(shadow, 0)

    shadow_directions = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
    shadow_directions = [shadow_directions[i] for i in range(8) if 0 != shadow & 1 << i]

    try:
        font_object = ImageFont.truetype(font, font_size)
    except OSError:
        font_object = ImageFont.truetype(os.sep.join(['', 'Library', 'Fonts', '']) + font,
                                         font_size)

    size = font_object.getsize(text)

    if shadow:
        x_margin += 2
        y_margin += 2

    size = (size[0] + 2 * x_margin,
            size[1] + 2 * y_margin)

    # size may be too small for some fonts / letters

    img = Image.new("1", size, "black")

    draw = ImageDraw.Draw(img)
    draw.text((x_margin, y_margin), text, "white", font=font_object)

    pixels = 2 * np.array(img, dtype=np.uint8)
    pixels_copy = np.array(img, dtype=np.uint8)

    for shadow_dir in shadow_directions:
        pixels = np.maximum(pixels, np.roll(pixels_copy, shadow_dir, axis=(0, 1)))

    if trim:
        # while pixels' edges are all zeros
        while not np.any(pixels[:, 0]):
            pixels = pixels[:, 1:]
        while not np.any(pixels[:, -1]):
            pixels = pixels[:, :-1]
        while not np.any(pixels[0, :]):
            pixels = pixels[1:, :]
        while not np.any(pixels[-1, :]):
            pixels = pixels[:-1, :]

    new_w, new_h = pixels.shape
    new_w += 2 * x_padding
    new_h += 2 * y_padding

    new_pixels = np.zeros(shape=(new_w, new_h), dtype=np.uint8)

    new_pixels[x_padding: new_w - x_padding, y_padding: new_h - y_padding] = pixels

    pixels = new_pixels

    chars = np.array([back_char, shadow_char, fill_char], dtype="U1")[pixels]
    strings = chars.view('U' + str(chars.shape[1])).flatten()

    string = "\n".join(strings)

    if double_width:
        string = "\n".join(["".join([char * 2 for char in line]) for line in string.split("\n")])

    return string


def start_game_sys(game_queue: list):
    """ Start the game system with the given list. """
    GameSysIO.game_queue = game_queue
    GameSysIO.running = True
    game_thread = Thread(target=GameSysIO.game_timer)
    game_thread.start()


class Render:
    class RenderException(Exception):
        def __init__(self, msg=None):
            """ Basic exception for errors raised by the render layer system. """
            if msg is None:
                msg = "An error occurred with Inventory"
                super(Render.RenderException, self).__init__(msg)
            self.msg = msg

    class Layer:
        """ Create a render layer for curses. """
        def __init__(self, window: Tuple[int, int, int, int] = (0, 0, None, None),
                     cell_dims: Tuple[int, int] = (2, 1), render_super_layer: Render.Layer = None):
            """ Create a render layer with (x,y)-offset and a screen dimension. """
            self.x_offset, self.y_offset, self.width, self.height = window
            self.cell_width, self.cell_height = cell_dims
            self.console = render_super_layer
            if self.console is None:
                self.console = Render.BaseLayer((0, 0, window[2], window[3]), cell_dims)
    
        def addstr(self, row, col, text):
            display_text = text
            if self.width is not None:
                max_text_length = self.width * self.cell_width - col
    
                display_text = text[: max_text_length]

            if self.height is None or row < self.height:
                self.console.addstr(self.y_offset * self.cell_height + row,
                                    self.x_offset * self.cell_width + col,
                                    display_text)
    
        def erase(self):
            self.console.erase()
    
        def refresh(self):
            self.console.refresh()

    class BaseLayer(Layer):
        """ Create a base render layer for curses. """
        def __init__(self, window: Tuple[int, int, int, int] = (0, 0, None, None),
                     cell_dims: Tuple[int, int] = (2, 1)):
            """ Create a render layer with (x,y)-offset and a screen dimension. """
            super().__init__(window, cell_dims, self)
            self.console = curses.initscr()  # initialize is our playground
            curses.curs_set(0)
    
        def addstr(self, row, col, text):
            display_text = text
            if self.width is not None:
                max_text_length = self.width * self.cell_width - col
    
                display_text = text[: max_text_length]
    
                pass
    
            if self.height is None or row < self.height:
                self.console.addstr(self.y_offset * self.cell_height + row,
                                    self.x_offset * self.cell_width + col,
                                    display_text)
    
        def erase(self):
            self.console.erase()
    
        def refresh(self):
            self.console.refresh()

    class Border(Layer):
        """ Creates a render layer with a border """
        def __init__(self, window: Tuple[int, int, int, int] = (0, 0, None, None),
                     cell_dims: Tuple[int, int] = (2, 1), render_super_layer: Render.Layer = None,
                     **kwargs):
            if None in window and render_super_layer is None:
                raise Render.RenderException("Cannot border unbounded render layer.")

            width, height = window[2], window[3]

            render_border = Render.Layer(window=(0, 0, width, height),
                                         cell_dims=cell_dims,
                                         render_super_layer=render_super_layer)
            render_super = Render.Layer(window=(1, 1, width-1, height-1),
                                        cell_dims=cell_dims,
                                        render_super_layer=render_border)
            super().__init__(window, cell_dims, render_super)
            # border faces
            self.border_tf = kwargs.get("border_tf", kwargs.get("top", "\u2500\u2500"))
            self.border_lf = kwargs.get("border_lf", kwargs.get("left", "\u2502 "))
            self.border_rf = kwargs.get("border_rf", kwargs.get("right", " \u2502"))
            self.border_bf = kwargs.get("border_bf", kwargs.get("bottom", "\u2500\u2500"))
            # border corners.
            self.border_tl = kwargs.get("border_tl",
                                        kwargs.get("top", kwargs.get("left", "\u250C\u2500")))
            self.border_bl = kwargs.get("border_bl",
                                        kwargs.get("bottom", kwargs.get("left",  "\u2514\u2500")))
            self.border_tr = kwargs.get("border_tr",
                                        kwargs.get("top", kwargs.get("right", "\u2500\u2510")))
            self.border_br = kwargs.get("border_br",
                                        kwargs.get("bottom", kwargs.get("right", "\u2500\u2518")))

        def refresh(self):
            self.console.console.addstr(0, 0, self.border_tl + self.border_tf * (self.width - 2) +
                                        self.border_tr)

            for i in range(self.height - 2):
                self.console.console.addstr(i+1, 0, self.border_lf)
                self.console.console.addstr(i+1, (self.width-1) * self.cell_width, self.border_rf)

            self.console.console.addstr((self.height - 1) * self.cell_height, 0, self.border_bl +
                                        self.border_bf * (self.width - 2) + self.border_br)

            self.console.refresh()

        @staticmethod
        def from_map_io(map_io: MapIO, **kwargs):
            """ Return the render layer object to create a border for the map system. """
            if type(map_io) == ScrollingMapIO:
                map_io: ScrollingMapIO
                window = map_io.window_size
            else:
                window = map_io.map_dims

            window = (0, 0, int(window[0]), int(window[1]))

            cell_dims = np.array(
                [list(line) for line in map_io.main_map.MAP_CHARS['default'].split("\n")],
                dtype=np.unicode).T.shape

            render_layer = Render.Border(window=window,
                                         cell_dims=cell_dims,
                                         **kwargs)

            return render_layer


class GameTrigger:
    """ A collection of Game system triggers. """
    class _GameSysTrigger:
        """ Game system trigger object, used for classifying different triggers. """
        def __init__(self, target, trigger: Callable):
            """ Create a generic trigger with a target and trigger. """
            self.target = target
            self.trigger = trigger

        def handle(self, game_sys: GameSysIO):
            """ Handle the trigger, including checking to see if the trigger callable
                returns a true value. """
            pass

    class GameSysChangeTrigger(_GameSysTrigger):
        """ Trigger for changing game systems, such as from title screen to main game, or
            to and from a pause menu. """
        def __init__(self, target: Union[List[GameSysIO], GameSysIO],
                     trigger: Callable, transient: bool = False, append: bool = False):
            """ Create a game system change trigger. """
            super().__init__(target, trigger)
            self.transient = transient
            self.append = append

        def handle(self, game_sys: GameSysIO):
            """ Handle the trigger and change the system if need be. """
            try:
                trigger_value = self.trigger(game_sys)
                if trigger_value and type(trigger_value) == bool:
                    if self.append:
                        if type(self.target) == list:
                            GameSysIO.game_queue += self.target[::]
                        else:
                            GameSysIO.game_queue.append(self.target)
                    else:
                        if type(self.target) == list:
                            GameSysIO.game_queue = self.target[::]
                        else:
                            GameSysIO.game_queue = [self.target]

                    if self.transient:
                        GameSysIO.game_queue.append(game_sys)

                    game_sys.render.erase()
                    game_sys.render.refresh()
                    curses.endwin()
                    return False
            except AttributeError:
                # attribute error occurs if lambda is not the trigger for the
                # right type of game system.
                pass

    class MapSysRelocationTrigger(_GameSysTrigger):
        """ Trigger for changing locations within the same map. """
        def __init__(self, map_obj: MapIO, trip_location: Tuple[int, int],
                     destination: Tuple[int, int]):
            """ Create a relocation trigger. """
            def trigger(map_object):
                return (map_object.x_loc, map_object.y_loc) == trip_location and map_obj.moved

            super().__init__(map_obj, trigger)

            self.trip_location = trip_location
            self.destination = destination

        def handle(self, game_sys: GameSysIO):
            """ Handle the trigger and relocate the player. """
            try:
                trigger_value = self.trigger(game_sys)
                if trigger_value and type(trigger_value) == bool:
                    self.target.x_loc, self.target.y_loc = self.destination

                    # redraw character.
                    game_sys.render.erase()
                    game_sys.draw_init()
                    game_sys.render.refresh()

                    return True
            except AttributeError:
                # attribute error occurs if lambda is not the trigger for the
                # right type of game system.
                pass

    class KeyBindingTrigger(_GameSysTrigger):
        """ Trigger that when added, maps a key to an action. """
        def __init__(self, target: GameTrigger._GameSysTrigger, key: keyboard.Key):
            """ Create a key binding trigger. """
            old_trigger = target.trigger

            def trigger(game_sys: GameSysIO):
                """ If key in game_sys.key_presses, then the key is pressed """
                return key in game_sys.key_presses or old_trigger(game_sys)
            super().__init__(target, trigger)
            self.target.trigger = trigger

        def handle(self, game_sys: GameSysIO):
            return self.target.handle(game_sys)


class GameSysIO:
    """ General IO for game system. """
    def __init__(self, render: Render.Layer = None):
        """ Initialize curses and hide the cursor. The methods of this
            new instantiated object are those that the key listener events
            will be passed to. """
        self.render = Render.BaseLayer() if render is None else render
        self.exception = None
        self.exit_code = None
        self.triggers = []
        self.key_presses = set()

    game_queue = []

    def on_press(self, key: keyboard.Key):
        """ On a key press, how to handle the rising edge (press). """
        self.key_presses.add(key)

    def on_release(self, key: keyboard.Key):
        """ On a key press, how to handle the falling edge (release). """
        pass

    def draw_init(self):
        """ Draw the initial display / console. This will be called at the
            end of the initialization of the new GameSysIO object to start
             the system with something displayed on the console. """
        pass

    def restart(self):
        """ Restart an ended GameSysIO object after control was given to a
            new object. This could be for pausing purposes, or as a saved
            state. """
        self.render.erase()
        self.draw_init()
        self.render.addstr(0, 0, "Loading... ")
        self.render.refresh()

        with keyboard.Listener(on_press=self.on_press,
                               on_release=self.on_release,
                               suppress=True) as listener:
            self.render.erase()
            self.draw_init()
            self.render.refresh()

            listener.join()

    def check_triggers(self):
        """ Check all triggers, if any triggers give true, then add the new game system. """
        for trigger_obj in self.triggers:
            return_value = trigger_obj.handle(self)
            if return_value is not None:
                if not return_value:
                    # return value is exactly False.
                    self.key_presses = set()
                    return False
                self.key_presses = set()
                return True

    def link_sys_change(self, target: Union[List[GameSysIO], GameSysIO], trigger: Callable,
                        transient: bool = False, append: bool = False,
                        key_binding: Union[str, keyboard.Key, keyboard.KeyCode] = None):
        """ When the trigger is set, change to other, transient being if self is set as a
            return point. Set a key binding if specified. """
        sys_change_trigger = GameTrigger.GameSysChangeTrigger(target, trigger, transient, append)

        if key_binding is not None:
            if type(key_binding) == str:
                # take first character in case the string is multiple characters
                key_binding = keyboard.KeyCode.from_char(key_binding[0])
            key_trigger = GameTrigger.KeyBindingTrigger(sys_change_trigger, key_binding)
            self.triggers.append(key_trigger)

        self.triggers.append(sys_change_trigger)

    @staticmethod
    def game_timer():
        """ The main game loop. This function is what drives event handling. As GameSysIO objects
            load additional systems in, they pause themselves, allowing themselves to be removed
            from the queue and allow the next system control. """
        while True:
            if len(GameSysIO.game_queue) > 0:
                next_sys = GameSysIO.game_queue.pop(0)
                if type(next_sys) == tuple:
                    next_sys, args = next_sys
                    next_game_sys = next_sys(*args)
                    next_game_sys.restart()
                else:
                    next_sys.restart()
            else:
                exit(0)


class MenuSysIO(GameSysIO):
    """ Initialize a title screen / menu screen IO system.
        Displays ascii art of the game title or particular menu. """
    def __init__(self, title: str, option_choices: list[str] = None, option_choice: int = 0,
                 font_size: int = 15, render: Render.Layer = None):
        """ Create a title screen or menu. """
        super().__init__(render=render)

        if title is not None and len(title.strip()) != 0:
            self.art = ascii_art(title,
                                 shadow='small_lr',
                                 font_size=font_size,
                                 x_margin=5,
                                 y_margin=5)
        else:
            self.art = ""

        self.option_choices = [
            "Start", "Quit"
        ]
        if option_choices is not None:
            self.option_choices = option_choices
        self.option_choice = min(len(self.option_choices)-1, max(0, option_choice))

        self.board = str(self.art).split("\n")

        self.chosen = False
        self.chosen_option = None

    def draw_init(self):
        """ Draw the menu with the default option selected. """
        self.render.erase()

        for i in range(len(self.board)):
            self.render.addstr(i, 0, self.board[i])

        for i in range(len(self.option_choices)):
            self.render.addstr(len(self.board)+2+i, 3, self.option_choices[i])

        self.render.addstr(len(self.board)+2, 1, ">")

        self.render.refresh()

    def on_press(self, key: keyboard.Key):
        """ Check if the user is choosing a new option (up / down arrow keys). """
        super().on_press(key)
        try:
            self.render.addstr(len(self.board)+2+self.option_choice, 1, " ")

            if key == keyboard.Key.up:
                self.option_choice = max(self.option_choice-1, 0)
            if key == keyboard.Key.down:
                self.option_choice = min(self.option_choice+1, len(self.option_choices) - 1)

            if key == keyboard.Key.enter:
                self.chosen_option = self.option_choices[self.option_choice]

            self.render.addstr(len(self.board)+2+self.option_choice, 1, ">")
            self.render.refresh()

            return self.check_triggers()
        except _curses.error:
            self.render.erase()
            self.render.refresh()
            curses.endwin()
            return False

    def on_release(self, key: keyboard.Key):
        """ Check what option the user choose. """
        self.chosen = False
        option_same = self.chosen_option == self.option_choices[self.option_choice]
        if key == keyboard.Key.enter and option_same:
            self.chosen = True

        return self.check_triggers()


class MapIO(GameSysIO):
    """ Create the IO system for a general map. This will be used for general walking around. """
    def __init__(self, main_map: Map, location: Tuple[int, int], render: Render.Layer = None):
        """ Generate a walkable area map for the user to walk around.
            Default location is provided by the x_loc and y_loc variables. """
        super().__init__(render=render)

        self.main_map = main_map
        self.map_dims = main_map.dims
        self.x_max, self.y_max = main_map.dims

        # this can be more streamlined but it's enough for demonstration purposes...
        self.render.erase()
        self.x_loc, self.y_loc = location
        self.pause = False
        self.char = "P1"
        self.refresh_on_key_press = False
        self.moved = False

    def draw_init(self):
        """ Draw the map and current location of the player. """
        self.render.erase()

        board = str(self.main_map).split("\n")

        for i in range(len(board)):
            self.render.addstr(i, 0, board[i])

        self.render.addstr(self.y_loc, self.x_loc * 2, self.char)
        self.render.refresh()

    def on_press(self, key: keyboard.Key):
        """ Check to see if the user is moving (arrow keys), or pausing ('p'). """
        super().on_press(key)
        try:
            # Moving check
            new_x, new_y = self.x_loc, self.y_loc

            if not self.refresh_on_key_press:
                # if updating a static map (MapIO, not ScrollingMapIO)
                self.render.addstr(self.y_loc, self.x_loc * 2,
                                   self.main_map.MAP_CHARS[self.main_map.map[new_y][new_x]])

            old_char = self.char

            if key == keyboard.Key.left:
                new_x -= 1
                self.char = "<<"
            if key == keyboard.Key.right:
                new_x += 1
                self.char = ">>"
            if key == keyboard.Key.up:
                new_y -= 1
                self.char = "^^"
            if key == keyboard.Key.down:
                new_y += 1
                self.char = "vv"

            # bound checking
            new_x = self.x_max - 1 if new_x >= self.x_max else 0 if new_x < 0 else new_x
            new_y = self.y_max - 1 if new_y >= self.y_max else 0 if new_y < 0 else new_y

            self.moved = (self.char != old_char)
            if self.main_map.is_walkable(self.main_map.map[new_y][new_x]):
                if (self.x_loc, self.y_loc) != (new_x, new_y):
                    self.x_loc, self.y_loc = new_x, new_y
                    self.moved = True

            if not self.refresh_on_key_press:
                # if updating a static map (MapIO, not ScrollingMapIO)
                self.render.addstr(self.y_loc, self.x_loc * 2, self.char)
                self.render.refresh()

            if self.moved:
                if self.refresh_on_key_press:
                    self.draw_init()

            return self.check_triggers()
        except _curses.error:
            self.render.erase()
            self.render.refresh()
            curses.endwin()
            return False

    def link_relocation(self, trip_location: Tuple[int, int], destination: Tuple[int, int]):
        """ Add a trigger to teleport the user from one location on map to another. """
        def mod_location(x, y, w, h):
            return x % w, y % h

        self.triggers.append(
            GameTrigger.MapSysRelocationTrigger(self,
                                                mod_location(*trip_location, *self.map_dims),
                                                mod_location(*destination, *self.map_dims)))

        self.main_map.draw_to_map("PORTAL", *mod_location(*trip_location, *self.map_dims))
        self.main_map.draw_to_map("PORTAL", *mod_location(*destination, *self.map_dims))

    def link_relocation_cycle(self, *locations):
        """ Create a cycle of teleportation points, where each point will lead to the next in the
            list of locations. """
        for i in range(len(locations)):
            self.link_relocation(locations[i-1], locations[i])


class ScrollingMapIO(MapIO):
    """ MapIO object that scrolls within a specified window. """
    def __init__(self, main_map: Map, location: Tuple[int, int], window: Tuple[int, int],
                 render: Render.Layer = None):
        """ Create a scrolling map to interact with. """
        super().__init__(main_map, location, render=render)
        self.window_size = window
        self.refresh_on_key_press = True

    def draw_init(self):
        """ Draw the visible window of the map with the player as centered as possible. """
        # width and height of window
        w_window, h_window = self.window_size
        # top left corner location
        x_window, y_window = self.x_loc - w_window // 2, self.y_loc - h_window // 2
        # bottom right corner location
        ox_window, oy_window = x_window + w_window, y_window + h_window

        while ox_window > self.x_max:
            x_window -= 1
            ox_window -= 1
        while oy_window > self.y_max:
            y_window -= 1
            oy_window -= 1
        while x_window < 0:
            x_window += 1
            ox_window += 1
        while y_window < 0:
            y_window += 1
            oy_window += 1

        np_map = np.array(self.main_map.map, dtype=np.unicode)

        np_map = np_map[y_window:oy_window, x_window:ox_window]

        self.render.erase()

        for line in range(len(np_map)):
            self.render.addstr(line, 0, self.main_map.array_to_string(np_map[line]))

        self.render.addstr(self.y_loc - y_window, (self.x_loc - x_window) * 2, self.char)
        self.render.refresh()
