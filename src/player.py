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

    def __init__(self, colour: catan.Colour) -> None:
        super().__init__(colour)
        self.dpg_components = self.__NamedDict()
        with dpg.window(width=300, height=400):
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
                
                with dpg.tab(label = "turn", show=True, ):
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="build road")
                        dpg.add_button(label="build settlement")
                        dpg.add_button(label="build city")

                    dpg.add_button(label="buy development card")
                    
                    # use dev card 
                    dpg.add_button(label="trade")
                    
                    dpg.add_button(label="end turn")

    def update_gui(self) -> None:
        dpg.set_value(self.dpg_components.vps, f"{self.victory_points} VPs")
        
        for resource in catan.Resource:
            if resource != catan.Resource.DESERT:
                dpg.set_value(self.dpg_components[f"resource_{resource.name.lower()}"], f"{self.resources[resource]}")
        
        for development_card in catan.Development_card:
            if development_card != catan.Development_card.NONE:
                dpg.set_value(self.dpg_components[f"development_card_{development_card.name.lower()}"], f"{self.development_cards[development_card]}")
    
    def __get_vertex(self) -> int:
        ...
    
    def __get_edge(self) -> int:
        ...
    
    def __get_hex(self) -> int:
        ...
    
    def __select_cards(self) -> dict[catan.Resource, int]:
        ...
    
    def __get_player(self, options: list[catan.Colour]) -> catan.Colour:
        ...
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
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
        # called when you roll a 7 or play a knight card
        # pos, player to steal from
        pos = self.__get_hex()
        return pos, self.__get_player(options=[board.verts[i].structure.owner for i in board.hexes[pos].verts])
    
    def do_action(self, board: catan.Board) -> catan.Action:
        # get from the ui tab
        # enable, get action, if its and end turn, disable it
        return catan.Action(catan.Event.END_TURN, None)
    
    def trade(self, person: catan.Colour, offer: list[catan.Resource], recieve: list[catan.Resource]) -> bool:
        # show resources in a dialoge box, and have an accepr/deny button
        return False