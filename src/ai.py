from src import catan
import random
import colours
import dearpygui.dearpygui as dpg

# 54 verts
# 72 edges
# 19 hexes

Action_options =  {
            "end turn": None,
            "build settlement": 40, # position
            "build city": 24, # position
            "build road": 68, # position
            "buy developmeant card": None,
            "use developmeant card": (catan.Development_card.KNIGHT, {"pos": 6, "steal": catan.Colour.RED}), # card
            "trade": {"give": [catan.Resource.BRICK], "recieve": [catan.Resource.WOOD]}, # trade contents
            
            # used to tell players about in-game events. e.g. dice rolling. these are never sent by AIs
            "dice roll": 6, # value on dice (never 7)
            "player stole from player": (catan.Colour.BLUE, catan.Colour.ORANGE), # (blue) stole from (orange)
            "player discarded": {"player": catan.Colour.RED, "resources": [catan.Resource.BRICK, catan.Resource.ORE]}
            }

development_card_options= [
    (catan.Development_card.KNIGHT, {"pos": 6, "steal": catan.Colour.RED}),
    (catan.Development_card.MONOPOLY, {"resource": catan.Resource.WOOD}),
    (catan.Development_card.ROAD_BUILDING, {"pos 1": 7, "pos 2": 8}),
    (catan.Development_card.YEAR_OF_PLENTY, {"resource 1": catan.Resource.WOOD, "resource 2": catan.Resource.GRAIN})
]

class AI:
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    victory_points: int
    resources: list[catan.Resource]
    development_cards: list[catan.Development_card]
    colour: catan.Colour
    ansi_colour: str
    
    def __init__(self, colour: catan.Colour) -> None:
        self.victory_points = 0
        self.resources = []
        self.development_cards = []
        self.colour = colour
        
        self.ansi_colour = {
            catan.Colour.RED: colours.fg.RED,
            catan.Colour.ORANGE: colours.fg.ORANGE,
            catan.Colour.BLUE: colours.fg.BLUE,
            catan.Colour.WHITE: colours.fg.WHITE,
        }[self.colour] + colours.bg.RGB(0, 0, 0)
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        match settlement_number:
            case "first":
                return 0, 0 # index of vertex, edge to place settlement, road
        
            case "second":
                return 0, 0 # index of vertex, edge to place settlement, road
            
            case _ as e:
                raise ValueError(f"tried to place a strange starting settlement: {e}")
    
    def discard_half(self) -> list[catan.Resource]:
        to_discard = len(self.resources)//2
        
        return self.resources[0:to_discard]
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        # called when you roll a 7 or play a knight card
        # pos, player to steal from
        return 0, catan.Colour.NONE
    
    def do_action(self, board: catan.Board) -> catan.Action:
        return "end turn", None
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        pass
    
    def gui_setup(self):
        # called at the start, can be used to display custom fields
        pass
     
class AI_Random(AI):
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    opponent_hands: dict[catan.Colour, list[catan.Resource]] = {}
    
    def __init__(self, colour: catan.Colour) -> None:
        super().__init__(colour)
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        # get settlement position:
        settlement_pos = random.randint(0, 53) # get random position
        while not board.can_place(catan.Building.SETTLEMENT, self.colour, None, settlement_pos, need_road=False): # if it's occupied, try again
            settlement_pos = random.randint(0, 53) # get random position
        
        # get road pos by choosing a random edges on the selectd vertex
        road_pos = random.choice([i for i in board.verts[settlement_pos].edges if i != None])

        return settlement_pos, road_pos
    
    def discard_half(self) -> list[catan.Resource]:
        return random.sample(self.resources, len(self.resources)//2)
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        
        robber_pos = random.randint(0, 18)
        while robber_pos == board.get_robber_pos():
            robber_pos = random.randint(0, 18)
            
        adj_players = [board.verts[i].structure.owner for i in board.hexes[robber_pos].verts] # get all players adjacent to that hex
        adj_players = [i for i in adj_players if i != catan.Colour.NONE and i != self.colour] # eliminate empty spots and yourself
        
        if adj_players == []:
            adj_players = [catan.Colour.NONE]

        return robber_pos, random.choice(adj_players)
    
    def __get_position_options(self, building: catan.Building, board: catan.Board) -> list[int] | set[int]:
        match building:
            case catan.Building.CITY | catan.Building.SETTLEMENT | catan.Building.ROAD:
                return {i for i in range(len(board.verts)) if board.can_place(building, self.colour, self.resources, i)}
            
            case catan.Building.DEVELOPMENT_CARD:
                raise ValueError("you can't 'place' a development card")
            
            case _:
                raise ValueError(f"{building} is not a valid building")

    
    def do_action(self, board: catan.Board) -> catan.Action:
        # try to build something if you can afford it
        for building in (catan.Building.CITY, catan.Building.SETTLEMENT, catan.Building.ROAD):
            if options := self.__get_position_options(building, board):
                return f"build {building.name.lower()}", random.choice(list(options))
        
        if catan.can_afford(self.resources, catan.Building.DEVELOPMENT_CARD) and len(board.development_cards) > 0:
            return f"buy developmeant card", None
            
        # try to use a development card if you have one
        
        return "end turn", None
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        ...
    
    def gui_setup(self):
        # called at the start, can be used to display custom fields
        pass