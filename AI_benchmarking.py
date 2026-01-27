from src import catan
from src.ai import AI, AI_Random as OLD_AI, AI_V1 as CURRENT_AI
from src.player import Player

import colours

import dearpygui.dearpygui as dpg
import random

HAS_HUMAN = False
HEADLESS = True

# MARK: start

def rotate(l: list, n: int) -> list:
    return l[n:] + l[:n]

def get_by_colour(col: catan.Colour) -> AI:
    """returns the AI with this colour"""
    for i in AI_list:
        if i.colour == col:
            return i
    
    raise ValueError(f"no AI with colour: {col.name}")

def get_real_vps(ai: AI) -> int:
    return ai.victory_points + ai.development_cards[catan.DevelopmentCard.VICTORY_POINT] + (2 if board.largest_army == ai.colour else 0) + (2 if board.longest_road == ai.colour else 0)

def copy_of_board():
    b = board.safe_copy
    b.player_info = {i: {"res_cards": sum(get_by_colour(i).resources.values()), "dev_cards": sum(get_by_colour(i).development_cards.values()) + sum(get_by_colour(i).development_cards_on_cooldown.values())} for i in catan.Colours()}
    
    return b

def update() -> bool:
    """update GUI"""
    if not HEADLESS:
        board.draw()
        dpg.render_dearpygui_frame()
    max_vps = 0
    for ai in AI_list:
        ai.update_gui(copy_of_board())
        
        vps = get_real_vps(ai)
        max_vps = max(max_vps, vps)
        if vps >= 10:
            return True
    
    print(f"the highest VPs is: {max_vps}")
    return False

def move_robber_and_steal(pos, mover: AI, steal_from: AI | None):
    if pos == board.robber_pos:
        raise ValueError("you can't move the robber to the same space it is already on")
    
    if pos < 0 or pos > 18:
        raise ValueError(f"hex: {pos} doesn't exist")
    
    # valid robber position
    if steal_from is None:
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

def use_dev_card(card: catan.DevelopmentCard, args: catan.EventArg, player: AI):
    # check if the player is even allowed to play that card
    if player.development_cards[card] == 0:
        # dont actualy have the card
        raise ValueError("you dont have that card")
    if player.used_dev_card:
        # already played one this turn
        raise ValueError("you can only play one development card per turn")
        
    match card, args:
        case [catan.DevelopmentCard.KNIGHT, None]:
            new_robber_pos, steal_target = player.move_robber(copy_of_board()) # get the robber movement
            move_robber_and_steal(new_robber_pos, player, get_by_colour(steal_target)) # interprit the movement
            
            # give player the largest army card if they have the most knights
            player.army_size += 1
            if player.army_size >= 3:
                for ai in AI_list:
                    if ai != player:
                        if ai.army_size > player.army_size:
                            break
                
                else:
                    # no players with a larger or equal army size
                    board.largest_army = player.colour
                    print(f"{player.colour.name.lower()} got the largest army card")
                
        
        case [catan.DevelopmentCard.YEAR_OF_PLENTY, [resource_1, resource_2]] if type(resource_1) == catan.Resource and type(resource_2) == catan.Resource:
            player.resources[resource_1] += 1
            player.resources[resource_2] += 1
            
        case [catan.DevelopmentCard.ROAD_BUILDING, [pos_1, pos_2]] if type(pos_1) == int and type(pos_2) == int:
            board.place_road(player.colour, hand=None, position=pos_1)
            board.place_road(player.colour, hand=None, position=pos_2)
            
        case [catan.DevelopmentCard.MONOPOLY, resource] if type(resource) == catan.Resource:
            taken = 0
            for ai in AI_list:
                if ai != player:
                    taken += ai.resources[resource]
                    ai.resources[resource] = 0
                        
            player.resources[resource] += taken
        
        case _:
            assert ValueError("something was malformed in the args")
            # should never happen
            pass
    
    # sucess
    player.used_dev_card = True    
    player.development_cards[card] -= 1

def bank_trade(giving: catan.Hand, recieving: catan.Hand, player: AI):
    # the 1 limitation is that you cant mix & match trade types for 1 resource 
    resources = [i for i in catan.Resources()]
    
    # do 2:1, removing from list
    
    # 3:1 the rest if posible, otherwise 4:1

