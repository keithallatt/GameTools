from __future__ import annotations
from colorama import Fore, Style, init
import random
import time

init()


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

    def __str__(self):
        pass

    def attempt(self):
        pass

    def is_solved(self) -> bool:
        pass

    def get_rules(self) -> str:
        pass

    def get_hint(self) -> str:
        pass


class AnagramPuzzle(PuzzleSystem):
    """ Cog / wheel puzzle where dials turned until the right solution appears. """
    def __init__(self, solution: str,
                 false_positives: list[str] = None,
                 wl: int = 3,
                 wheels: list[str] = None,
                 hint=None):
        super().__init__()
        self.hint = hint
        if len(solution) >= 10:
            raise PuzzleException(self, msg="Solution cannot be more than 9 characters")
        self.solution = solution

        if wheels is not None:
            for c_i in range(len(solution)):
                if solution[c_i] not in wheels[c_i]:
                    raise PuzzleException(self, msg="Puzzle not possible in this configuration")

            self.wheels = wheels
            return

        for i in range(len(false_positives)):
            fp = false_positives[i]
            while len(fp) < len(solution):
                fp += chr(random.randint(ord('a'), ord('z')))
            false_positives[i] = fp

        self.wheels = [
            [solution[c]] + [fp[c]
                             for fp in false_positives]
            for c in range(len(solution))
        ]

        self.wheels = [wheel +
                       [chr(random.randint(ord('a'), ord('z'))) for _ in range(wl - len(wheel))]
                       for wheel in self.wheels]

        while self.is_solved():
            for i in range(len(self.wheels)):
                wheel = self.wheels[i]
                random.shuffle(wheel)
                self.wheels[i] = wheel

    def __str__(self):
        num_before_after = len(self.wheels[0]) // 2
        str_repr = ""
        for i in range(-num_before_after, len(self.wheels[0]) - num_before_after):
            if i == 0:
                str_repr += Fore.MAGENTA + f"{Fore.RESET}|{Fore.MAGENTA}---" * len(self.wheels)
                str_repr += Style.RESET_ALL + "|\n" + Fore.RED + f"{Fore.RESET}| {Fore.RED}"
                str_repr += f"{Fore.RESET} | {Fore.RED}".join([w[i] for w in self.wheels])
                str_repr += f"{Fore.RESET} |" + Fore.RESET + "\n" + Fore.MAGENTA
                str_repr += f"{Fore.RESET}|{Fore.MAGENTA}---" * len(self.wheels)
                str_repr += Style.RESET_ALL + "|"
            else:
                if i == -num_before_after or i == len(self.wheels[0]) - num_before_after - 1:
                    str_repr += Fore.WHITE
                    str_repr += "| " + f" | ".join([w[i] for w in self.wheels]) + " |"
                    str_repr += Fore.RESET
                else:
                    str_repr += "| " + f" | ".join([w[i] for w in self.wheels]) + " |"

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
            if in_.strip() == "exit" or in_.strip() == "leave":
                return
            if in_.strip() == "help":
                print(self.get_rules())
                continue
            for c in in_:
                try:
                    w = int(c) - 1
                    if 0 <= w < len(self.solution):
                        self.rotate_wheel(w)
                except ValueError:
                    pass
        print(ap)

        print(f"You solved it! The answer is {Fore.GREEN}{self.solution}{Fore.RESET}!")

    def get_rules(self):
        return f"\n- Use (1 - {len(self.solution)}) to rotate each dial from left to right. \n" \
               f"- Multiple commands can be issued at each turn. \n" \
               f"- Any non-digit character will be ignored.\n" \
               f"- Each dial turns down by one letter at a time. \n" \
               f"- To see these tips again type 'help'\n" + self.get_hint()

    def get_hint(self):
        return ("\n" + repr(self.hint) + "\n") if self.hint is not None else ""


class ColorPuzzle(PuzzleSystem):
    """ Puzzle of the variety of respond with the color of the text, not what is written.
        So if `blue` is written in red, the correct answer / response is 'red'. """
    def __init__(self, num_rounds: int = 5, time_limit: int = 10, num_strikes: int = 3):
        super().__init__()
        self.colors = [
            (Fore.RED, "red"),
            (Fore.LIGHTYELLOW_EX, "yellow"),
            (Fore.GREEN, "green"),
            (Fore.BLUE, "blue")
        ]
        self.num_rounds = num_rounds
        self.strikes = num_strikes
        self.time_limit = time_limit
        self.time_taken = None

    def attempt(self):
        input(self.get_rules())
        successes = 0
        failures = 0
        start_time = time.time()
        while True:
            i = random.randint(0, 3)
            j = random.randint(0, 3)
            while j == i:
                j = random.randint(0, 3)
            word = self.colors[i][1]
            color, solution = self.colors[j]

            print(color + word + Style.RESET_ALL)

            guess = input("> ")
            if guess.strip().lower() == solution:
                successes += 1
            elif guess.strip().lower() == "leave":
                return
            else:
                failures += 1

            if successes == self.num_rounds:
                self.time_taken = time.time() - start_time
                print(f"Successfully answered {self.num_rounds} rounds!")
                break
            if failures == self.strikes:
                self.time_taken = None
                print(f"Answered {self.strikes} rounds incorrectly!")
                break
            if time.time() - start_time > self.time_limit:
                self.time_taken = time.time() - start_time + 0.1  # just in case
                print(f"Took longer than {self.time_limit} seconds!")
                break

    def is_solved(self) -> bool:
        return self.time_taken is not None and self.time_taken <= self.time_limit

    def get_rules(self) -> str:
        return f"Respond to each prompt with the color of the text, not the color that is " \
               f"written. \nYou have {self.time_limit} seconds to answer {self.num_rounds}" \
               f" successfully, without making {self.strikes} or more mistakes.\nTime begins " \
               f"when you hit enter. \n> "

    def get_hint(self) -> str:
        pass


if __name__ == "__main__":
    ap = ColorPuzzle()
    ap.attempt()

    if ap.is_solved():
        print("Congratulations! You solved the puzzle!")
    else:
        print("Better luck next time!")
