from __future__ import annotations
from colorama import Fore, Style, init
from ansiwrap import *



class PuzzleException(Exception):
    """Basic exception for errors raised by the inventory system"""

    def __init__(self, puzzle: PuzzleSystem, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occurred with Inventory:\n%s" % str(puzzle)
            super(PuzzleException, self).__init__(msg)
        self.msg = msg
        self.puzzle = puzzle


class PuzzleSystem:
    pass