# MARK: start

if not HEADLESS:
    # create dpg widow
    dpg.create_context()

    # init viewport
    dpg.create_viewport(title='Catan', width=1920, height=1080)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    #dpg.toggle_viewport_fullscreen()
# create a board
board = catan.Board()

# create AIs

AI_list: list[AI] = [
    Player(catan.Colour.RED, 0) if HAS_HUMAN else CURRENT_AI(catan.Colour.RED, 0),
    CURRENT_AI(catan.Colour.ORANGE, 1),
    CURRENT_AI(catan.Colour.BLUE, 2),
    CURRENT_AI(catan.Colour.WHITE, 3),
]

ready_for_turn = True
def next_turn():
    global ready_for_turn
    ready_for_turn = True

auto_run = -1

if not HAS_HUMAN and not HEADLESS:    
    with dpg.window(label="graphs", pos= (400+39, 0)):
        dpg.add_button(label="next turn", callback=next_turn)
        auto_run = dpg.add_checkbox(label="auto")


# MARK: set-up phase
# choose starting player
update()

for player_i, settlement_num in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
    update()
    
    settlement_pos = 99999
    while 1:
        settlement_pos, road_pos = AI_list[player_i].place_starter_settlement(settlement_num, copy_of_board()) # get a move from the AI

        try:
            board.place_settlement(catan.Colour(player_i+1), hand=None, position=settlement_pos, need_road=False)
            
            if road_pos not in board.verts[settlement_pos].edges:
                raise catan.BuildingError("Not connected to correct settlement")
        
            board.place_road(catan.Colour(player_i+1), hand=None, position=road_pos)
            
        except catan.BuildingError as e:
            print(e)
            board.delete_settlement(settlement_pos)
        else:
            break

    AI_list[player_i].victory_points += 1
    if settlement_num == "second":
        # give starting resources
        resources = board.get_resources(None, settlement_pos)
        AI_list[player_i].resources = resources[AI_list[player_i].colour]

# MARK: game loop
current_turn = 0

