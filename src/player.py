from .ai import AI, AI_Random
from . import catan

import dearpygui.dearpygui as dpg

class Player(AI_Random): # TODO inherit from normal AI

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
    
    __card_selection: dict[catan.Resource, int]
    __done_card_selection = False
    board: catan.Board

    def __init__(self, colour: catan.Colour) -> None:
        super().__init__(colour)
        
        self.__card_selection = {i: 0 for i in catan.Resource if i != catan.Resource.DESERT}
        
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(callback=self.__mouse_click)
        
        self.dpg_components = self.__NamedDict()
        with dpg.window(width=300, height=400, pos=(0,0)):
            self.dpg_components.vps = dpg.add_text(f"{0} VPs")
            
            with dpg.tab_bar():
                with dpg.tab(label = "hand"):
                    dpg.add_text(f"\nresources:")
                    with dpg.table(header_row=False):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        
                        for resource in catan.Resource:
                            if resource != catan.Resource.DESERT:
                                with dpg.table_row():
                                    dpg.add_text(resource.name.lower())
                                    self.dpg_components.update({f"resource_{resource.name.lower()}": dpg.add_text("0")})
                    
                    dpg.add_text(f"\nDevelopment cards:")
                    with dpg.table(header_row=False):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        
                        for development_card in catan.Development_card:
                            if development_card != catan.Development_card.NONE:
                                
                                with dpg.table_row():
                                    dpg.add_text(development_card.name.lower().replace("_", " "))
                                    self.dpg_components.update({f"development_card_{development_card.name.lower()}": dpg.add_text("0")})
                
                with dpg.tab(label = "opponents"):
                    dpg.add_text(f"\nhands:")
                    with dpg.table():
                        dpg.add_table_column(label="player")
                        dpg.add_table_column(label="resource cards")
                        dpg.add_table_column(label="developmeant cards")
                        
                        for player in catan.Colour:
                            if player != self.colour and player != catan.Colour.NONE:
                                
                                with dpg.table_row():
                                    dpg.add_text(player.name.lower())
                                    dpg.add_text("0", tag=f"{player.name.lower()}_num_res_cards")
                                    dpg.add_text("0", tag=f"{player.name.lower()}_num_dev_cards")
                
                with dpg.tab(label = "turn", show=True, ):
                    dpg.add_button(label="roll dice")
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="build road")
                        dpg.add_button(label="build settlement")
                        dpg.add_button(label="build city")

                    dpg.add_button(label="buy development card")
                    
                    # use dev card 
                    dpg.add_button(label="trade")
                    
                    dpg.add_button(label="end turn")

        with dpg.window(width=150, height=100, show=False, tag="player selector", label="select a player", no_close=True, pos=(300,0)):
            dpg.add_button(label="Red", show=False, callback=self.__colour_selected, user_data=catan.Colour.RED, tag="red button")
            dpg.add_button(label="Orange", show=False, callback=self.__colour_selected, user_data=catan.Colour.ORANGE, tag="orange button")
            dpg.add_button(label="Blue", show=False, callback=self.__colour_selected, user_data=catan.Colour.BLUE, tag="blue button")
            dpg.add_button(label="White", show=False, callback=self.__colour_selected, user_data=catan.Colour.WHITE, tag="white button")
        
        with dpg.window(width=250, height=200, show=False, tag="card selector", label="select some cards", no_close=True, pos=(300, 0)):
            for i in catan.Resource:
                if i != catan.Resource.DESERT:
                    dpg.add_input_int(label=i.name.lower(), show=True, min_clamped=True, max_clamped=True, min_value=0, user_data=i, callback=self.__resource_changed, tag = f"{i.name.lower()} input")
            
            dpg.add_text(label="card selector text")
            
            dpg.add_button(tag="card selector button", callback=self.__resource_selection_button_clicked, label="confirm")
            
            

    def update_gui(self, board: catan.Board) -> None:
        dpg.set_value(self.dpg_components.vps, f"{self.victory_points} VPs")
        
        for resource in catan.Resource:
            if resource != catan.Resource.DESERT:
                dpg.set_value(self.dpg_components[f"resource_{resource.name.lower()}"], f"{self.resources[resource]}")
        
        for development_card in catan.Development_card:
            if development_card != catan.Development_card.NONE:
                dpg.set_value(self.dpg_components[f"development_card_{development_card.name.lower()}"], f"{self.development_cards[development_card]}")
        
        for player in catan.Colour:
            if player != self.colour and player != catan.Colour.NONE:
                dpg.set_value(f"{player.name.lower()}_num_res_cards", board.player_info[player]["res_cards"])
                dpg.set_value(f"{player.name.lower()}_num_dev_cards", board.player_info[player]["dev_cards"])
    
    def __mouse_click(self, sender, app_data):
        self.__last_click_pos = dpg.get_mouse_pos(local=False)
    
    def __get_vertex(self) -> int:
        self.__last_click_pos = None
        print("waiting for mouse click")
        while self.__last_click_pos == None:
            dpg.render_dearpygui_frame()
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2, height//2)

        hex_positions: list[tuple[float, float]] = []
        
        for vert in self.board.verts:
            # get positions
            
            p = (vert.relative_pos[0] * size + center[0], vert.relative_pos[1] * size + center[1])

            hex_positions.append(p)
        
        distances = [(x - self.__last_click_pos[0])**2 + (y - self.__last_click_pos[1])**2 for x, y in hex_positions]
        
        selected = distances.index(min(distances))
        print(f"selected: {selected}")
        return selected
    
    def __get_edge(self) -> int:
        self.__last_click_pos = None
        print("waiting for mouse click")
        while self.__last_click_pos == None:
            dpg.render_dearpygui_frame()
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2, height//2)

        edge_positions: list[tuple[float, float]] = []
        
        for edge_i, edge in enumerate(self.board.edges):
            
            p0 = (self.board.verts[edge.verts[0]].relative_pos[0]*size + center[0], self.board.verts[edge.verts[0]].relative_pos[1]*size + center[1])
            p1 = (self.board.verts[edge.verts[1]].relative_pos[0]*size + center[0], self.board.verts[edge.verts[1]].relative_pos[1]*size + center[1])
                    
            edge_positions.append(((p0[0] + p1[0])/2, (p0[1] + p1[1])/2))
        
        distances = [(x - self.__last_click_pos[0])**2 + (y - self.__last_click_pos[1])**2 for x, y in edge_positions]
        
        selected = distances.index(min(distances))
        print(f"selected: {selected}")
        return selected
    
    def __get_hex(self) -> int:
        self.__last_click_pos = None
        print("waiting for mouse click")
        while self.__last_click_pos == None:
            dpg.render_dearpygui_frame()
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2, height//2)

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
        print(f"selected: {selected}")
        return selected
    
    def __get_player(self, options: set[catan.Colour]) -> catan.Colour:
        self.__last_colour_selected = None
        dpg.show_item("player selector")
        for player in options:
            dpg.show_item(f"{player.name.lower()} button")
        print("waiting for player selection")
        
        while self.__last_colour_selected == None:
            dpg.render_dearpygui_frame()
        
        dpg.hide_item("player selector")
        for player in options:
            dpg.hide_item(f"{player.name.lower()} button")
        
        return self.__last_colour_selected
    
    def __colour_selected(self, sender, app_data, user_data: catan.Colour):
        self.__last_colour_selected = user_data
    
    def __select_cards(self, number: int = 0) -> dict[catan.Resource, int]:
        self.__done_card_selection = False
        self.__card_selection = {i: 0 for i in catan.Resource if i != catan.Resource.DESERT} # reset the card selection
        for i in catan.Resource:
            if i != catan.Resource.DESERT:
                dpg.configure_item(f"{i.name.lower()} input", max_value = self.resources[i])
                dpg.set_value(f"{i.name.lower()} input", 0)
                
        dpg.show_item("card selector")
        
        while not self.__done_card_selection:
            dpg.render_dearpygui_frame()
            
        dpg.hide_item("card selector")
        
        return self.__card_selection
    
    def __resource_changed(self, sender, app_data, user_data: catan.Resource):
        self.__card_selection[user_data] = dpg.get_value(sender)
        # calculate new maximums
        num_selected = sum(self.__card_selection.values())
        to_remove = sum(self.resources.values()) // 2
        if num_selected == to_remove:
            # selected enough
            print("enough")#dpg.enable_item("card selector button")
        else:
            print("not enough")#dpg.disable_item("card selector button")
        
        # update maximums
        missing = to_remove - num_selected
        for i in catan.Resource:
            if i != catan.Resource.DESERT:
                dpg.configure_item(f"{i.name.lower()} input", max_value = min(self.__card_selection[i] + missing, self.resources[i]))
    
    def __resource_selection_button_clicked(self, sender, app_data, user_data):
        if sum(self.__card_selection.values()) == sum(self.resources.values()) // 2:
            # selected enough cards
            self.__done_card_selection = True
    
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        self.board = board
        match settlement_number:
            case "first":
                return self.__get_vertex(), self.__get_edge() # index of vertex, edge to place settlement, road
        
            case "second":
                return self.__get_vertex(), self.__get_edge() # index of vertex, edge to place settlement, road
            
            case _ as e:
                raise ValueError(f"tried to place a strange starting settlement: {e} (this should never happen)")
    
    def discard_half(self) -> dict[catan.Resource, int]:
        return self.__select_cards()
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        self.board = board
        # called when you roll a 7 or play a knight card
        # pos, player to steal from
        options = set()
        pos = 99999999
        
        while not options:
            pos = self.__get_hex()
            
            options = {board.verts[i].structure.owner for i in board.hexes[pos].verts if board.verts[i].structure.owner != catan.Colour.NONE and board.verts[i].structure.owner != self.colour}
        
        return pos, self.__get_player(options=options)
    
    def do_action(self, board: catan.Board) -> catan.Action:
        self.board = board
        # get from the ui tab
        # enable, get action, if its and end turn, disable it
        return catan.Action(catan.Event.END_TURN, None)
    
    def trade(self, person: catan.Colour, offer: list[catan.Resource], recieve: list[catan.Resource]) -> bool:
        # show resources in a dialoge box, and have an accepr/deny button
        return False