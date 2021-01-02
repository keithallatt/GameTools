from __future__ import annotations
import _curses
import curses
from MapSystem.map import Map, BlankSystem
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

                    game_sys.exit_code = 0
                    game_sys.console.clear()
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
            """ Create a relocation trigger """
            def trigger(map_object):
                return (map_object.x_loc, map_object.y_loc) == trip_location

            super().__init__(map_obj, trigger)

            self.destination = destination

        def handle(self, game_sys: GameSysIO):
            """ Handle the trigger and relocate the player. """
            try:
                trigger_value = self.trigger(game_sys)
                if trigger_value and type(trigger_value) == bool:
                    self.target.x_loc, self.target.y_loc = self.destination
                    # redraw character.
                    game_sys.console.clear()
                    game_sys.draw_init()
                    game_sys.console.refresh()
            except AttributeError:
                # attribute error occurs if lambda is not the trigger for the
                # right type of game system.
                pass


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

    game_queue = []

    def on_press(self, key: keyboard.Key):
        """ On a key press, how to handle the rising edge (press) """
        pass

    def on_release(self, key: keyboard.Key):
        """ On a key press, how to handle the falling edge (release) """
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
        self.console.clear()
        self.draw_init()
        self.console.addstr(0, 0, "Loading... ")
        self.console.refresh()

        with keyboard.Listener(on_press=self.on_press,
                               on_release=self.on_release,
                               suppress=True) as listener:
            time.sleep(0.1)
            self.console.clear()
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
                    return False

    def link_sys_change(self, target: Union[List[GameSysIO], GameSysIO], trigger: Callable,
                        transient: bool = False, append: bool = False):
        """ When the trigger is set, change to other, transient being if self is set as a
            return point """
        self.triggers.append(GameTrigger.GameSysChangeTrigger(target, trigger, transient, append))

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
        """ Draw the menu with the default option selected """
        self.console.clear()

        for i in range(len(self.board)):
            self.console.addstr(i, 0, self.board[i])

        for i in range(len(self.option_choices)):
            self.console.addstr(len(self.board)+2+i, 3, self.option_choices[i])
        self.console.addstr(len(self.board)+2, 1, ">")

        self.console.refresh()

    def on_press(self, key: keyboard.Key):
        """ Check if the user is choosing a new option (up / down arrow keys) """
        try:
            self.console.addstr(len(self.board)+2+self.option_choice, 1, " ")

            if key == keyboard.Key.up:
                self.option_choice = max(self.option_choice-1, 0)
            if key == keyboard.Key.down:
                self.option_choice = min(self.option_choice+1, len(self.option_choices) - 1)

            self.console.addstr(len(self.board)+2+self.option_choice, 1, ">")

            self.console.refresh()

        except _curses.error as e:
            self.console.clear()
            curses.endwin()
            self.exception = e
            self.exit_code = 1
            return False

    def on_release(self, key: keyboard.Key):
        """ Check what option the user choose. """
        self.chosen = False
        self.chosen_option = None
        if key == keyboard.Key.enter:
            self.chosen = True
            self.chosen_option = self.option_choices[self.option_choice]
        return self.check_triggers()


class MapIO(GameSysIO):
    """ Create the IO system for a general map. This will be used for general walking around. """
    def __init__(self, main_map: Map, x_loc: int, y_loc: int):
        """ Generate a walkable area map for the user to walk around.
            Default location is provided """
        super().__init__()

        self.main_map = main_map
        self.x_max, self.y_max = main_map.dims

        # this can be more streamlined but it's enough for demonstration purposes...
        self.console.clear()

        self.x_loc = x_loc
        self.y_loc = y_loc

        self.pause = False

        self.char = "P1"

    def draw_init(self):
        """ Draw the map and initial location of the user """
        self.console.clear()

        board = str(self.main_map).split("\n")

        for i in range(len(board)):
            self.console.addstr(i, 0, board[i])

        self.console.addstr(self.y_loc, self.x_loc * 2, self.char)
        self.console.refresh()

    def on_press(self, key: keyboard.Key):
        """ Check to see if the user is moving (arrow keys), or pausing ('p') """
        try:
            self.pause = False
            # if key == keyboard.Key.esc: ## Lags a lot
            if key == keyboard.KeyCode.from_char('p'):
                self.pause = True
                return

            new_x, new_y = self.x_loc, self.y_loc

            self.console.addstr(self.y_loc, self.x_loc * 2,
                                self.main_map.MAP_CHARS[self.main_map.map[new_y][new_x]])

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
            if new_x < 0:
                new_x = 0
            if new_y < 0:
                new_y = 0

            if new_x >= self.x_max:
                new_x = self.x_max - 1
            if new_y >= self.y_max:
                new_y = self.y_max - 1

            if self.main_map.map[new_y][new_x] == "WALKABLE":
                self.x_loc, self.y_loc = new_x, new_y

            self.console.addstr(self.y_loc, self.x_loc * 2, self.char)
            self.console.refresh()

            return self.check_triggers()
        except _curses.error:
            self.console.clear()
            curses.endwin()
            self.exit_code = 1
            return False

    def link_relocation(self, trip_location: Tuple[int, int], destination: Tuple[int, int]):
        self.triggers.append(GameTrigger.MapSysRelocationTrigger(self, trip_location, destination))


if __name__ == "__main__":
    main_title = TitleSysIO(title="Game", option_choices=["Start", "Quit"])
    pause_title = TitleSysIO(title="Pause", option_choices=["Continue", "Return to menu"],
                             font_size=12)
    map_sys = MapIO(BlankSystem(10, 10, "WALKABLE"), 1, 1)

    main_title.link_sys_change([], lambda x: x.chosen and x.chosen_option == "Quit")
    main_title.link_sys_change([map_sys], lambda x: x.chosen and x.chosen_option == "Start")

    pause_title.link_sys_change([main_title],
                                lambda x: x.chosen and x.chosen_option == "Return to menu")
    pause_title.link_sys_change([map_sys], lambda x: x.chosen and x.chosen_option == "Continue")

    map_sys.link_sys_change([pause_title], lambda x: x.pause, transient=True)

    map_sys.link_relocation((0, 0), (5, 5))

    start_game_sys([main_title])
