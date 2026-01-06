from src import catan
from src.ai import AI, AI_Random
from src.player import Player

import colours

import dearpygui.dearpygui as dpg
import random

HAS_HUMAN = True

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
dpg.create_viewport(title='Catan', width=1920, height=1080)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.toggle_viewport_fullscreen()
# create a board
board = catan.Board()

# create AIs

AI_list: list[AI] = [
    Player(catan.Colour.RED) if HAS_HUMAN else AI_Random(catan.Colour.RED),
    AI_Random(catan.Colour.ORANGE),
    AI_Random(catan.Colour.BLUE),
    AI_Random(catan.Colour.WHITE),
]
def get_by_colour(col: catan.Colour) -> AI:
    """returns the AI with this colour"""
    for i in AI_list:
        if i.colour == col:
            return i
    
    raise ValueError(f"no AI with colour: {col.name}")

pos_list = [(0,0), (0,1080-400-39), (1920-300-16, 0), (1920-300-16, 1080-400-39)]

if not HAS_HUMAN: # show debug info on AIs

    for ai_index, ai in enumerate(AI_list):
        with dpg.window(label=ai.colour.name, width=300, height=400, pos=pos_list[ai_index], ):
            dpg.add_text(f"{ai.victory_points} ({0}) VPs", tag=f"{ai.colour.name}_vps")
            
            with dpg.tab_bar():
                with dpg.tab(label = "hand"):
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
                            if development_card != catan.Development_card.NONE:
                                
                                with dpg.table_row():
                                    dpg.add_text(development_card.name)
                                    dpg.add_text("0", tag=f"{ai.colour.name}_{development_card.name}_number")

ready_for_turn = True
def next_turn():
    global ready_for_turn
    ready_for_turn = True

auto_run = -1

if not HAS_HUMAN:    
    with dpg.window(label="graphs", pos= (400+39, 0)):
        dpg.add_button(label="next turn", callback=next_turn)
        auto_run = dpg.add_checkbox(label="auto")


# MARK: set-up phaze
# choose starting player

for i, j in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
    while 1:
        #print(f"{COLOUR_LIST[i]}{catan.Colour(i+1).name} is placing it's {j} settlement and road at: ", end=" ")
        settlement_pos, road_pos = AI_list[i].place_starter_settlement(j, board.safe_copy) # get a move from the AI
        #print(f"{settlement_pos} and {road_pos}{colours.END}")
        
        board.place_settlement(catan.Colour(i+1), hand=None, position=settlement_pos, need_road=False)

        if road_pos not in board.verts[settlement_pos].edges:
            raise catan.BuildingError("Not connected to correct settlement")
        
        board.place_road(catan.Colour(i+1), hand=None, position=road_pos)
            
        AI_list[i].victory_points += 1
        break

def update() -> bool:
    """update GUI"""
    board.draw()
    dpg.render_dearpygui_frame()
    
    if  HAS_HUMAN:
        AI_list[0].update_gui()
    else:
        for ai in AI_list:
            
            real_vps = ai.victory_points + ai.development_cards[catan.Development_card.VICTORY_POINT]
            dpg.set_value(f"{ai.colour.name}_vps", f"{ai.victory_points} ({real_vps}) VPs")
            
            for resource in catan.Resource:
                if resource != catan.Resource.DESERT:
                    dpg.set_value(f"{ai.colour.name}_{resource.name}_number", f"{ai.resources[resource]}")
            
            for development_card in catan.Development_card:
                if development_card != catan.Development_card.NONE:
                    dpg.set_value(f"{ai.colour.name}_{development_card.name}_number", f"{ai.development_cards[development_card]}")
            
            if ai.victory_points + ai.development_cards[catan.Development_card.VICTORY_POINT] >= 10:
                return True
    
    return False

def move_robber_and_steal(pos, mover: AI, steal_from: AI | None):
    if pos == board.robber_pos:
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
    if sum(steal_from.resources.values()) > 0: # only try to steal if they have >1 card
        card = random.choices(list(steal_from.resources.keys()), list(steal_from.resources.values()))[0]
        #print(f"\t{mover.ansi_colour}{mover.colour}{colours.END} stole {card} from {steal_from.ansi_colour}{steal_from.colour}{colours.END}")
        
        steal_from.resources[card] -= 1
        mover.resources[card] += 1
    
    board.set_robber_pos(pos)

# MARK: main loop
current_turn = 0

