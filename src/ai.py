class AI:
    # basic class to build other versions off
    # AIs are trusted to not make illegal moves.
    victory_points: int = 0
    
    def place_first_settlement(self) -> tuple[int, int]:
        return 0, 0 # index of vertex, edge to place settlement, road

    def place_second_settlement(self) -> tuple[int, int]:
        return 0, 0 # index of vertex, edge to place settlement, road
    
    def have_turn(self) -> ...:
        ...
