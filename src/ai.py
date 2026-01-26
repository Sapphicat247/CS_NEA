from src import catan
import random
import colours
import dearpygui.dearpygui as dpg
from typing import Literal

class AI:
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    victory_points: int
    resources: dict[catan.Resource, int]
    development_cards: dict[catan.DevelopmentCard, int]
    development_cards_on_cooldown: dict[catan.DevelopmentCard, int]
    colour: catan.Colour
    ansi_colour: str
    army_size: int
    used_dev_card: bool
    is_human: bool
    
    def __init__(self, colour: catan.Colour) -> None:
        self.victory_points = 0
        self.resources = {i: 0 for i in catan.Resource if i != catan.Resource.DESERT}
        self.development_cards = {i: 0 for i in catan.DevelopmentCard if i != catan.DevelopmentCard.NONE}
        self.development_cards_on_cooldown = {i: 0 for i in catan.DevelopmentCard if i != catan.DevelopmentCard.NONE}
        self.colour = colour
        
        self.army_size = 0
        self.used_dev_card = False
        self.is_human = False
        
        self.ansi_colour = {
            catan.Colour.RED: colours.fg.RED,
            catan.Colour.ORANGE: colours.fg.ORANGE,
            catan.Colour.BLUE: colours.fg.BLUE,
            catan.Colour.WHITE: colours.fg.WHITE,
        }[self.colour] + colours.bg.RGB(0, 0, 0)
    
    def update_gui(self, board: catan.Board) -> None:
        ...

    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        ...
    
    def discard_half(self) -> dict[catan.Resource, int]:
        ...
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        # called when you roll a 7 or play a knight card
        # pos, player to steal from
        ...
    
    def roll_dice(self, board: catan.Board) -> catan.Action:
        ...
    
    def do_action(self, board: catan.Board) -> catan.Action:
        ...
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        ...
    
    def trade(self, person: catan.Colour, offer: catan.Hand, recieve: catan.Hand) -> bool:
        # does this ai want to accept a deal from another player?
        ...
    
    def __eq__(self, other):
        return self.colour == other.colour
     
class AI_Random(AI):
    # basic class to build other versions off
    # AIs are not trusted to make legal moves, however the AI will have to avoid infinite loops by always attempting an illegal move
    opponent_hands: dict[catan.Colour, list[catan.Resource]] = {}
    
    def __init__(self, colour: catan.Colour) -> None:
        super().__init__(colour)
    
    def place_starter_settlement(self, settlement_number: str, board: catan.Board) -> tuple[int, int]:
        # get settlement position:
        settlement_pos = random.randint(0, 53) # get random position
        while not board.can_place(catan.Building.SETTLEMENT, self.colour, hand=None, position=settlement_pos, need_road=False): # if it's occupied, try again
            settlement_pos = random.randint(0, 53) # get random position
        
        # get road pos by choosing a random edges on the selectd vertex
        road_pos = random.choice([i for i in board.verts[settlement_pos].edges if i != None])

        return settlement_pos, road_pos
    
    def discard_half(self) -> dict[catan.Resource, int]:
        to_remove = sum(self.resources.values()) // 2 # number of cards above limit
        to_discard = {i: 0 for i in catan.Resource if i != catan.Resource.DESERT} # dict of resources
        hand_copy = self.resources.copy()
        
        while sum(to_discard.values()) < to_remove: # while you have too many cards
            card = random.choice([i for i in catan.Resource if i != catan.Resource.DESERT]) # chose a card type
            if hand_copy[card] > 0:
                hand_copy[card] -= 1
                to_discard[card] += 1

        return to_discard
    
    def move_robber(self, board: catan.Board) -> tuple[int, catan.Colour]:
        
        robber_pos = random.randint(0, 18)
        while robber_pos == board.robber_pos or len([board.verts[i].structure.owner for i in board.hexes[robber_pos].verts if board.verts[i].structure.owner != catan.Colour.NONE and board.verts[i].structure.owner != self.colour]) == 0:
            robber_pos = random.randint(0, 18)
            
        adj_players = [board.verts[i].structure.owner for i in board.hexes[robber_pos].verts if board.verts[i].structure.owner != catan.Colour.NONE and board.verts[i].structure.owner != self.colour] # get all players adjacent to that hex
        adj_players = [i for i in adj_players if i != catan.Colour.NONE and i != self.colour] # eliminate empty spots and yourself
        
        if adj_players == []:
            adj_players = [catan.Colour.NONE]

        return robber_pos, random.choice(adj_players)
    
    def __get_position_options(self, building: catan.Building, board: catan.Board) -> set[int]:
        match building:
            case catan.Building.CITY | catan.Building.SETTLEMENT | catan.Building.ROAD:
                return {i for i in range(len(board.verts)) if board.can_place(building, self.colour, hand=self.resources, position=i)}
            
            case catan.Building.DEVELOPMENT_CARD:
                raise ValueError("you can't 'place' a development card")
            
            case _:
                raise ValueError(f"{building} is not a valid building")
    
    def roll_dice(self, board: catan.Board) -> catan.Action:
        if sum(v for k, v in self.development_cards.items() if k != catan.DevelopmentCard.VICTORY_POINT) > 0:
            # has a development card
            card = random.choice([k for k, v in self.development_cards.items() if k != catan.DevelopmentCard.VICTORY_POINT and v > 0])
            return catan.Action(catan.Event[f"USE_{card.name}"], None)
        
        return catan.Action(catan.Event.DICE_ROLL, None)
    
    def do_action(self, board: catan.Board) -> catan.Action:
        # try to build something if you can afford it
        if options := self.__get_position_options(catan.Building.CITY, board):
            return catan.Action(catan.Event.BUILD_CITY, random.choice(list(options)))
        
        if options := self.__get_position_options(catan.Building.SETTLEMENT, board):
            return catan.Action(catan.Event.BUILD_SETTLEMENT, random.choice(list(options)))
        
        if options := self.__get_position_options(catan.Building.ROAD, board):
            return catan.Action(catan.Event.BUILD_ROAD, random.choice(list(options)))
        
        if catan.can_afford(self.resources, catan.Building.DEVELOPMENT_CARD) and len(board.development_cards) > 0:
            return catan.Action(catan.Event.BUY_DEV_CARD, None)
            
        # try to use a development card if you have one and not used one this turn
        if not self.used_dev_card:
            if sum(v for k, v in self.development_cards.items() if k != catan.DevelopmentCard.VICTORY_POINT) > 0:
                # has a development card
                card = random.choice([k for k, v in self.development_cards.items() if k != catan.DevelopmentCard.VICTORY_POINT and v > 0])
                return catan.Action(catan.Event[f"USE_{card.name}"], None)
        
        return catan.Action(catan.Event.END_TURN, None)
    
    def on_opponent_action(self, action: catan.Action, board: catan.Board) -> None: # gives the action e.g. dice roll, and the state of the board after the action was completed
        # can be called on own turn, when another player accepts a trade deal
        ...
    
    def trade(self, person: catan.Colour, offer: catan.Hand, recieve: catan.Hand) -> bool:
        return False