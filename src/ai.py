from src import catan

class AI:
    # basic class to build other versions off
    # AIs are trusted to not make illegal moves.
    victory_points: int = 0
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> dict:
        match settlement_number:
            case "first":
                return {"settlement_pos": 0, "road_pos": 0} # index of vertex, edge to place settlement, road
        
            case "second":
                return {"settlement_pos": 2, "road_pos": 1} # index of vertex, edge to place settlement, road
            
            case _:
                raise ValueError
    
    def have_turn(self, board: catan.Board) -> dict:
        return {"end_turn": True} # gives actions
    
    def accept_trade(self, trade: dict) -> bool:
        return False # determines weather a trade offer is good or not
    
    def on_opponent_action(self, action: dict, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board
        ...
