from __future__ import annotations
import _curses
import curses
from MapSystem.map import Map, MazeSystem
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


def ascii_art(text: str, font: str = "Arial.ttf", font_size: int = 15, x_margin: int = 0,
              y_margin: int = 0, shadow_char: str = u'\u2591', fill_char: str = u'\u2588',
              double_width: bool = False, trim: bool = False, shadow: bool = False,
              full_shadow: bool = False):
    """ Draw Ascii Art of text of a particular font and font size. """
    if full_shadow:
        shadow = True

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

    pixels = np.array(img, dtype=np.uint8)

    if shadow:
        shadow_pixels_diagonal = np.roll(pixels, (1, 1), axis=(0, 1))
        shadow_pixels_top = shadow_pixels_diagonal
        shadow_pixels_bottom = shadow_pixels_diagonal
        if full_shadow:
            shadow_pixels_top = np.roll(pixels, (1, 0), axis=(0, 1))
            shadow_pixels_bottom = np.roll(pixels, (0, 1), axis=(0, 1))

        pixels = 2*pixels
        pixels = np.maximum(pixels, shadow_pixels_diagonal)
        pixels = np.maximum(pixels, shadow_pixels_top)
        pixels = np.maximum(pixels, shadow_pixels_bottom)
    else:
        pixels = 2 * pixels

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

    chars = np.array([' ', shadow_char, fill_char], dtype="U1")[pixels]
    strings = chars.view('U' + str(chars.shape[1])).flatten()

    string = "\n".join(strings)

    if double_width:
        string = string.replace(" ", "  ")
        string = string.replace(fill_char, 2 * fill_char)
        string = string.replace(shadow_char, 2 * shadow_char)

    return string


