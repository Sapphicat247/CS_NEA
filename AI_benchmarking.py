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

attempts = 0

for i, j in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
    while 1:
        attempts += 1
        print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing it's {j} settlement", end=" ")
        effect = players[i].place_starter_settlement(j, board) # get a move from the AI
        print(f"at {effect}{colours.END}")
        
        try:
            board.place_settlement(catan.Colour(i+1), effect["settlement_pos"], need_road=False)
            
        except catan.BuildingError as e:
            print(f"error: invalid settlement placement: {e}")
        
        else: # can build settlement
            try:
                board.place_road(catan.Colour(i+1), effect["road_pos"])
                
            except catan.BuildingError as e:
                print(f"error: invalid road placement: {e}")
                board.delete_settlement(effect["settlement_pos"]) # dont keep settlement
            
            else: # can build road
                break

print(f"{colours.fg.GREEN}setup took {attempts} attempts{colours.fg.END}")

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
    break