from src import catan
import random

# 54 verts
# 72 edges
# 19 hexes

Action_options =  {
            "end turn": None,
            "build settlement": 40, # position
            "build city": 24, # position
            "build road": 68, # position
            "buy developmeant card": None,
            "use developmeant card": catan.Development_card.KNIGHT, # card
            "trade": {"give": [catan.Resource.BRICK], "recieve": [catan.Resource.WOOD]}, # trade contents
            
            # used to tell players about in-game events. e.g. dice rolling. these are never sent by AIs
            "dice roll": 6 # value on dice (never 7)
            }

class AI:
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    victory_points: int = 0
    hand: list[catan.Resource | catan.Development_card] = []
    colour: catan.Colour
    
    def __init__(self, colour: catan.Colour) -> None:
        self.colour = colour
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> dict:
        match settlement_number:
            case "first":
                return {"settlement_pos": 0, "road_pos": 0} # index of vertex, edge to place settlement, road
        
            case "second":
                return {"settlement_pos": 0, "road_pos": 0} # index of vertex, edge to place settlement, road
            
            case _ as e:
                raise ValueError(f"tried to place a strange starting settlement: {e}")
    
    def do_action(self, board: catan.Board) -> catan.Action:
        return "end turn", None
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        pass

class AI_Random(AI):
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    
    def __init__(self, colour: catan.Colour) -> None:
        super().__init__(colour)
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> dict:
        match settlement_number:
            case "first":
                return {"settlement_pos": random.randint(0, 53), "road_pos": random.randint(0, 71)} # index of vertex, edge to place settlement, road
        
            case "second":
                return {"settlement_pos": random.randint(0, 53), "road_pos": random.randint(0, 71)} # index of vertex, edge to place settlement, road
            
            case _ as e:
                raise ValueError(f"tried to place a strange starting settlement: {e}")
    
    def do_action(self, board: catan.Board) -> catan.Action:
        options =  {
            "end turn": None,
            "build settlement": 40, # position
            "build city": 24, # position
            "build road": 68, # position
            "buy developmeant card": None,
            "use developmeant card": catan.Development_card.KNIGHT, # card
            "trade": {"give": [catan.Resource.BRICK], "recieve": [catan.Resource.WOOD]}, # trade contents
            
            # used to tell players about in-game events. e.g. dice rolling. these are never sent by AIs
            "dice roll": 6 # value on dice (never 7)
            
            }
        
        return "end turn", None
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        ...