def start_game_sys(game_queue: list):
    """ Start the game system with the given list. """
    GameSysIO.game_queue = game_queue
    GameSysIO.running = True
    game_thread = Thread(target=GameSysIO.game_timer)
    game_thread.start()


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

                    game_sys.console.erase()
                    game_sys.console.refresh()
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
                    game_sys.console.erase()
                    game_sys.draw_init()
                    game_sys.console.refresh()

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
    def __init__(self):
        """ Initialize curses and hide the cursor. The methods of this
            new instantiated object are those that the key listener events
            will be passed to. """
        self.console = curses.initscr()  # initialize is our playground
        curses.curs_set(0)
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
        self.console.erase()
        self.draw_init()
        self.console.addstr(0, 0, "Loading... ")
        self.console.refresh()

        with keyboard.Listener(on_press=self.on_press,
                               on_release=self.on_release,
                               suppress=True) as listener:
            time.sleep(0.1)
            self.console.erase()
            self.draw_init()
            self.console.refresh()

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
            return point. Set a key binding if specified """
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


class TitleSysIO(GameSysIO):
    """ Initialize a title screen IO system. Displays ascii art of the
        game title or particular menu. """
    def __init__(self, title: str, option_choices: list[str] = None, option_choice: int = 0,
                 font_size: int = 15):
        """ Create a title screen or menu. """
        super().__init__()

        self.art = ascii_art(title, shadow=True, font_size=font_size)

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
        self.console.erase()

        for i in range(len(self.board)):
            self.console.addstr(i, 0, self.board[i])

        for i in range(len(self.option_choices)):
            self.console.addstr(len(self.board)+2+i, 3, self.option_choices[i])
        self.console.addstr(len(self.board)+2, 1, ">")

        self.console.refresh()

    def on_press(self, key: keyboard.Key):
        """ Check if the user is choosing a new option (up / down arrow keys). """
        super().on_press(key)
        try:
            self.console.addstr(len(self.board)+2+self.option_choice, 1, " ")

            if key == keyboard.Key.up:
                self.option_choice = max(self.option_choice-1, 0)
            if key == keyboard.Key.down:
                self.option_choice = min(self.option_choice+1, len(self.option_choices) - 1)

            if key == keyboard.Key.enter:
                self.chosen_option = self.option_choices[self.option_choice]

            self.console.addstr(len(self.board)+2+self.option_choice, 1, ">")
            self.console.refresh()

            return self.check_triggers()
        except _curses.error:
            self.console.erase()
            self.console.refresh()
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
    def __init__(self, main_map: Map, location: Tuple[int, int]):
        """ Generate a walkable area map for the user to walk around.
            Default location is provided by the x_loc and y_loc variables. """
        super().__init__()

        self.main_map = main_map
        self.map_dims = main_map.dims
        self.x_max, self.y_max = main_map.dims

        # this can be more streamlined but it's enough for demonstration purposes...
        self.console.erase()
        self.x_loc, self.y_loc = location
        self.pause = False
        self.char = "P1"
        self.refresh_on_key_press = False
        self.moved = False

    def draw_init(self):
        """ Draw the map and current location of the player. """
        self.console.erase()

        board = str(self.main_map).split("\n")

        for i in range(len(board)):
            self.console.addstr(i, 0, board[i])

        self.console.addstr(self.y_loc, self.x_loc * 2, self.char)
        self.console.refresh()

    def on_press(self, key: keyboard.Key):
        """ Check to see if the user is moving (arrow keys), or pausing ('p'). """
        super().on_press(key)
        try:
            # Moving check
            new_x, new_y = self.x_loc, self.y_loc

            if not self.refresh_on_key_press:
                # if updating a static map (MapIO, not ScrollingMapIO)
                self.console.addstr(self.y_loc, self.x_loc * 2,
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
                self.console.addstr(self.y_loc, self.x_loc * 2, self.char)
                self.console.refresh()

            if self.moved:
                if self.refresh_on_key_press:
                    self.draw_init()

            return self.check_triggers()
        except _curses.error:
            self.console.erase()
            self.console.refresh()
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
    def __init__(self, main_map: Map, location: Tuple[int, int], window: Tuple[int, int]):
        """ Create a scrolling map to interact with. """
        super().__init__(main_map, location)
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

        while x_window < 0:
            x_window += 1
            ox_window += 1
        while y_window < 0:
            y_window += 1
            oy_window += 1
        while ox_window > self.x_max:
            x_window -= 1
            ox_window -= 1
        while oy_window > self.y_max:
            y_window -= 1
            oy_window -= 1

        np_map = np.array(self.main_map.map, dtype=np.unicode)

        np_map = np_map[y_window:oy_window, x_window:ox_window]

        self.console.erase()

        for line in range(len(np_map)):
            self.console.addstr(line, 0, self.main_map.array_to_string(np_map[line]))

        self.console.addstr(self.y_loc - y_window, (self.x_loc - x_window) * 2, self.char)
        self.console.refresh()


if __name__ == "__main__":
    main_title = TitleSysIO(title="Game", option_choices=["Start", "Quit"])
    pause_title = TitleSysIO(title="Pause", option_choices=["Continue", "Return to menu"],
                             font_size=12)

    map_system = MazeSystem(51, 51)
    map_system.declare_map_char_block("PORTAL", "[]", walkable=True)

    map_sys = ScrollingMapIO(map_system, (1, 1), (21, 21))

    main_title.link_sys_change(
        [], lambda x: x.chosen and x.chosen_option == "Quit",
        key_binding='q'
    )

    main_title.link_sys_change([map_sys], lambda x: x.chosen and x.chosen_option == "Start")

    pause_title.link_sys_change([main_title],
                                lambda x: x.chosen and x.chosen_option == "Return to menu")
    pause_title.link_sys_change([map_sys], lambda x: x.chosen and x.chosen_option == "Continue")

    map_sys.link_sys_change([pause_title], lambda x: False, transient=True, key_binding='p')
    map_sys.link_relocation((-2, -2), (1, 1))

    start_game_sys([main_title])
