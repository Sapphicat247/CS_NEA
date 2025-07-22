from enum import Enum, Flag
from dataclasses import dataclass, field, MISSING

class Direction(Flag):
    N  = 2**0
    NE = 2**1
    E  = 2**2
    SE = 2**3
    S  = 2**4
    SW = 2**5
    W  = 2**6
    NW = 2**7

# MARK: board contents

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

@dataclass
class Port:
    resource: Resource
    direction: Direction # for drawing on screen

# MARK: board construction

# "pointers" to objects are dictionaries with set keys

@dataclass
class Vertex:
    structure: Structure = field(default_factory=Structure)
    
    edges: dict = field(default_factory = dict)

@dataclass
class Edge:
    port: Port # compare with MISSING to check if port exists: https://stackoverflow.com/questions/53589794/pythonic-way-to-check-if-a-dataclass-field-has-a-default-value
    
    structure: Structure = field(default_factory=Structure)
    
    verts: dict = field(default_factory = dict)

@dataclass
class Hex:
    resource: Resource = Resource.DESERT
    diceValue: int = 0
    hasRobber: bool = False
    
    hexes: dict = field(default_factory = dict)
    verts: dict = field(default_factory = dict)