while dpg.is_dearpygui_running():
    update()
    if not HAS_HUMAN:
        while not ready_for_turn and dpg.get_value(auto_run) == False:
            update()
    
    ready_for_turn = False
    current_AI = AI_list[current_turn]
    
    #print(f"{COLOUR_LIST[current_turn]}{catan.Colour(current_turn+1).name} is having a turn{colours.END}")
    #if DEBUG: print("\trolling dice")
    dice = random.randint(1, 6) + random.randint(1, 6)
    #print(f"\trolled a {dice};", "moving robber" if dice == 7 else "distributing resources")
    # filter for rolling a 7
    
    if dice == 7:
        # hand limit of 7
        for ai in AI_list:
            temp = sum(ai.resources.values())
            if temp > 7:
                
                discarded = ai.discard_half()
                if sum(discarded.values()) != sum(ai.resources.values())//2:
                    raise ValueError(f"{sum(discarded.values())} is not half of your hand of {sum(ai.resources.values())}")
                
                if not catan.can_afford(ai.resources, discarded):
                    raise ValueError("you can't discard cards you don't have")
                
                for card in discarded.keys():
                    ai.resources[card] -= discarded[card]
        
        # robber
        new_robber_pos, steal_target = current_AI.move_robber(board.safe_copy) # get the robber movement
        
        if steal_target == catan.Colour.NONE:
            steal_target = None
        else:
            steal_target = get_by_colour(steal_target)
            
        move_robber_and_steal(new_robber_pos, current_AI, steal_target) # interprit the movement
        
    else:
        resources = board.get_resources(dice)
        #if DEBUG: print(resources)
        for ai in AI_list:
            for resource in resources[ai.colour].keys():
                ai.resources[resource] += resources[ai.colour][resource]
        
            ai.on_opponent_action(catan.Action(catan.Event.DICE_ROLL, dice), board.safe_copy)
    
    if update():
        break
    
    while 1:
        #if DEBUG: print("\tdoing action")
        action = current_AI.do_action(board.safe_copy)
        
        #print(f"\t{action.event.name}: {action.arg}")
        
        # try to do action
        match action.event, action.arg:
            case [catan.Event.END_TURN, None]:
                break
            
            case [catan.Event.BUILD_SETTLEMENT, pos] if type(pos) == int:
                board.place_settlement(current_AI.colour, hand=current_AI.resources, position=pos)
                
                # can place settlement
                current_AI.resources[catan.Resource.BRICK] -= 1
                current_AI.resources[catan.Resource.WOOD] -= 1
                current_AI.resources[catan.Resource.WOOL] -= 1
                current_AI.resources[catan.Resource.GRAIN] -= 1

                current_AI.victory_points += 1
            
            case [catan.Event.BUILD_CITY, pos] if type(pos) == int:
                board.place_city(current_AI.colour, hand=current_AI.resources, position=pos)
                
                # can place city
                current_AI.resources[catan.Resource.ORE] -= 3
                current_AI.resources[catan.Resource.GRAIN] -= 2

                current_AI.victory_points += 1
                
            case [catan.Event.BUILD_ROAD, pos] if type(pos) == int:
                board.place_road(current_AI.colour, hand=current_AI.resources, position=pos)
                
                # can place road
                current_AI.resources[catan.Resource.BRICK] -= 1
                current_AI.resources[catan.Resource.WOOD] -= 1
                
            case [catan.Event.BUY_DEV_CARD, None]:
                if not catan.can_afford(current_AI.resources, catan.Building.DEVELOPMENT_CARD):
                    raise ValueError("you can't afford a developmeant card")
                
                current_AI.resources[catan.Resource.ORE] -= 1
                current_AI.resources[catan.Resource.WOOL] -= 1
                current_AI.resources[catan.Resource.GRAIN] -= 1
                
                
                try:
                    current_AI.development_cards[board.development_cards.pop()] += 1 # give AI a development card
                except IndexError:
                    print("no development cards left")
            
            case [catan.Event.USE_KNIGHT, None]:
                new_robber_pos, steal_target = current_AI.move_robber(board.safe_copy) # get the robber movement
                move_robber_and_steal(new_robber_pos, current_AI, get_by_colour(steal_target)) # interprit the movement
            
            case [catan.Event.USE_YEAR_OF_PLENTY, [resource_1, resource_2]] if type(resource_1) == catan.Resource and type(resource_2) == catan.Resource:
                if type(resource_1) != catan.Resource or type(resource_2) != catan.Resource:
                    raise ValueError(f"{resource_1} or {resource_2} is not a Resource")
                
                current_AI.resources[resource_1] += 1
                current_AI.resources[resource_2] += 1
                
            case [catan.Event.USE_ROAD_BUILDING, [pos_1, pos_2]] if type(pos_1) == int and type(pos_2) == int:
                board.place_road(current_AI.colour, hand=None, position=pos_1)
                board.place_road(current_AI.colour, hand=None, position=pos_2)
                
            case [catan.Event.USE_MONOPOLY, resource] if type(resource) == catan.Resource:
                taken = 0
                for ai in AI_list:
                    if ai != current_AI:
                        taken += ai.resources[resource]
                        ai.resources[resource] = 0
                            
                current_AI.resources[resource] += taken
            
            case [catan.Event.TRADE, giving, recieving]:
                ...
            
            case _:
                raise Exception(f"could not interprit {action} as an action")

        # if it gets to here, action was succesfull.
        # so notify players and update gui
        
        for ai in AI_list:
            if ai != current_AI:
                ai.on_opponent_action(action, board.safe_copy)
        
        board.draw()
        
        # update info pannels for each player
        
        if update():
            break
        
    #if DEBUG: print("\tturn over, 'passing the dice'")
    
    # increment turn counter
    current_turn += 1
    current_turn %= 4
    if update():
        break

for ai in AI_list:
    if ai.victory_points + ai.development_cards[catan.Development_card.VICTORY_POINT] >= 10:
        print(f"{ai.ansi_colour}{ai.colour.name} WON!{colours.END}")

while dpg.is_dearpygui_running():
    update()

dpg.destroy_context()