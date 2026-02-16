from src import catan
from src.ai import AI, AI_V1
from src.player import Player

import dearpygui.dearpygui as dpg
import random, time, sys

if "-h" in sys.argv or "--help" in sys.argv:
    print("[-h, --help] [-d, --debug] [--onlyAIs] [--noGUI]")
    sys.exit(0)

# Change these to test software
HAS_HUMAN = "--onlyAIs" not in sys.argv # include player?
HEADLESS = "--noGUI" in sys.argv # draw GUI?

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
    #b = board.safe_copy()
    #b.player_info = {i: {"res_cards": sum(get_by_colour(i).resources.values()), "dev_cards": sum(get_by_colour(i).development_cards.values()) + sum(get_by_colour(i).development_cards_on_cooldown.values())} for i in catan.Colours()}
    
    return board

def update() -> bool:
    """update GUI"""
    if not HEADLESS:
        board.draw()
        dpg.render_dearpygui_frame()
        
    max_vps = 0
    for ai in AI_list:
        if not HAS_HUMAN or ai.is_human:
            ai.update_gui(copy_of_board())
        
        vps = get_real_vps(ai)
        max_vps = max(max_vps, vps)
        if vps >= 10:
            return True
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
                    if catan.DEBUG: print(f"\t{player.colour.name.lower()} got the largest army card")
                    if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"{player.colour.name.lower()} got the largest army card")
                
        
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

def bank_trade(giving: dict[catan.Resource, int], recieving: dict[catan.Resource, int], player: AI):
    # the 1 limitation is that you cant mix & match trade types for 1 resource
    
    avaliable: dict[catan.Resource, int | float] = {k: v for k, v in giving.items()}
    
    ports = set()
    for vert in board.verts:
        if vert.structure.owner == player.colour:
            for edge_i in vert.edges:
                if edge_i is not None and (port := board.edges[edge_i].port) is not None:
                    ports.add(port.resource)
    
    for resource in ports:
        if resource != catan.Resource.DESERT:
            avaliable[resource] /= 2
    
    rate = 3 if catan.Resource.DESERT in ports else 4
    
    for resource in catan.Resources():
        if resource not in ports:
            avaliable[resource] /= rate
    
    return all(i == int(i) for i in avaliable.values()) and sum(avaliable.values()) == sum(recieving.values())

board: catan.Board
AI_list: list[AI]

