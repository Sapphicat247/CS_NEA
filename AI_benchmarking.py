from src import AI, catan
import colours
import copy

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

for i, j in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
    while 1:
        print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing it's {j} settlement{colours.END}")
        effect = players[i].place_starter_settlement(j, board)
        if board.valid_placement(catan.Structure(catan.Colour(i+1), catan.Building.SETTLEMENT), effect["settlement"], settlements_need_road=False):
            # settlement can be placed there
            
            tester = copy.deepcopy(board)
            tester.verts[effect["settlement"]].structure = catan.Structure(catan.Colour(i+1), catan.Building.SETTLEMENT)
            if board.valid_placement(catan.Structure(catan.Colour(i+1), catan.Building.ROAD), effect["road"]):
                # road can be placed
                board.verts[effect["settlement"]].structure = catan.Structure(catan.Colour(i+1), catan.Building.SETTLEMENT)
                board.edges[effect["road"]].structure = catan.Structure(catan.Colour(i+1), catan.Building.ROAD)
                
                break # valid input so break out of the loop
            
            else:
                print("error: invalid road placement")
        else:
            print("error: invalid settlement placement")

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