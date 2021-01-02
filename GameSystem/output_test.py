import _curses
import curses
from MapSystem.map import Map, BlankSystem
from pynput import keyboard
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from threading import Thread
import os
import time

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
            trigger, other, transient, append = trigger_obj
            try:
                if trigger(self):
                    if append:
                        if type(other) == list:
                            GameSysIO.game_queue += other[::]
                        else:
                            GameSysIO.game_queue.append(other)
                    else:
                        if type(other) == list:
                            GameSysIO.game_queue = other[::]
                        else:
                            GameSysIO.game_queue = [other]

                    if transient:
                        GameSysIO.game_queue.append(self)

                    self.exit_code = 0
                    self.console.clear()
                    curses.endwin()
                    return False
            except AttributeError:
                # attribute error occurs if lambda is not the trigger for the
                # right type of game system.
                pass
        else:
            return True

    def link(self, other, trigger, transient=False, append=False):
        """ When the trigger is set, change to other, transient being if self is set as a
            return point """
        self.triggers.append((trigger, other, transient, append))

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
    def __init__(self, title: str, option_choices: list[str] = None, option_choice: int = 0):
        """ Create a title screen or menu. """
        super().__init__()

        self.art = ascii_art(title, shadow=True)

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
        """ Check to see if the user is moving (arrow keys) """
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
        except _curses.error:
            self.console.clear()
            curses.endwin()
            self.exit_code = 1
            return False

    def on_release(self, key: keyboard.Key):
        """ Check to see if the user is pausing. """
        return self.check_triggers()


if __name__ == "__main__":
    main_title = TitleSysIO(title="Game", option_choices=["Start", "Quit"])
    pause_title = TitleSysIO(title="Pause", option_choices=["Continue", "Quit"])
    map_sys = MapIO(BlankSystem(10, 10, "WALKABLE"), 1, 1)

    main_title.link([], lambda x: x.chosen and x.chosen_option == "Quit")
    main_title.link([map_sys], lambda x: x.chosen and x.chosen_option == "Start")

    pause_title.link([], lambda x: x.chosen and x.chosen_option == "Quit")
    pause_title.link([map_sys], lambda x: x.chosen and x.chosen_option == "Continue")

    map_sys.link([pause_title], lambda x: x.pause, transient=True)

    start_game_sys([main_title])
