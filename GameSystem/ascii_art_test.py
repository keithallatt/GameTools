from PIL import Image, ImageDraw, ImageFont
import numpy as np
from colorama import Fore, Back, Style


def ascii_art(text: str,
              font: str = "Arial.ttf",
              font_size: int = 15,
              x_margin: int = 0,
              y_margin: int = 0,
              fill_char: str = "#",
              fg: Fore = None,
              bg: Back = None,
              double_width: bool = False):

    try:
        font_object = ImageFont.truetype(font, font_size)
    except OSError:
        font_object = ImageFont.truetype("/Library/Fonts/" + font, font_size)

    size = font_object.getsize(text)

    size = (size[0] + 2 * x_margin,
            size[1] + 2 * y_margin)

    # size may be too small for some fonts / letters (

    img = Image.new("1", size, "black")

    draw = ImageDraw.Draw(img)
    draw.text((x_margin, y_margin), text, "white", font=font_object)

    pixels = np.array(img, dtype=np.uint8)
    chars = np.array([' ', fill_char], dtype="U1")[pixels]
    strings = chars.view('U' + str(chars.shape[1])).flatten()

    string = "\n".join(strings)

    if double_width:
        string = string.replace(" ", "  ")
        string = string.replace(fill_char, 2 * fill_char)

    color = (fg if fg is not None else "") + (bg if bg is not None else "")

    if bg is not None:
        string = string.replace(fill_char, color + fill_char + Style.RESET_ALL)
        string = string.replace(Style.RESET_ALL + color, '')

    return string


if __name__ == "__main__":
    print(ascii_art("How are you?", x_margin=2, fg=Fore.BLUE, bg=Back.BLUE))
