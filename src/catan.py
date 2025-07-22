from enum import Enum
from dataclasses import dataclass

class Colour(Enum):
    NONE = 0 # only used as placeholder
    RED = 1
    ORANGE = 2
    BLUE = 3
    WHITE = 4

class Building(Enum):
    EMPTY = 0 # used when e.g. a vertex has no settlement / city
    SETTLEMENT = 1
    CITY = 2
    ROAD = 3

@dataclass
class Structure:
    owner: Colour = Colour.NONE
    type: Building = Building.EMPTY

class Resource(Enum):
    DESERT = 0 # also used for 3:1 trade at ports
    WOOD = 1
    WOOL = 2
    BRICK = 3
    ORE = 4
    GRAIN = 5