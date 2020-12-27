""" Seems to work! """
from pynput import keyboard


options = [
    "Yes", "No", "Maybe"
]

index = 0


def option_str():
    global index, options
    return "   ".join(
        [
            "<" + options[i] + ">" if i == index else " " + options[i] + " "
            for i in range(len(options))
        ]
    )

def on_press(key):
    global index, options
    try:
        if key == keyboard.Key.left:
            index = max(index-1, 0)
        if key == keyboard.Key.right:
            index = min(index+1, len(options)-1)
        print('\r' + option_str(), end="")
    except AttributeError:
        print('\rspecial key {0} pressed'.format(
            key), end="")


def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False


if __name__ == "__main__":
    print('\r' + option_str(), end="")
    # Collect events until released
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release, suppress=True) as listener:
        listener.join()
