# changes colour of the background
BLACK = "\033[40m"
GREY = "\033[100m"
WHITE = "\033[107m"

RED = "\033[101m"
GREEN = "\033[102m"
YELLOW = "\033[103m"
BLUE = "\033[104m"
MAGENTA = "\033[105m"
CYAN = "\033[106m"

END = "\033[49m"

def RGB(r, g, b) -> str:
    # sets background colour to RGB values
    return f"\033[48;2;{int(r)};{int(g)};{int(b)}m"

DICT = {"black": BLACK, "grey": GREY, "white": WHITE, "red": RED, "green": GREEN, "yellow": YELLOW, "blue": BLUE, "magenta": MAGENTA, "cyan": CYAN}