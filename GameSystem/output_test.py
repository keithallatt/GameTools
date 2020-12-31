import _curses
import curses
from MapSystem.map import MazeSystem, BlankSystem
from pynput import keyboard
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from time import sleep
from threading import Thread


def ascii_art(text: str, font: str = "Arial.ttf", font_size: int = 15, x_margin: int = 0,
              y_margin: int = 0, shadow_char: str = u'\u2591', fill_char: str = u'\u2588',
              double_width: bool = False, trim: bool = False, shadow: bool = False,
              full_shadow: bool = False):
    if full_shadow:
        shadow = True

    try:
        font_object = ImageFont.truetype(font, font_size)
    except OSError:
        font_object = ImageFont.truetype("/Library/Fonts/" + font, font_size)

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
        shadow_pixels_diag = np.roll(pixels, (1, 1), axis=(0, 1))
        shadow_pixels_top = shadow_pixels_diag
        shadow_pixels_bottom = shadow_pixels_diag
        if full_shadow:
            shadow_pixels_top = np.roll(pixels, (1, 0), axis=(0, 1))
            shadow_pixels_bottom = np.roll(pixels, (0, 1), axis=(0, 1))

        pixels = 2*pixels
        pixels = np.maximum(pixels, shadow_pixels_diag)
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


"""
If not running in Pycharm:
 - Click 'Run' menu
 - Click 'Edit Configurations...'
 - Check 'Emulate terminal in output console'
"""


class GameSysIO:
    def __init__(self):
        self.console = curses.initscr()  # initialize is our playground
        curses.curs_set(0)
        self.exception = None
        self.exit_code = None

    game_queue = []

    def on_press(self, key):
        pass

    def on_release(self, key):
        pass

    def draw_init(self):
        pass

    def restart(self):
        self.console.clear()
        self.draw_init()
        self.console.refresh()

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release,
                               suppress=True) as listener:
            listener.join()

    @staticmethod
    def my_timer():
        while True:
            if len(GameSysIO.game_queue) > 0:
                next_sys = GameSysIO.game_queue.pop(0)
                if type(next_sys) == tuple:
                    next_sys, args = next_sys
                    next_sys(*args)
                else:
                    next_sys.restart()
            else:
                exit(0)


class TitleSysIO(GameSysIO):
    def __init__(self, title: str, option_choices: list[str] = None, option_choice: int = 0):
        super().__init__()

        self.art = ascii_art(title, shadow=True)

        self.option_choices = [
            "Start", "Quit"
        ]
        if option_choices is not None:
            self.option_choices = option_choices
        self.option_choice = min(len(self.option_choices)-1, max(0, option_choice))

        self.board = str(self.art).split("\n")

        self.draw_init()

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release,
                               suppress=True) as listener:
            listener.join()

    def draw_init(self):
        self.console.clear()

        for i in range(len(self.board)):
            self.console.addstr(i, 0, self.board[i])

        for i in range(len(self.option_choices)):
            self.console.addstr(len(self.board)+2+i, 3, self.option_choices[i])
        self.console.addstr(len(self.board)+2, 1, ">")

        self.console.refresh()

    def on_press(self, key):
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

    def on_release(self, key):
        if key == keyboard.Key.enter:
            if self.option_choices[self.option_choice] == "Quit":
                # Stop listener
                GameSysIO.game_queue = []
                self.exit_code = 0
                self.console.clear()
                curses.endwin()
                return False
            if self.option_choices[self.option_choice] == "Start":
                # Stop listener
                GameSysIO.game_queue.append((MazeIO, (MazeSystem(10, 10),)))
                self.exit_code = 0
                self.console.clear()
                curses.endwin()
                return False
            if self.option_choices[self.option_choice] == "Continue":
                # Stop listener
                self.exit_code = 0
                self.console.clear()
                curses.endwin()
                return False


class MazeIO(GameSysIO):
    def __init__(self, maze: MazeSystem):
        super().__init__()

        x_max, y_max = maze.dims

        self.main_map = BlankSystem(x_max+4, y_max+4, "WALKABLE")
        self.main_map.draw_rect_to_map("WALL", 0, 0, x_max+4, y_max+4)
        self.main_map.draw_rect_to_map("WALL", 1, 0, x_max+2, y_max+4)

        self.main_map.draw_sub_map(maze, 2, 2)
        self.main_map.draw_to_map("WALKABLE", 3, 2)
        self.main_map.draw_to_map("WALKABLE", 3, 2)
        self.main_map.draw_to_map("WALKABLE", x_max, y_max+1)

        self.x_max, self.y_max = self.main_map.dims

        # this can be more streamlined but it's enough for demonstration purposes...
        self.console.clear()

        board = str(self.main_map).split("\n")

        for i in range(len(board)):
            self.console.addstr(i, 0, board[i])

        self.x_loc = (x_max + 1) // 2 + 1
        self.y_loc = 1

        self.char = "P1"

        self.console.addstr(self.y_loc, self.x_loc * 2, self.char)
        self.console.refresh()

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release,
                               suppress=True) as listener:
            listener.join()

    def draw_init(self):
        self.console.clear()

        board = str(self.main_map).split("\n")

        for i in range(len(board)):
            self.console.addstr(i, 0, board[i])

        self.console.addstr(self.y_loc, self.x_loc * 2, self.char)
        self.console.refresh()

    def on_press(self, key):
        try:
            new_x, new_y = self.x_loc, self.y_loc

            self.console.addstr(self.y_loc, self.x_loc * 2, self.main_map.MAP_CHARS[self.main_map.map[new_y][new_x]])

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

        except _curses.error as e:
            self.console.clear()
            curses.endwin()
            self.exit_code = 1
            return False

    def on_release(self, key):
        if key == keyboard.Key.esc:
            # Stop listener
            GameSysIO.game_queue.append((TitleSysIO, ("Game", ["Continue", "Quit"])))
            GameSysIO.game_queue.append(self)
            self.exit_code = 0
            self.console.clear()
            curses.endwin()
            return False


if __name__ == "__main__":
    GameSysIO.game_queue = [(TitleSysIO, ("Game",))]
    GameSysIO.running = True
    myThread = Thread(target=GameSysIO.my_timer)
    myThread.start()
