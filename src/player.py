from .ai import AI, AI_Random
from . import catan

import dearpygui.dearpygui as dpg

class Player(AI_Random):

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
                
                with dpg.tab(label = "turn", show=True):
                    dpg.add_button(label="build road")
                    dpg.add_same_line()
                    dpg.add_button(label="build settlement")
                    dpg.add_same_line()
                    dpg.add_button(label="build city")
                    dpg.add_same_line()

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