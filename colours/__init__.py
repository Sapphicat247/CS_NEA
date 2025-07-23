from . import fg
from . import bg
from . import style

END = "\033[0m"
def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(col: str) -> tuple[int, int, int]:
    return tuple([int(col[2*i+1:2*i+3], 16) for i in range(3)])