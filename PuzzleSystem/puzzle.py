from __future__ import annotations
from colorama import Fore, Style, init
from ansiwrap import *
import random


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
    def __init__(self):
        pass


class AnagramPuzzle(PuzzleSystem):
    """ Cog / wheel puzzle where dials turned until the right solution appears. """
    def __init__(self, solution: str, false_positives: list[str], wl: int = 3, wheels: list[str] = None):
        super().__init__()
        self.solution = solution

        for i in range(len(false_positives)):
            fp = false_positives[i]
            while len(fp) < len(solution):
                fp +=  chr(random.randint(ord('a'), ord('z')))
            false_positives[i] = fp

        self.wheels = [
            [solution[c]] + [fp[c]
                             for fp in false_positives]
            for c in range(len(solution))
        ]

        self.wheels = [wheel +
                       [chr(random.randint(ord('a'), ord('z'))) for i in range(wl - len(wheel))]
                       for wheel in self.wheels]

        for i in range(len(self.wheels)):
            wheel = self.wheels[i]
            random.shuffle(wheel)
            self.wheels[i] = wheel

    def __str__(self):
        num_before_after = len(self.wheels[0]) // 2
        str_repr = ""
        for i in range(-num_before_after, len(self.wheels[0]) - num_before_after):
            if i == 0:
                str_repr += "--" * len(self.wheels) + "-\n"
            str_repr += " " + " ".join([w[i] for w in self.wheels])
            if i == 0:
                str_repr += "\n" + "--" * len(self.wheels) + "-"
            str_repr += "\n"

        return str_repr

    def rotate_wheel(self, wheel_num: int):
        self.wheels[wheel_num] = [self.wheels[wheel_num][-1]] + self.wheels[wheel_num][:-1]

    def is_solved(self):
        return self.solution == "".join([w[0] for w in self.wheels])

    def attempt(self):
        print(self.get_rules())
        while not ap.is_solved():
            print(ap)
            in_ = input("> ")
            if in_.strip() == "exit":
                return
            for c in in_:
                try:
                    ap.rotate_wheel(int(c))
                except ValueError:
                    pass
        print(f"You solved it! The answer is {self.solution}")

    def get_rules(self):
        return "<Get Rules>"


if __name__ == "__main__":
    ap = AnagramPuzzle("puzzle", [], wl=7)
    ap.attempt()


