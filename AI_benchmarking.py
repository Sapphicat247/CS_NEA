from src import catan
from src.ai import AI, AI_Random
import colours
import dearpygui.dearpygui as dpg
from collections import Counter

import random

def rotate(l: list, n: int) -> list:
    return l[n:] + l[:n]

COLOUR_LIST = [
    colours.fg.RED +    colours.bg.RGB(0, 0, 0),
    colours.fg.ORANGE + colours.bg.RGB(0, 0, 0),
    colours.fg.BLUE +   colours.bg.RGB(0, 0, 0),
    colours.fg.WHITE +  colours.bg.RGB(0, 0, 0),
    ]

# MARK: dpg stuff

# create dpg widow
dpg.create_context()

# init viewport
dpg.create_viewport(title='Custom Title', width=600, height=200)
dpg.setup_dearpygui()
dpg.show_viewport()

# create a board
board = catan.Board()

# create AIs

AI_list: list[AI] = [
    AI_Random(catan.Colour.RED),
    AI_Random(catan.Colour.ORANGE),
    AI_Random(catan.Colour.BLUE),
    AI_Random(catan.Colour.WHITE),
]

for ai in AI_list:
    with dpg.window(label=ai.colour.name):
        
        dpg.add_text(f"{ai.victory_points} VPs", tag=f"{ai.colour.name}_vps")
        dpg.add_text(f"\nresources:")
        with dpg.table(header_row=False):
            dpg.add_table_column()
            dpg.add_table_column()
            
            for resource in catan.Resource:
                if resource != catan.Resource.DESERT:
                    with dpg.table_row():
                        dpg.add_text(resource.name)
                        dpg.add_text("0", tag=f"{ai.colour.name}_{resource.name}_number")
        
        dpg.add_text(f"\nDevelopment cards:")
        with dpg.table(header_row=False):
            dpg.add_table_column()
            dpg.add_table_column()
            
            for development_card in catan.Development_card:
                
                with dpg.table_row():
                    dpg.add_text(development_card.name)
                    dpg.add_text("0", tag=f"{ai.colour.name}_{development_card.name}_number")
    
with dpg.window(label="graphs"):
    pass


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
                if effect["road_pos"] not in board.verts[effect["settlement_pos"]].edges:
                    raise catan.BuildingError("Not connected to correct settlement")
                
                board.place_road(catan.Colour(i+1), None, effect["road_pos"])
                
            except catan.BuildingError as e:
                print(f"error: invalid road placement: {e}")
                board.delete_settlement(effect["settlement_pos"]) # dont keep settlement
                # don't need to delete road as it's not placed if an error is raised
            
            else: # can build road!
                AI_list[i].victory_points += 1
                break

print(f"{colours.fg.GREEN}setup took {attempts} attempts{colours.fg.END}")

def update():
    board.draw()
    dpg.render_dearpygui_frame()
    
    for ai in AI_list:
        resources_counter = Counter(ai.resources)
        development_cards_counter = Counter(ai.development_cards)
        
        dpg.set_value(f"{ai.colour.name}_vps", f"{ai.victory_points} VPs")
        
        for resource in catan.Resource:
            if resource != catan.Resource.DESERT:
                dpg.set_value(f"{ai.colour.name}_{resource.name}_number", f"{resources_counter[resource]}")
        
        for development_card in catan.Development_card:
            dpg.set_value(f"{ai.colour.name}_{development_card.name}_number", f"{development_cards_counter[development_card]}")

# MARK: main loop
current_turn = 0

