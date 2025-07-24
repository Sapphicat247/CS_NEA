from src import catan
from src.AI import AI
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

AI_list: list[AI] = [
    AI(catan.Colour.RED),
    AI(catan.Colour.ORANGE),
    AI(catan.Colour.BLUE),
    AI(catan.Colour.WHITE),
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
            board.place_settlement(catan.Colour(i+1), None, effect["settlement_pos"], need_road=False)
            
        except catan.BuildingError as e:
            print(f"error: invalid settlement placement: {e}")
        
        else: # can build settlement
            try:
                board.place_road(catan.Colour(i+1), None, effect["road_pos"])
                
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
    current_AI = AI_list[current_turn]
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
            ai.on_opponent_action(("dice roll", dice), board)
    
    while 1:
        print("\tdoing action")
        action, args = current_AI.do_action(board)
        
        print(f"\tinterpriting action: {action}")
        
        # try to do action
        match action, args:
            case ["end turn", None]:
                break
            
            case ["build settlement", pos] if type(pos) == int:
                try:
                    board.place_settlement(current_AI.colour, current_AI.hand, pos)
                
                except catan.BuildingError:
                    # cant place settlement, due to game rules
                    continue
                
                # can place settlement
                current_AI.hand.remove(catan.Resource.WOOL)
                current_AI.hand.remove(catan.Resource.WOOD)
                current_AI.hand.remove(catan.Resource.BRICK)
                current_AI.hand.remove(catan.Resource.GRAIN)

                current_AI.victory_points += 1
                
                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
            
            case ["build city", pos] if type(pos) == int:
                try:
                    board.place_city(current_AI.colour, current_AI.hand, pos)
                
                except catan.BuildingError:
                    # cant place city, due to game rules
                    continue
                
                # can place city
                current_AI.hand.remove(catan.Resource.GRAIN)
                current_AI.hand.remove(catan.Resource.GRAIN)
                current_AI.hand.remove(catan.Resource.ORE)
                current_AI.hand.remove(catan.Resource.ORE)
                current_AI.hand.remove(catan.Resource.ORE)

                current_AI.victory_points += 1
                
                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
                
            case ["build road", pos] if type(pos) == int:
                try:
                    board.place_road(current_AI.colour, current_AI.hand, pos)
                
                except catan.BuildingError:
                    # cant place road, due to game rules
                    continue
                
                # can place road
                current_AI.hand.remove(catan.Resource.WOOD)
                current_AI.hand.remove(catan.Resource.BRICK)

                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
                
            case ["buy developmeant card", None]:
                if not catan.can_afford(current_AI.hand, catan.Building.DEVELOPMENT_CARD):
                    continue # can't afford it
                
                current_AI.hand.remove(catan.Resource.WOOL)
                current_AI.hand.remove(catan.Resource.GRAIN)
                current_AI.hand.remove(catan.Resource.ORE)
                current_AI.hand.append(board.development_cards.pop()) # give AI a development card
            
            case ["use developmeant card", card] if type(card) == catan.Development_card:
                if card not in current_AI.hand:
                    continue
                
                # has card
                current_AI.hand.remove(card)
                # interprit card
                match card:
                    case catan.Development_card.KNIGHT:
                        ...
                    case catan.Development_card.VICTORY_POINT:
                        ...
                    case catan.Development_card.YEAR_OF_PLENTY:
                        ...
                    case catan.Development_card.ROAD_BUILDING:
                        ...
                    case catan.Development_card.MONOPOLY:
                        ...
                    case _:
                        raise ValueError(f"{card} is not a development card???")
            
            case "trade":
                ...
            
            case _:
                ...
        
        # if it gets to here, action was succesfull.
        # so notify players
        
        for ai in AI_list:
            if ai != current_AI:
                ai.on_opponent_action((action, args), board)
        
    print("\tturn over, 'passing the dice'")
    
    # increment turn counter
    current_turn += 1
    current_turn %= 4
    break