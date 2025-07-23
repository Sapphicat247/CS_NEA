# changes colour of the foreground (the text)
BLACK = "\033[30m"
GREY = "\033[90m"
WHITE = "\033[97m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"

ORANGE = "\033[38;2;255;127;0m"
PURPLE = "\033[38;2;32;0;127m"

END = "\033[39m"

def RGB(r, g, b) -> str:
    # sets foreground colour to RGB values
    return f"\033[38;2;{int(r)};{int(g)};{int(b)}m"

DICT = {"black": BLACK, "grey": GREY, "white": WHITE, "red": RED, "green": GREEN, "yellow": YELLOW, "blue": BLUE, "magenta": MAGENTA, "cyan": CYAN, "orange": ORANGE, "purple": PURPLE}

def rainbow(msg):
    result = ""
    msg = list(msg)
    j = 0
    for i in range(len(msg)):
        result += [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, MAGENTA][j%7] + msg[i]
        if msg[i] != " ":
            j+=1
    
    return result + END