# below replaces, start_dearpygui()
while dpg.is_dearpygui_running():
    # insert here any code you would like to run in the render loop
    # you can manually stop by using stop_dearpygui()
    #print("this will run every frame")

    current_AI = AI_list[current_turn]
    print(f"{COLOUR_LIST[current_turn]}{catan.Colour(current_turn+1).name} is having a turn{colours.END}")
    print("\trolling dice")
    dice = random.randint(1, 6) + random.randint(1, 6)
    print(f"\trolled a {dice};", "moving robber\n" if dice == 7 else "distributing resources: ", end="")
    # filter for rolling a 7
    
    if dice == 7:
        # hand limit of 7
        for ai in AI_list:
            if len(ai.resources) > 7:
                discarded = []
                while 1:
                    discarded = ai.discard_half()
                    if len(discarded) != len(ai.resources)//2:
                        continue # too many / too few cards chosen
                    
                    if catan.can_afford(ai.resources, discarded):
                        for card in discarded:
                            ai.resources.remove(card)
                            
                        break # ai has enough cards
                    
                    # ai tried to discard cards it doesn't have
        
        # robber
        new_robber_pos = 1000 # will error if this is ever used
        while 1:
            new_robber_pos, steal_target = AI_list[current_turn].move_robber(board)
            if new_robber_pos != board.get_robber_pos():
                # valid robber move
                
                if steal_target == None or steal_target == AI_list[current_turn].colour:
                    break # don't steal
                
                # try to steal from someone
                
                adj_vert_owners = [board.verts[i].structure.owner for i in board.hexes[new_robber_pos].verts]
                
                if steal_target not in adj_vert_owners:
                    continue # cant steal from a player not on the robbers hex
                
                # steal from target
                for ai in AI_list:
                    if ai.colour == steal_target:
                        # found target
                        if len(ai.resources) != 0: # only steal if they have >1 card
                            card = random.choice(ai.resources)
                            print(f"\t{AI_list[current_turn].ansi_colour}{AI_list[current_turn].colour}{colours.END} stole {card} from {ai.ansi_colour}{ai.colour}{colours.END}")
                            ai.resources.remove(card)
                            
                            AI_list[current_turn].resources.append(card)
                
                break # sucesfully stole
            
        board.set_robber_pos(new_robber_pos) # move robber after steal in-case AI tries to steal from invalid player
                
        
    else:
        resources = board.get_resources(dice)
        print(resources)
        for ai in AI_list:
            ai.resources += resources[ai.colour]
            ai.on_opponent_action(("dice roll", dice), board)
    
    update()
    
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
                    board.place_settlement(current_AI.colour, current_AI.resources, pos)
                
                except catan.BuildingError:
                    # cant place settlement, due to game rules
                    continue
                
                # can place settlement
                current_AI.resources.remove(catan.Resource.WOOL)
                current_AI.resources.remove(catan.Resource.WOOD)
                current_AI.resources.remove(catan.Resource.BRICK)
                current_AI.resources.remove(catan.Resource.GRAIN)

                current_AI.victory_points += 1
                
                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
            
            case ["build city", pos] if type(pos) == int:
                try:
                    board.place_city(current_AI.colour, current_AI.resources, pos)
                
                except catan.BuildingError:
                    # cant place city, due to game rules
                    continue
                
                # can place city
                current_AI.resources.remove(catan.Resource.GRAIN)
                current_AI.resources.remove(catan.Resource.GRAIN)
                current_AI.resources.remove(catan.Resource.ORE)
                current_AI.resources.remove(catan.Resource.ORE)
                current_AI.resources.remove(catan.Resource.ORE)

                current_AI.victory_points += 1
                
                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
                
            case ["build road", pos] if type(pos) == int:
                try:
                    board.place_road(current_AI.colour, current_AI.resources, pos)
                
                except catan.BuildingError:
                    # cant place road, due to game rules
                    continue
                
                # can place road
                current_AI.resources.remove(catan.Resource.WOOD)
                current_AI.resources.remove(catan.Resource.BRICK)

                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
                
            case ["buy developmeant card", None]:
                if not catan.can_afford(current_AI.resources, catan.Building.DEVELOPMENT_CARD):
                    continue # can't afford it
                
                current_AI.resources.remove(catan.Resource.WOOL)
                current_AI.resources.remove(catan.Resource.GRAIN)
                current_AI.resources.remove(catan.Resource.ORE)
                current_AI.development_cards.append(board.development_cards.pop()) # give AI a development card
            
            case ["use developmeant card", card] if type(card) == catan.Development_card:
                if card not in current_AI.development_cards:
                    continue # can't use a card you don't have
                
                # has card
                current_AI.development_cards.remove(card)
                # interprit card TODO
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
        # so notify players and update gui
        
        for ai in AI_list:
            if ai != current_AI:
                ai.on_opponent_action((action, args), board)
        
        board.draw()
        
        # update info pannels for each player
        
        update()
        
    print("\tturn over, 'passing the dice'")
    
    # increment turn counter
    current_turn += 1
    current_turn %= 4
    update()

dpg.destroy_context()