while HEADLESS or dpg.is_dearpygui_running():
    
    if not HAS_HUMAN and not HEADLESS:
        while not ready_for_turn and not dpg.get_value(auto_run) and dpg.is_dearpygui_running():
            update()
    
    if update():
        break
    
    ready_for_turn = False
    current_AI = AI_list[current_turn]
    print(f"its {current_AI.colour.name.capitalize()}'s turn")
    
    # give the ai it's dev_cards which are on cooldown & reset if they've played one already this turn
    current_AI.used_dev_card = False
    for development_card in catan.DevelopmentCards():
        current_AI.development_cards[development_card] += current_AI.development_cards_on_cooldown[development_card]
        current_AI.development_cards_on_cooldown[development_card] = 0
    
    # check if they wish to play a dev card before rolling dice
    action = current_AI.roll_dice(copy_of_board())
    match action.event:
        case catan.Event.DICE_ROLL:
            pass
        case catan.Event.USE_KNIGHT | catan.Event.USE_MONOPOLY | catan.Event.USE_ROAD_BUILDING | catan.Event.USE_YEAR_OF_PLENTY:
            card = catan.DevelopmentCard[action.event.name.removeprefix("USE_")]
            use_dev_card(card, action.arg, current_AI)
            
        case _:
            raise ValueError(f"you cant't {action.event} before you roll the dice")

    dice = random.randint(1, 6) + random.randint(1, 6)
    print(f"{"An" if dice == 8 or dice == 11 else "A"} {dice} was rolled")
    
    if dice == 7:
        print("7 rolled")
        # hand limit of 7
        for ai in AI_list:
            if sum(ai.resources.values()) > 7:
                print(f"{ai.colour.name} has too many cards")
                
                discarded = ai.discard_half(copy_of_board())
                if sum(discarded.values()) != sum(ai.resources.values())//2:
                    raise ValueError(f"{sum(discarded.values())} is not half of your hand of {sum(ai.resources.values())}")
                
                if not catan.can_afford(ai.resources, discarded):
                    raise ValueError("you can't discard cards you don't have")
                
                for card in discarded.keys():
                    ai.resources[card] -= discarded[card]
        
        # robber
        new_robber_pos, steal_target = current_AI.move_robber(copy_of_board()) # get the robber movement
        
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
        
            ai.on_opponent_action(catan.Action(catan.Event.DICE_ROLL, dice), current_AI.colour, copy_of_board())
    
    if update():
        break
    
    while 1:
        #if DEBUG: print("\tdoing action")
        action = current_AI.do_action(copy_of_board())
        
        #print(f"\t{action.event.name}: {action.arg}")
        
        # try to do action
        try:
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
                    
                    update()
                    
                    print(f"{current_AI.colour.name}'s longest road is {board.get_longest_road(current_AI.colour)} tiles long")
                    
                case [catan.Event.BUY_DEV_CARD, None]:
                    if not catan.can_afford(current_AI.resources, catan.Building.DEVELOPMENT_CARD):
                        raise ValueError("you can't afford a developmeant card")
                    
                    current_AI.resources[catan.Resource.ORE] -= 1
                    current_AI.resources[catan.Resource.WOOL] -= 1
                    current_AI.resources[catan.Resource.GRAIN] -= 1
                    
                    
                    try:
                        # give AI a development card
                        card = board.development_cards.pop()
                        if card == catan.DevelopmentCard.VICTORY_POINT:
                            current_AI.development_cards[card] += 1
                        else:
                            current_AI.development_cards_on_cooldown[card] += 1
                    except IndexError:
                        print("no development cards left")
                
                case [catan.Event.TRADE, [giving, recieving, preferances]]:
                    if not catan.can_afford(current_AI.resources, giving):
                        raise ValueError("you cant afford that trade")
                    
                    # check with players
                    respondants = set()
                    for ai in AI_list:
                        if ai != current_AI:
                            if ai.trade(current_AI.colour, giving, recieving, copy_of_board()):
                                if not catan.can_afford(ai.resources, recieving):
                                    raise ValueError("you cant afford that trade")
                                respondants.add(ai.colour)
                    
                    # check with bank
                    if bank_trade(giving, recieving, current_AI):
                        respondants.add(catan.Colour.NONE)
                                                    
                    for player in preferances:
                        if player in respondants:
                            # both parties agreed
                            if player != catan.Colour.NONE:
                                # ai / person
                                player = get_by_colour(player)
                                for resource in catan.Resources():
                                    current_AI.resources[resource] += recieving[resource]
                                    player.resources[resource] -= recieving[resource]
                                    
                                    current_AI.resources[resource] -= giving[resource]
                                    player.resources[resource] += giving[resource]
                            else:
                                # bank
                                for resource in catan.Resources():
                                    current_AI.resources[resource] += recieving[resource]
                                    current_AI.resources[resource] -= giving[resource]
                                
                                
                                    
                
                case [catan.Event.USE_KNIGHT | catan.Event.USE_MONOPOLY | catan.Event.USE_ROAD_BUILDING |catan.Event.USE_YEAR_OF_PLENTY, _]:
                    card = catan.DevelopmentCard[action.event.name.removeprefix("USE_")]
                    use_dev_card(card, action.arg, current_AI)
                
                case _:
                    raise Exception(f"could not interprit {action} as an action")
                
        except Exception as e:
            if current_AI.is_human:
                print(e)
            else:
                raise e
        
        board.update_longest_raod()
        # if it gets to here, action was succesfull.
        # so notify players and update gui
        
        for ai in AI_list:
            if ai != current_AI:
                ai.on_opponent_action(action, ai.colour, copy_of_board())
                
        # update info pannels for each player
        
        if update():
            break

    # increment turn counter
    current_turn += 1
    current_turn %= 4
    if update():
        break

# MARK: print winner

for ai in AI_list:
    if get_real_vps(ai) >= 10:
        print(f"{ai.ansi_colour}{ai.colour.name} WON!{colours.END}")
        if board.largest_army == ai.colour:
            print("they had the largest army")
        if board.longest_road == ai.colour:
            print("they had the longest road")

if not HEADLESS:
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()