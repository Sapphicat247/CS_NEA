from src import catan
import random
import colours

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
            "dice roll": 6, # value on dice (never 7)
            "player stole from player": (catan.Colour.BLUE, catan.Colour.ORANGE), # (blue) stole from (orange)
            }

class AI:
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    victory_points: int = 0
    resources: list[catan.Resource] = []
    development_cards: list[catan.Development_card] = []
    colour: catan.Colour
    
    def __init__(self, colour: catan.Colour) -> None:
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
    
    
class AI_Random(AI):
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    
    def __init__(self, colour: catan.Colour) -> None:
        super().__init__(colour)
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        match settlement_number:
            case "first":
                return random.randint(0, 53), random.randint(0, 71) # index of vertex, edge to place settlement, road
        
            case "second":
                return random.randint(0, 53), random.randint(0, 71) # index of vertex, edge to place settlement, road
            
            case _ as e:
                raise ValueError(f"tried to place a strange starting settlement: {e}")
    
    def discard_half(self) -> list[catan.Resource]:
        to_discard = len(self.resources)//2
        discarded = []
        for _ in range(to_discard):
            discarded.append(random.choice(self.resources))
        
        return discarded
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        return random.randint(0, 18), random.choice([i for i in catan.Colour if i != self.colour])
    
    def do_action(self, board: catan.Board) -> catan.Action:
        return "end turn", None
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        ...