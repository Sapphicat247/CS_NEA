from src.ai import AI
from src import catan

import dearpygui.dearpygui as dpg

class Player(AI):

    class __NamedDict(dict):

        def __init__(self):
            super().__init__()
        
        def __getattr__(self, name: str) -> dpg.Any:
            return super().__getitem__(name)
        
        def __setattr__(self, name: str, value) -> None:
            super().__setitem__(name, value)

    dpg_components: __NamedDict
    
    __last_click_pos = None
    __last_colour_selected = None
    
    __last_pressed_event: catan.Event | None
    __monopoly_resource = None
    __yop_resources: list[catan.Resource]
    __yop_selection_done = False
    
    __card_selection: dict[catan.Resource, int]
    __done_card_selection = False
    
    __trading = False
    
    board: catan.Board
    
    def __update_screen(self):
        dpg.render_dearpygui_frame()
        if not dpg.is_dearpygui_running():
            dpg.destroy_context()

    def __init__(self, colour: catan.Colour, player_number: int) -> None:
        super().__init__(colour, player_number, False)
        
        self.__card_selection = {i: 0 for i in catan.Resources()}
        self.__yop_resources = [catan.Resource.DESERT, catan.Resource.DESERT]
        
        self.is_human = True
        
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(callback=self.__mouse_click)
        
        self.dpg_components = self.__NamedDict()
        
        main_width = 800
        main_height = 650
        
        with dpg.window(width=main_width, height=main_height, pos=(0,0), no_close=True):
            dpg.add_text(f"{0} VPs", tag="player_vps_and_info")
            
            with dpg.tab_bar():
                with dpg.tab(label = "Hand"):
                    dpg.add_text(f"\nresources:")
                    with dpg.table(header_row=False):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        
                        for resource in catan.Resources():
                            with dpg.table_row():
                                dpg.add_text(resource.name.lower())
                                self.dpg_components.update({f"resource_{resource.name.lower()}": dpg.add_text("0")})
                    
                    dpg.add_text(f"\nDevelopment cards:")
                    with dpg.table(header_row=False):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        
                        for development_card in catan.DevelopmentCards():
                            with dpg.table_row():
                                dpg.add_text(development_card.name.lower().replace("_", " "))
                                self.dpg_components.update({f"development_card_{development_card.name.lower()}": dpg.add_text("0")})
                
                with dpg.tab(label = "Opponents"):
                    with dpg.table():
                        dpg.add_table_column(label="player")
                        dpg.add_table_column(label="resource cards")
                        dpg.add_table_column(label="developmeant cards")
                        
                        for player in catan.Colours():
                            with dpg.table_row():
                                with dpg.group(horizontal=True):
                                    dpg.add_text(player.name.lower())
                                    dpg.add_text("", tag=f"{player.name.lower()}_extras")
                                dpg.add_text("0", tag=f"{player.name.lower()}_num_res_cards")
                                dpg.add_text("0", tag=f"{player.name.lower()}_num_dev_cards")
                
                with dpg.tab(label = "Turn", show=True, ):
                    dpg.add_button(label="Roll Dice", callback=self.__gui_button_pressed, user_data=catan.Event.DICE_ROLL)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Build Road", callback=self.__gui_button_pressed, user_data=catan.Event.BUILD_ROAD)
                        dpg.add_button(label="Build Settlement", callback=self.__gui_button_pressed, user_data=catan.Event.BUILD_SETTLEMENT)
                        dpg.add_button(label="Build City", callback=self.__gui_button_pressed, user_data=catan.Event.BUILD_CITY)

                    dpg.add_button(label="buy development card", callback=self.__gui_button_pressed, user_data=catan.Event.BUY_DEV_CARD)
                    dpg.add_text("use development card: ")
                    with dpg.group(horizontal=True):
                        for i in catan.DevelopmentCard:
                            if i != catan.DevelopmentCard.NONE and i != catan.DevelopmentCard.VICTORY_POINT:
                                dpg.add_button(label=f"{i.name.lower().replace("_", " ").capitalize()}", callback=self.__gui_button_pressed, user_data=catan.Event[f"USE_{i.name}"])

                    dpg.add_button(label="trade", callback=self.__gui_button_pressed, user_data=catan.Event.TRADE)
                    
                    dpg.add_button(label="end turn", callback=self.__gui_button_pressed, user_data=catan.Event.END_TURN)

        with dpg.window(width=main_width, height=600, pos=(0,main_height), no_close=True):
            dpg.add_text(tag="text output box", tracked=True, wrap=main_width, track_offset=1)
        
        with dpg.window(width=150, height=100, show=False, tag="player selector", label="select a player", no_close=True, pos=(main_width,0)):
            dpg.add_button(label="Red", show=False, callback=self.__colour_selected, user_data=catan.Colour.RED, tag="red button")
            dpg.add_button(label="Orange", show=False, callback=self.__colour_selected, user_data=catan.Colour.ORANGE, tag="orange button")
            dpg.add_button(label="Blue", show=False, callback=self.__colour_selected, user_data=catan.Colour.BLUE, tag="blue button")
            dpg.add_button(label="White", show=False, callback=self.__colour_selected, user_data=catan.Colour.WHITE, tag="white button")
        
        with dpg.window(width=250, height=200, show=False, tag="card selector", label="select some cards", no_close=True, pos=(main_width, 0)):
            for i in catan.Resources():
                dpg.add_input_int(label=i.name.lower(), show=True, min_clamped=True, max_clamped=True, min_value=0, user_data=i, callback=self.__resource_changed, tag = f"{i.name.lower()} input")
            
            dpg.add_text(label="card selector text")
            
            dpg.add_button(tag="card selector button", callback=self.__resource_selection_button_clicked, label="confirm")
        
        with dpg.window(width=250, height=200, show=False, tag="monopoly selector", label="select a resoruce type", no_close=True, pos=(main_width, 0)):
            
            for i in catan.Resources():
                dpg.add_button(label=i.name.lower(), show=True, user_data=i, callback=self.__monopoly_button_pressed)
        
        with dpg.window(width=250, height=200, show=False, tag="yop selector", label="select a resoruce type", no_close=True, pos=(main_width, 0)):
            
            for i in catan.Resources():
                with dpg.group(horizontal=True):
                    dpg.add_text(i.name.lower())
                    dpg.add_checkbox(user_data=(0, i), callback=self.__yop_button_pressed, tag=f"{i.name.lower()} checkbox 0")
                    dpg.add_checkbox(user_data=(1, i), callback=self.__yop_button_pressed, tag=f"{i.name.lower()} checkbox 1")
            
            dpg.add_button(tag="finished_yop_selection_button", callback=self.__yop_button_pressed, label="confirm", user_data=(None, catan.Resource.DESERT)) # desert = send button
        

    def update_gui(self, board: catan.Board) -> None:
        dpg.set_value("player_vps_and_info", f"{self.victory_points} VPs {"(K) " if board.largest_army == self.colour else ""}{"(R)" if board.longest_road == self.colour else ""}")
        
        for resource in catan.Resources():
            dpg.set_value(self.dpg_components[f"resource_{resource.name.lower()}"], f"{self.resources[resource]}")
        
        for development_card in catan.DevelopmentCards():
            dpg.set_value(self.dpg_components[f"development_card_{development_card.name.lower()}"], f"{self.development_cards[development_card] + self.development_cards_on_cooldown[development_card]}")
        
        for player in catan.Colour:
            if player != self.colour and player != catan.Colour.NONE:
                dpg.set_value(f"{player.name.lower()}_num_res_cards", board.player_info[player]["res_cards"])
                dpg.set_value(f"{player.name.lower()}_num_dev_cards", board.player_info[player]["dev_cards"])
                dpg.set_value(f"{player.name.lower()}_extras", ("(K) " if board.largest_army == player else "") + ("(R)" if board.longest_road == player else ""))
    
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        self.board = board
        match settlement_number:
            case "first":
                dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\nplace your first settlement")
                return self.__get_vertex(), self.__get_edge() # index of vertex, edge to place settlement, road
        
            case "second":
                dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\nplace your second settlement")
                return self.__get_vertex(), self.__get_edge() # index of vertex, edge to place settlement, road
            
            case _ as e:
                raise ValueError(f"tried to place a strange starting settlement number {e} (this should never happen)")
    
    def discard_half(self, board: catan.Board) -> dict[catan.Resource, int]:
        dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "discard half your hand")
        return self.__select_cards()
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        self.board = board
        # called when you roll a 7 or play a knight card
        # pos, player to steal from
        options = set()
        pos = None
        
        while not options:
            dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "chose a location for the robber to move to")
            pos = self.__get_hex()
            if pos == board.robber_pos:
                continue # invalid
            
            options = {board.verts[i].structure.owner for i in board.hexes[pos].verts if board.verts[i].structure.owner != catan.Colour.NONE and board.verts[i].structure.owner != self.colour}
        
        assert pos is not None
        dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "chose a player")
        return pos, self.__get_player(options=options)
    
    def roll_dice(self, board: catan.Board) -> catan.Action:
        self.board = board
        self.__last_pressed_event = None
        
        dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "It's the start of your turn, you may play a development card before rolling the dice")
        
        if sum(v for k, v in self.development_cards.items() if k != catan.DevelopmentCard.VICTORY_POINT) > 0:
            # has a development card
            ...
        while 1:
            self.__last_pressed_event = None
            # wait for button click
            while self.__last_pressed_event == None:
                self.__update_screen()
            
            # check it was valid
            match self.__last_pressed_event:
                case catan.Event.DICE_ROLL:
                    break
                
                case catan.Event.USE_KNIGHT:
                    return catan.Action(catan.Event.USE_KNIGHT, None)
                case catan.Event.USE_MONOPOLY:
                    return catan.Action(catan.Event.USE_MONOPOLY, self.__get_monopoly_resource())
                case catan.Event.USE_YEAR_OF_PLENTY:
                    return catan.Action(catan.Event.USE_YEAR_OF_PLENTY, self.__get_yop_resources())
                case catan.Event.USE_ROAD_BUILDING:
                    return catan.Action(catan.Event.USE_ROAD_BUILDING, (self.__get_edge(), self.__get_edge()))
                
        return catan.Action(catan.Event.DICE_ROLL, None)
        
        
    
    def do_action(self, board: catan.Board) -> catan.Action:
        self.board = board
        self.__last_pressed_event = None
        dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "It's your turn, have an action")
        while self.__last_pressed_event == None:
            self.__update_screen()
        
        # button pressed
        # get specific input for the action
        
        match self.__last_pressed_event:
            # events with no argument
            case catan.Event.END_TURN | catan.Event.BUY_DEV_CARD | catan.Event.USE_KNIGHT as event:
                return catan.Action(event, None)
            
            # place building
            case catan.Event.BUILD_CITY | catan.Event.BUILD_SETTLEMENT as event:
                return catan.Action(event, self.__get_vertex())
            case catan.Event.BUILD_ROAD:
                return catan.Action(catan.Event.BUILD_ROAD, self.__get_edge())
            
            # use dev card
            case catan.Event.USE_MONOPOLY:
                return catan.Action(catan.Event.USE_MONOPOLY, self.__get_monopoly_resource())
            case catan.Event.USE_YEAR_OF_PLENTY:
                return catan.Action(catan.Event.USE_YEAR_OF_PLENTY, self.__get_yop_resources())
            case catan.Event.USE_ROAD_BUILDING:
                return catan.Action(catan.Event.USE_ROAD_BUILDING, (self.__get_edge(), self.__get_edge()))
            
            case catan.Event.TRADE:
                dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "trading may or may not work")
                # print("select the cards you want")
                # recieve = self.__select_cards(limits = False)
                # print("select the cards you would like to recieve")
                # offer = self.__select_cards(limits = False)
                # return catan.Action(catan.Event.TRADE, (offer, recieve, [catan.Colour.NONE]))
            
            case _:
                print("idk...")
        
        
        return catan.Action(self.__last_pressed_event, None)
    
    def trade(self, person: catan.Colour, offer: catan.Hand, recieve: catan.Hand, board: catan.Board) -> bool:
        # show resources in a dialoge box, and have an accept/deny button
        
        return False
    
    def __gui_button_pressed(self, sender, app_data, user_data):
        self.__last_pressed_event = user_data # update the flag
    
    def __mouse_click(self, sender, app_data):
        self.__last_click_pos = dpg.get_mouse_pos(local=False)
    
    def __get_vertex(self) -> int:
        self.__last_click_pos = None
        print("waiting for vertex click...")
        while self.__last_click_pos == None:
            self.__update_screen()
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2 + 4*abs(size-horizontal_size), height//2)

        hex_positions: list[tuple[float, float]] = []
        
        for vert in self.board.verts:
            # get positions
            
            p = (vert.relative_pos[0] * size + center[0], vert.relative_pos[1] * size + center[1])

            hex_positions.append(p)
        
        distances = [(x - self.__last_click_pos[0])**2 + (y - self.__last_click_pos[1])**2 for x, y in hex_positions]
        
        selected = distances.index(min(distances))
        return selected
    
    def __get_edge(self) -> int:
        self.__last_click_pos = None
        print("waiting for edge click...")
        while self.__last_click_pos == None:
            self.__update_screen()
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2 + 4*abs(size-horizontal_size), height//2)

        edge_positions: list[tuple[float, float]] = []
        
        for edge_i, edge in enumerate(self.board.edges):
            
            p0 = (self.board.verts[edge.verts[0]].relative_pos[0]*size + center[0], self.board.verts[edge.verts[0]].relative_pos[1]*size + center[1])
            p1 = (self.board.verts[edge.verts[1]].relative_pos[0]*size + center[0], self.board.verts[edge.verts[1]].relative_pos[1]*size + center[1])
                    
            edge_positions.append(((p0[0] + p1[0])/2, (p0[1] + p1[1])/2))
        
        distances = [(x - self.__last_click_pos[0])**2 + (y - self.__last_click_pos[1])**2 for x, y in edge_positions]
        
        selected = distances.index(min(distances))
        return selected
    
    def __get_hex(self) -> int:
        self.__last_click_pos = None
        print("waiting for hex click...")
        while self.__last_click_pos == None:
            self.__update_screen()
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2 + 4*abs(size-horizontal_size), height//2)

        hex_positions: list[tuple[float, float]] = []
        
        for hex in self.board.hexes:
            # get positions
            p0 = self.board.verts[hex.verts[0]].relative_pos
            p1 = self.board.verts[hex.verts[3]].relative_pos
            
            p0 = [p0[0] * size + center[0], p0[1] * size + center[1]]
            p1 = [p1[0] * size + center[0], p1[1] * size + center[1]]

            hex_positions.append(((p0[0] + p1[0])/2, (p0[1] + p1[1])/2))
        
        distances = [(x - self.__last_click_pos[0])**2 + (y - self.__last_click_pos[1])**2 for x, y in hex_positions]
        
        selected = distances.index(min(distances))
        return selected
    
    def __get_player(self, options: set[catan.Colour]) -> catan.Colour:
        self.__last_colour_selected = None
        dpg.show_item("player selector")
        for player in options:
            dpg.show_item(f"{player.name.lower()} button")
        dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "waiting for player selection")
        
        while self.__last_colour_selected == None:
            self.__update_screen()
        
        dpg.hide_item("player selector")
        for player in options:
            dpg.hide_item(f"{player.name.lower()} button")
        
        return self.__last_colour_selected
    
    def __colour_selected(self, sender, app_data, user_data: catan.Colour):
        self.__last_colour_selected = user_data
    
    def __select_cards(self, number: int = 0, limits: bool = True) -> dict[catan.Resource, int]:
        self.__done_card_selection = False
        self.__card_selection = {i: 0 for i in catan.Resources()} # reset the card selection
        for i in catan.Resources():
            dpg.configure_item(f"{i.name.lower()} input", max_value = self.resources[i] if limits else 10)
            dpg.set_value(f"{i.name.lower()} input", 0)

        if not limits:
            self.__trading = True
        dpg.show_item("card selector")
        
        while not self.__done_card_selection:
            self.__update_screen()
            
        dpg.hide_item("card selector")
        self.__trading = False
        return self.__card_selection
    
    def __resource_changed(self, sender, app_data, user_data: catan.Resource):
        self.__card_selection[user_data] = dpg.get_value(sender)
        # calculate new maximums
        if not self.__trading:
            num_selected = sum(self.__card_selection.values())
            to_remove = sum(self.resources.values()) // 2
            if num_selected == to_remove:
                # selected enough
                dpg.set_value("text output box", str(dpg.get_value("text output box")) + "\n" + "you have selected enough cards")
            else:
                print("not enough")
        
            # update maximums
            missing = to_remove - num_selected
            for i in catan.Resources():
                dpg.configure_item(f"{i.name.lower()} input", max_value = min(self.__card_selection[i] + missing, self.resources[i]))
    
    def __resource_selection_button_clicked(self, sender, app_data, user_data):
        if (not self.__trading) or sum(self.__card_selection.values()) == sum(self.resources.values()) // 2:
            # selected enough cards
            self.__done_card_selection = True
    
    def __monopoly_button_pressed(self, sender, app_data, user_data):
        self.__monopoly_resource = user_data
    
    def __get_monopoly_resource(self):
        self.__monopoly_resource = None
        dpg.show_item("monopoly selector")
        
        while self.__monopoly_resource is None:
            self.__update_screen()
        
        dpg.hide_item("monopoly selector")
        return self.__monopoly_resource
    
    def __yop_button_pressed(self, sender, app_data, user_data: tuple[int, catan.Resource]):
        if user_data[1] == catan.Resource.DESERT:
            # only done if both resources are selected
            self.__yop_selection_done = catan.Resource.DESERT not in self.__yop_resources
        
        else:
            # reset other boxes in that column
            for i in catan.Resource:
                if i != catan.Resource.DESERT and i != user_data[1]:
                    dpg.set_value(f"{i.name.lower()} checkbox {user_data[0]}", False)
            
            
            self.__yop_resources[user_data[0]] = user_data[1]
    
    def __get_yop_resources(self):
        # reset
        self.__yop_resources = [catan.Resource.DESERT, catan.Resource.DESERT]
        self.__yop_selection_done = False
        
        dpg.show_item("yop selector")
        
        while not self.__yop_selection_done:
            self.__update_screen()
        
        dpg.hide_item("yop selector")
        
        return tuple(self.__yop_resources)
        
        