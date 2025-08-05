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
def get_by_colour(col: catan.Colour) -> AI:
    for i in AI_list:
        if i.colour == col:
            return i
    
    raise ValueError(f"no AI with colour: {col.name}")

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

for i, j in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
    while 1:
        print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing it's {j} settlement and road at: ", end=" ")
        settlement_pos, road_pos = AI_list[i].place_starter_settlement(j, board) # get a move from the AI
        print(f"{settlement_pos} and {road_pos}{colours.END}")
        
        board.place_settlement(catan.Colour(i+1), None, settlement_pos, need_road=False)

        if road_pos not in board.verts[settlement_pos].edges:
            raise catan.BuildingError("Not connected to correct settlement")
        
        board.place_road(catan.Colour(i+1), None, road_pos)
            
        AI_list[i].victory_points += 1
        break

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

def move_robber_and_steal(pos, mover: AI, steal_from: AI | None):
    if pos == board.get_robber_pos():
        raise ValueError("you can't move the robber to the same space it is already on")
    
    if pos < 0 or pos > 18:
        raise ValueError(f"hex: {pos} doesn't exist")
    
    # valid robber position
    if steal_from == None:
        board.set_robber_pos(pos) # always valid
        return
    
    if steal_from == mover:
        raise ValueError("you can't steal from yourself")
    
    adj_vert_owner_ais = [get_by_colour(board.verts[i].structure.owner) for i in board.hexes[pos].verts if board.verts[i].structure.owner != catan.Colour.NONE]
    
    if steal_from not in adj_vert_owner_ais:
        raise ValueError(f"{steal_from.colour} doen't own any settlements or cities adjacent to the robber position")
    
    # valid steal config
    if len(steal_from.resources) != 0: # only steal if they have >1 card
        card = random.choice(steal_from.resources)
        print(f"\t{mover.ansi_colour}{mover.colour}{colours.END} stole {card} from {steal_from.ansi_colour}{steal_from.colour}{colours.END}")
        steal_from.resources.remove(card)
        
        mover.resources.append(card)
    
    board.set_robber_pos(pos)

# MARK: main loop
current_turn = 0

while dpg.is_dearpygui_running():
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
                
                discarded = ai.discard_half()
                if len(discarded) != len(ai.resources)//2:
                    raise ValueError(f"{len(discarded)} is not half of your hand")
                
                if not catan.can_afford(ai.resources, discarded):
                    raise ValueError("you can't discard cards you don't have")
                
                for card in discarded:
                    ai.resources.remove(card)
        
        # robber
        new_robber_pos, steal_target = current_AI.move_robber(board) # get the robber movement
        
        if steal_target == catan.Colour.NONE:
            steal_target = None
        else:
            steal_target = get_by_colour(steal_target)
            
        move_robber_and_steal(new_robber_pos, current_AI, steal_target) # interprit the movement
        
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
                board.place_settlement(current_AI.colour, current_AI.resources, pos)
                
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
                board.place_city(current_AI.colour, current_AI.resources, pos)
                
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
                board.place_road(current_AI.colour, current_AI.resources, pos)
                
                # can place road
                current_AI.resources.remove(catan.Resource.WOOD)
                current_AI.resources.remove(catan.Resource.BRICK)

                for ai in AI_list:
                    if ai != current_AI:
                        ai.on_opponent_action((action, args), board)
                
            case ["buy developmeant card", None]:
                if not catan.can_afford(current_AI.resources, catan.Building.DEVELOPMENT_CARD):
                    raise ValueError("you can't afford a developmeant card")
                
                current_AI.resources.remove(catan.Resource.WOOL)
                current_AI.resources.remove(catan.Resource.GRAIN)
                current_AI.resources.remove(catan.Resource.ORE)
                current_AI.development_cards.append(board.development_cards.pop()) # give AI a development card
            
            case ["use developmeant card", opts] if type(opts) == tuple:
                card, opts = opts
                if card not in current_AI.development_cards:
                    raise ValueError("you can't use a card you don't have")
                
                # has card
                current_AI.development_cards.remove(card)
                # interprit card TODO
                match card:
                    case catan.Development_card.KNIGHT:
                        new_robber_pos, steal_target = current_AI.move_robber(board) # get the robber movement
                        move_robber_and_steal(new_robber_pos, current_AI, get_by_colour(steal_target)) # interprit the movement
                        
                    case catan.Development_card.VICTORY_POINT:
                        raise ValueError("you can't play victory point cards")
                        
                    case catan.Development_card.YEAR_OF_PLENTY:
                        resource_1 = opts["resource 1"]
                        resource_2 = opts["resource 2"]
                        
                        if type(resource_1) != catan.Resource:
                            raise ValueError(f"{resource_1} is not a resource")
                        
                        if type(resource_2) != catan.Resource:
                            raise ValueError(f"{resource_2} is not a resource")
                        
                        current_AI.resources.append(resource_1)
                        current_AI.resources.append(resource_2)
                        
                    case catan.Development_card.ROAD_BUILDING:
                        pos_1 = opts["pos 1"]
                        pos_2 = opts["pos 1"]
                        
                        if type(pos_1) != int:
                            raise ValueError(f"{pos_1} is not an int")
                        
                        if type(pos_2) != int:
                            raise ValueError(f"{pos_2} is not an int")
                        
                        board.place_road(current_AI.colour, current_AI.resources, pos_1)
                        board.place_road(current_AI.colour, current_AI.resources, pos_2)
                        
                    case catan.Development_card.MONOPOLY:
                        resource = opts["resource"]
                        if type(resource) != catan.Resource:
                            raise ValueError(f"{resource} is not a Resource")
                        
                        taken = 0
                        for ai in AI_list:
                            if ai != current_AI:
                                while resource in ai.resources:
                                    ai.resources.remove(resource)
                                    taken += 1
                                    
                        current_AI.resources += [resource]*taken
                        
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