def main(print_output: bool = True):
    # MARK: start
    start_time = time.time()

    if not HEADLESS:
        # create dpg widow
        dpg.create_context()

        # init viewport
        dpg.create_viewport(title='Catan', width=2560, height=1440)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        dpg.set_global_font_scale(2)
        #dpg.toggle_viewport_fullscreen()
        
    # create a board
    global board
    board = catan.Board()

    # create AIs

    global AI_list
    AI_list = [
        Player(catan.Colour.RED, 0) if HAS_HUMAN else AI_V1(catan.Colour.RED, 0),
        AI_V1(catan.Colour.ORANGE, 1, draw_gui = not HAS_HUMAN),
        AI_V1(catan.Colour.BLUE, 2, draw_gui = not HAS_HUMAN),
        AI_V1(catan.Colour.WHITE, 3, draw_gui = not HAS_HUMAN),
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
    update()
    update()

    for player_i, settlement_num in ((0, "first"), (1, "first"), (2, "first"), (3, "first"), (3, "second"), (2, "second"), (1, "second"), (0, "second")):
        update()
        
        settlement_pos = 99999
        while 1:
            settlement_pos, road_pos = AI_list[player_i].place_starter_settlement(settlement_num, copy_of_board()) # get a move from the AI
            test_board = board.safe_copy()
            try:
                test_board.place_settlement(catan.Colour(player_i+1), hand=None, position=settlement_pos, need_road=False)
                
                if road_pos not in board.verts[settlement_pos].edges:
                    raise catan.BuildingError("Not connected to correct settlement")
            
                test_board.place_road(catan.Colour(player_i+1), hand=None, position=road_pos)
                
            except catan.BuildingError as e:
                if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + str(e))
            else:
                board.place_settlement(catan.Colour(player_i+1), hand=None, position=settlement_pos, need_road=False)
                board.place_road(catan.Colour(player_i+1), hand=None, position=road_pos)
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
        if catan.DEBUG: print(f"its {current_AI.colour.name.capitalize()}'s turn")
        if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"its {current_AI.colour.name.capitalize()}'s turn")
        
        # give the ai it's dev_cards which are on cooldown & reset if they've played one already this turn
        current_AI.used_dev_card = False
        for development_card in catan.DevelopmentCards():
            current_AI.development_cards[development_card] += current_AI.development_cards_on_cooldown[development_card]
            current_AI.development_cards_on_cooldown[development_card] = 0
        
        # check if they wish to play a dev card before rolling dice
        while 1:
            action = current_AI.roll_dice(copy_of_board())
            try:
                match action.event:
                    case catan.Event.DICE_ROLL:
                        pass
                    case catan.Event.USE_KNIGHT | catan.Event.USE_MONOPOLY | catan.Event.USE_ROAD_BUILDING | catan.Event.USE_YEAR_OF_PLENTY:
                        card = catan.DevelopmentCard[action.event.name.removeprefix("USE_")]
                        use_dev_card(card, action.arg, current_AI)
                        
                    case _:
                        raise ValueError(f"you cant't {action.event} before you roll the dice")
                    
            except Exception as e:
                if current_AI.is_human:
                    if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"{e}")
                else:
                    raise e
            
            else:
                break

        dice = random.randint(1, 6) + random.randint(1, 6)
        if catan.DEBUG: print(f"\t{"An" if dice == 8 or dice == 11 else "A"} {dice} was rolled")
        if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"{"An" if dice == 8 or dice == 11 else "A"} {dice} was rolled")
        
        if dice == 7:
            # hand limit of 7
            for ai in AI_list:
                if sum(ai.resources.values()) > 7:
                    if catan.DEBUG: print(f"\t\t{ai.colour.name} has too many cards")
                    if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"{ai.colour.name} has too many cards")
                    
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
            for ai in AI_list:
                for resource in resources[ai.colour].keys():
                    ai.resources[resource] += resources[ai.colour][resource]
            
                ai.on_opponent_action(catan.Action(catan.Event.DICE_ROLL, dice), current_AI.colour, copy_of_board())
        
        if update():
            break
        
        while 1:
            action = current_AI.do_action(copy_of_board())
            
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
                            if catan.DEBUG: print("\nError: no development cards left")
                            if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "no development cards left")
                    
                    case [catan.Event.TRADE, [giving, recieving, preferances]]:
                        if not catan.can_afford(current_AI.resources, giving):
                            raise ValueError("you cant afford that trade")
                        
                        for person in preferances:
                            if person == catan.Colour.NONE and bank_trade(giving, recieving, current_AI):
                                # asked to use bank & is valid
                                for resource in catan.Resources():
                                    current_AI.resources[resource] += recieving[resource]
                                    current_AI.resources[resource] -= giving[resource]
                                break
                            
                            for other_ai in AI_list:
                                if other_ai != current_AI and other_ai.trade(current_AI.colour, giving, recieving, copy_of_board()):
                                    # player & they agreed
                                    if not catan.can_afford(other_ai.resources, recieving):
                                        raise ValueError(f"{other_ai.colour.name.capitalize()} cant afford that trade")
                                    
                                    if catan.DEBUG: print(f"\t{current_AI.colour.name.capitalize()} traded with {other_ai.colour.name.capitalize()}")
                                    if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"{current_AI.colour.name.capitalize()} traded with {other_ai.colour.name.capitalize()}")
                                    
                                    # they can afford it
                                    for resource in catan.Resources():
                                        current_AI.resources[resource] += recieving[resource]
                                        other_ai.resources[resource] -= recieving[resource]
                                        
                                        current_AI.resources[resource] -= giving[resource]
                                        other_ai.resources[resource] += giving[resource]
                                    break
                                
                            # if the inner loop exited early, break agian, else do nothing
                            else:
                                continue
                            break        
                    
                    case [catan.Event.USE_KNIGHT | catan.Event.USE_MONOPOLY | catan.Event.USE_ROAD_BUILDING |catan.Event.USE_YEAR_OF_PLENTY, _]:
                        card = catan.DevelopmentCard[action.event.name.removeprefix("USE_")]
                        use_dev_card(card, action.arg, current_AI)
                    
                    case _:
                        raise Exception(f"could not interprit {action} as an action")
                    
            except Exception as e:
                if current_AI.is_human:
                    if catan.DEBUG: print(f"\tError: {e}")
                    if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + str(e))
                else:
                    raise e
            
            board.update_longest_road()
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

    # MARK: End
    winner = "NONE"

    for ai in AI_list:
        if get_real_vps(ai) >= 10:
            winner = ai.colour.name
            if catan.DEBUG:
                print(f"{ai.colour.name} {"(K) " if board.largest_army == ai else ""}{("(R) " if board.longest_road == ai else "")}WON!")
            else:
                print(f"{ai.colour.name} WON!")
                
            if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + f"{ai.colour.name} WON!")
            if board.largest_army == ai.colour:
                if catan.DEBUG: print("they had the largest army")
                if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "they had the largest army")
            if board.longest_road == ai.colour:
                if catan.DEBUG: print("they had the longest road")
                if HAS_HUMAN: dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "they had the longest road")

    if not HEADLESS:
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()

    runtime = time.time() - start_time

    print("execution took %s seconds" % (runtime))
    return winner, runtime

if __name__ == "__main__":
    main(print_output = True)