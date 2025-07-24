from src import AI, catan
import colours
import random

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

AI_list: list[AI.AI] = [
    AI.AI(catan.Colour.RED),
    AI.AI(catan.Colour.ORANGE),
    AI.AI(catan.Colour.BLUE),
    AI.AI(catan.Colour.WHITE),
]

# MARK: set-up phaze
# choose starting player

attempts = 0

for i, j in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
    while 1:
        attempts += 1
        print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing it's {j} settlement", end=" ")
        effect = AI_list[i].place_starter_settlement(j, board) # get a move from the AI
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
                AI_list[i].victory_points += 1
                break

print(f"{colours.fg.GREEN}setup took {attempts} attempts{colours.fg.END}")

# MARK: main loop

current_turn = 0

while 1:
    print(f"{COLOUR_LIST[current_turn]}{catan.Colour(current_turn+1).name} is having a turn{colours.END}")
    print("\trolling dice")
    dice = random.randint(1, 6) + random.randint(1, 6)
    print(f"\trolled a {dice};", "moving robber" if dice == 7 else "distributing resources")
    # filter for rolling a 7
    
    if dice == 7:
        ...# TODO do robber stuff
        
    else:
        resources = board.get_resources(dice)
        for ai in AI_list:
            ai.hand += resources[ai.colour]
    
    while 1:
        print("\tdoing action")
        action, args = AI_list[current_turn].do_action(board)
        
        print(f"\tinterpriting action: {action}")
        
        match action:
            case "end turn":
                break
    
    print("\tturn over, 'passing the dice'")
    
    # increment turn counter
    current_turn += 1
    current_turn %= 4
    break