import curses
import time
import ascii_art_test

"""
If not running in Pycharm:
 - Click 'Run' menu
 - Click 'Edit Configurations...'
 - Check 'Emulate terminal in output console'
"""

console = curses.initscr()  # initialize is our playground


# this can be more streamlined but it's enough for demonstration purposes...
def draw_board(text):
    console.clear()

    ascii_art = ascii_art_test.ascii_art(" ".join(text), x_margin=2, shadow=True, trim=True).split("\n")

    for i in range(len(ascii_art)):
        console.addstr(i, 0, ascii_art[i])

    console.refresh()


def draw_star(x, y, char="*"):
    console.addstr(x, y, char)
    console.refresh()


time_taken = 2

draw_board("Hi")  # draw a board
time.sleep(time_taken)  # wait a second
draw_board("Hello")  # draw a board
time.sleep(time_taken)  # wait a second
draw_board("Hey")  # draw a board
time.sleep(time_taken)  # wait a second
draw_board("Bye")  # draw a board
time.sleep(time_taken)  # wait a second

curses.endwin()  # return control back to the console
