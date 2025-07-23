from src import AI, catan
import colours

def rotate(l: list, n: int) -> list:
    return l[n:] + l[:n]

COLOUR_LIST = [
    colours.fg.RED +    colours.bg.RGB(0, 0, 0),
    colours.fg.ORANGE + colours.bg.RGB(0, 0, 0),
    colours.fg.BLUE +   colours.bg.RGB(0, 0, 0),
    colours.fg.WHITE +  colours.bg.RGB(0, 0, 0),
    ]

# create a board
board = catan.Board()

# create AIs

players: list[AI.AI] = [
    AI.AI(), # red
    AI.AI(), # orange
    AI.AI(), # blue
    AI.AI(), # white
]

# MARK: set-up phaze
# choose starting player

for i in (0, 1, 2, 3):
    print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing first settlement{colours.END}")
    v, e =  players[i].place_first_settlement(board)

print()

for i in (3, 2, 1, 0):
    print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing second settlement{colours.END}")
    v, e =  players[i].place_second_settlement(board)

# MARK: main loop

current_turn = 0

while 1:
    while 1:
        print(f"{COLOUR_LIST[current_turn]}{catan.Colour(current_turn+1).name} is having a turn{colours.END}")
        
        # try to have turn
        effect = players[current_turn].have_turn(board)
        
        if effect["end_turn"] == True:
            break
    
    # increment turn counter
    current_turn += 1
    current_turn %= 4