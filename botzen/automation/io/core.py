"""
A module that offers classes with the ability to configure
each IO action  arbitrarily depending on the regarded action
"""

import os
import time
import keyboard
import pyscreeze
import pyautogui as pg
from pyscreeze import Box
from pyautogui import ImageNotFoundException


def get_position():
    """
    Returns a `Point` indicating
    where in the screen the mouse is
    located.
    """
    return pg.position()


class IOMove:
    def __init__(self, x: int, y: int, v: int) -> None:
        """
        :param int         x: Point to move in the x axis
        :param int         y: Point to move in the y axis
        :param int | float v: Velocity for the mouse to move
        """
        self.x = x
        self.y = y
        self.v = v

    def run(self):
        pg.moveTo(self.x, self.y, self.v)


class IOClick:
    def __init__(self):
        self.clicks = 1
        self.x = None
        self.y = None
        self.button = "primary"
        self.interval_wait = 0.0

    def at(self, x: int, y: int):
        """
        Defines the location of a click rather than clicking where
        is already at.

        :param x int: Where to click in the x axis of the screen
        :param y int: Where to click in the y axis of the screen
        """
        self.x = x
        self.y = y

    def with_left_button(self):
        """
        Sets the left button to be used for the clicking action
        """
        self.button = "left"

    def with_primary_button(self):
        """
        Sets the primary button to used for the clicking action
        """
        self.button = "primary"

    def with_right_button(self):
        """
        Sets the right button to used for the clicking action
        """
        self.button = "right"

    def wait(self, t: int | float):
        """
        Allows for a delay before a click
        """
        self.interval_wait = t

    def repeat(self, clicks: int):
        """
        Sets a different amount of clicks given an integer
        """
        assert clicks != 0, "Cannot click 0 times"
        self.clicks = clicks

    def run(self):
        if self.interval_wait == 0:
            pg.click(
                x=self.x,
                y=self.y,
                button=self.button,
                clicks=self.clicks,
            )
        else:
            for _ in range(self.clicks):
                time.sleep(self.interval_wait)
                pg.click(
                    x=self.x,
                    y=self.y,
                    button=self.button,
                )


class IOKeyboard:
    def __init__(self):
        self.interval_wait = 0.0

    def set_interval_wait(self, wait: float | int):
        """
        Modifies the `.interval_wait` variable
        for brief pauses when typing a string
        """
        self.interval_wait = wait

    def write(self, string: str):
        keyboard.write(string, delay=self.interval_wait)

    @staticmethod
    def is_pressed(key: str) -> bool:
        return keyboard.is_pressed(key)

    @staticmethod
    def add_hotkey(hotkey: str, function, args=()):
        """
        Upon detection of a hotkey, a call function is executed

        :param str        hotkey: Hotkey to register and detect. (eg. "ctrl+shift+e")
        :param Callable function: Callback function
        :param str          args: Arguments for the callback function
        """
        keyboard.add_hotkey(hotkey, function, args)

    @staticmethod
    def add_abbreviation(old: str, new: str):
        """
        Upon detection of the specified `old` sequence of characters,
        such string will get replaced by the new string given.

        :param str old: Sequence of characters needed to trigger
        :param str new: Replacement string for the old string
        """
        keyboard.add_abbreviation(old, new)


class IOPixel:
    def __init__(self, x: int = None, y: int = None):
        self.x = x
        self.y = y
        self.rgb = None

    def at(self, x: int, y: int):
        """
        Regards the pixel located in the given coordinates,
        rather than the underlying pixel from the mouse.
        """
        self.x = x
        self.y = y

    def set_rgb(self, r: int, g: int, b: int):
        assert 0 <= r <= 255, "Invalid red value"
        assert 0 <= g <= 255, "Invalid green value"
        assert 0 <= b <= 255, "Invalid blue value"
        self.rgb = (r, g, b)

    def manually_pick(self):
        """
        In case of uncertainty, this function
        helps to locate a pixel and memoize its
        coordinate and rbg value
        """
        print("Press `.` to select the pixel")
        keyboard.block_key(".")  # avoiding further input to other windows
        while True:
            x, y = pg.position()
            rgb = pg.pixel(x, y)
            print(f"\rX: {x}  Y: {y}  RBG: {str(rgb):>15}", end="")
            if keyboard.is_pressed("."):
                print("\n")
                self.x = x
                self.y = y
                self.rgb = rgb
                keyboard.unblock_key(".")
                return

    def is_active(self):
        """
        Checks if the pixel, given coordinates, is
        displaying the  RGB value specified.
        """
        return pg.pixelMatchesColor(
            self.x,
            self.y,
            self.rgb,
        )


class IOImage:
    def __init__(self, path: str):
        assert os.path.exists(path), f"`{path}` does not exist"
        assert os.path.isfile(path), f"`{path}` is not a file"
        self.path = path
        self.wait_for = False
        self.timeout = -1  # indicates no timeout is specified
        self.tolerance = 0
        self.place_mouse = False

    def check_for(self) -> tuple[bool, ...]:
        """
        indicates to check in the instance if the image exists
        """
        self.wait_for = False

    def set_timeout(self, timeout: int | float):
        self.timeout = timeout

    def place_mouse_over(self):
        """
        Indicates to move the mouse over
        to the detect image
        """
        self.place_mouse = True

    def set_tolerance(self, tolerance: int):
        """
        Regarding RGB values, `tolerance` defines
        the difference in how off the RGB value of pixel is.
        0 tolerance signifies an exact match, otherwise,
        a tolerance of, for example, 25 for the red value,
        and a tolerance of 2, if the detected red value is 24,
        25(original) - 24(detected) = 1 is within the range of
        tolerance.
        """
        self.tolerance = tolerance

    def wait_for_presence(self):
        """
        sets the `.wait_for` variable for the image to pop up indefinitely
        """
        self.wait_for = True

    def is_existing(self) -> tuple[bool, Box]:
        """
        Indicates whether such image is on the screen
        at that very instance
        """
        try:
            box = pg.locateOnScreen(self.path)
            return True, box
        except ImageNotFoundException:
            return False, None

    def run(self) -> tuple[bool, Box | None]:
        if self.wait_for:
            if self.timeout == -1:
                # if no timeout was specified
                while True:
                    exists, box = self.is_existing()
                    if exists:
                        if self.place_mouse_over:
                            center_point = pg.center(box)
                            pg.moveTo(center_point)
                        return True, box
                    time.sleep(0.01)  # millisecond pause to avoid unecessary lag
            else:
                start = time.time()
                while True:
                    time.sleep(1 / 100)  # millisecond pause to avoid unecessary lag
                    if time.time() - start >= self.timeout:
                        # checking if timeout is done
                        return False, None
                    exists, box = self.is_existing()
                    if exists:
                        if self.place_mouse_over:
                            center_point = pg.center(box)
                            pg.moveTo(center_point)
                        return True, box
        else:
            exists, box = self.is_existing()
            if exists and self.place_mouse:
                center_point = pg.center(box)
                pg.moveTo(center_point)
            return exists, box
