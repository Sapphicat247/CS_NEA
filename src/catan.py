# data type imports
from enum import Enum
from dataclasses import dataclass, field

# function imports
import random, math
from copy import deepcopy

# GUI
import dearpygui.dearpygui as dpg

DEBUG = False

class BuildingError(Exception):
    """error used for when an AI tries to place a building in an invalid location"""
    def __init__(self, message):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

# MARK: board contents

class Colour(Enum):
    """used to keep track of who ownes what,\n
    component of the actual board game"""
    NONE = 0 # only used as placeholder
    RED = 1
    ORANGE = 2
    BLUE = 3
    WHITE = 4

def Colours():
    for i in Colour:
        if i != Colour.NONE:
            yield i

class Building(Enum):
    """a building"""
    EMPTY = 0 # used when e.g. a vertex has no settlement / city
    SETTLEMENT = 1
    CITY = 2
    ROAD = 3
    DEVELOPMENT_CARD = 4
    
def Buildings():
    for i in Building:
        if i != Building.EMPTY:
            yield i

@dataclass
class Structure:
    """a building with an owner"""
    owner: Colour = Colour.NONE
    type: Building = Building.EMPTY

class Resource(Enum):
    """used for cards and recording the type of each hex"""
    DESERT = 0 # also used for 3:1 trade at ports
    WOOD = 1
    WOOL = 2
    BRICK = 3
    ORE = 4
    GRAIN = 5
    
def Resources():
    for i in Resource:
        if i != Resource.DESERT:
            yield i

class DevelopmentCard(Enum):
    """component of the actual board game"""
    NONE = 0
    KNIGHT = 1
    VICTORY_POINT = 2
    YEAR_OF_PLENTY = 3
    ROAD_BUILDING = 4
    MONOPOLY = 5

def DevelopmentCards():
    for i in DevelopmentCard:
        if i != DevelopmentCard.NONE:
            yield i

class Event(Enum):
    """used so the AIs can communicate with the game,\n
    each event is a basic thing an ai can do"""
    END_TURN = 0 # None
    BUILD_SETTLEMENT = 10 # location
    BUILD_CITY = 11 # location
    BUILD_ROAD = 12 # location
    TRADE = 20 # tuple: (giving, recieving)
    BUY_DEV_CARD = 30 # None
    
    USE_KNIGHT = 31 # None
    USE_YEAR_OF_PLENTY = 32 # tuple[resource, resource]
    USE_ROAD_BUILDING = 33 # tuple[location, location]
    USE_MONOPOLY = 34 # resource
    
    DICE_ROLL = 51 # int: number
    P_STOLE_FROM_P = 52 # tuple: (giver, stealer)
    P_DISCARDED = 53 # tuple: (person, number of cards)

Location = int
Hand = dict[Resource, int]

EventArg = None | Location | Resource | tuple[Hand, Hand, list[Colour]] | tuple[Resource, Resource] | tuple[Location, Location] | tuple[Colour, Colour] | tuple[Colour, int]

@dataclass
class Action:
    """holds information as well as the actual thing the AI wants to do,\n
    or for information to be sent back to the AI"""
    event: Event
    arg: EventArg
    
    def __iter__(self):
        yield self.event
        yield self.arg

@dataclass
class Port:
    """component of the actual board game"""
    resource: Resource

# MARK: board elements

@dataclass
class Vertex:
    """the intersection between 3 edges (or 2 on the coast),\n
    where you build settlements and cities"""
    structure: Structure = field(default_factory=Structure)
    #                                                                     0   1   2   3   4   5
    edges: list[int | None] = field(default_factory = lambda: [None]*6) # N   NE  SE  S   SW  NW
    
    relative_pos: tuple[float, float] = (0, 0)

@dataclass
class Edge:
    """where you build roads"""
    structure: Structure = field(default_factory=Structure)
    port: Port | None = None
    
    verts: list[int] = field(default_factory = lambda: [-1]*2) # N S | NE SW | NW SE

@dataclass
class Hex:
    """produces resources and interacts with the robber"""
    resource: Resource = Resource.DESERT
    diceValue: int = 0
    hasRobber: bool = False
    #                                                                     0   1   2   3   4   5
    hexes: list[int | None] = field(default_factory = lambda: [None]*6) # NE  E   SE  SW  W   NW
    verts: list[int] =        field(default_factory = lambda: [-1]*6)   # N   NE  SE  S   SW  NW
    
    relative_pos: tuple[float, float] = (0, 0)

def rotate(l: list, n: int) -> list:
    """moves the first item of a list to the end {n} times"""
    return l[n:] + l[:n]

def get_cost(building: Building) -> Hand:
    match building:
        case Building.SETTLEMENT:
            return {
                Resource.BRICK: 1,
                Resource.WOOD:  1,
                Resource.WOOL:  1,
                Resource.GRAIN: 1
            }
            
        case Building.CITY:
            return {
                Resource.GRAIN: 2,
                Resource.ORE:   3
            }
            
        case Building.ROAD:
            return {
                Resource.BRICK: 1,
                Resource.WOOD:  1,
            }
        
        case Building.DEVELOPMENT_CARD:
            return {
                Resource.WOOL:  1,
                Resource.GRAIN: 1,
                Resource.ORE:   1
            }
        
        case _:
            raise ValueError(f"incorrect type: {building}")

def can_afford(hand: Hand, building: Building | Hand) -> bool:
    """given a hand of cards, can you afford a certain building"""
    match building:
        case Building.SETTLEMENT:
            return all([hand[Resource.BRICK] >= 1,
                        hand[Resource.WOOD]  >= 1,
                        hand[Resource.WOOL]  >= 1,
                        hand[Resource.GRAIN] >= 1,])
            
        case Building.CITY:
            return all([hand[Resource.ORE]   >= 3,
                        hand[Resource.GRAIN] >= 2,])
            
        case Building.ROAD:
            return all([hand[Resource.BRICK] >= 1,
                        hand[Resource.WOOD]  >= 1,])
        
        case Building.DEVELOPMENT_CARD:
            return all([hand[Resource.ORE]   >= 1,
                        hand[Resource.WOOL]  >= 1,
                        hand[Resource.GRAIN] >= 1,])
        
        case _ as resources if type(resources) == dict:
            return all(hand[k] >= resources[k] for k in resources.keys())
        
        case _:
            raise ValueError(f"incorrect type: {building}")

class Board:
    """hold all information about the current game"""
    hexes: list[Hex]
    edges: list[Edge]
    verts: list[Vertex]
    development_cards: list[DevelopmentCard]
    
    player_info: dict[Colour, dict[str, int]]# for each player, records the number of each type of card they have
    longest_road: Colour
    largest_army: Colour
    
    
    # MARK: board construction
    def __init__(self, data: dict | None = None) -> None:
        # optional data dictionary to specify the board layout
        # set up dpg viewport =========================================================================================================
        dpg.create_context()
        
        with dpg.viewport_drawlist(label="Board", front=False):
            with dpg.draw_layer(tag="hexes"):
                pass
            with dpg.draw_layer(tag="edges"):
                pass
            with dpg.draw_layer(tag="verts"):
                pass
            with dpg.draw_layer(tag="debug"):
                pass
        
        self.hexes = []
        self.edges = []
        self.verts = []
        
        self.player_info = {i: {"res_cards": 0, "dev_cards": 0} for i in Colour if i != Colour.NONE}
        self.longest_road = Colour.NONE
        self.largest_army = Colour.NONE
        
        self.development_cards = [DevelopmentCard.KNIGHT]*14 + [DevelopmentCard.VICTORY_POINT]*5 + [DevelopmentCard.YEAR_OF_PLENTY]*2 + [DevelopmentCard.ROAD_BUILDING]*2 + [DevelopmentCard.MONOPOLY]*2
        random.shuffle(self.development_cards)
        
        # set hexes on hexes ===========================================================================================================
        # create root
        self.hexes.append(Hex(hexes=[1,2,3,4,5,6], verts=[0,1,2,3,4,5]))
        # first ring
        for i in range(6):
            # set "pointers"
            hexes = [i*2 + 8,         # corner
                     (i+1)%6 * 2 + 7, # edge (CW)
                     (i+1)%6 + 1,     # clockwise
                     0,               # center
                     (i+5)%6 + 1,     # anticlockwise
                     i*2 + 7]         # edge (ACW)
            
            self.hexes.append(Hex(hexes=rotate(hexes, -i))) # create Hex and add to list
        
        # second ring
        for i in range(6):
            edgeHexes = [-1,
                         2*i + 8,         # CW
                         i + 1,           # CW IN
                         (i+5)%6 + 1,     # ACW IN
                         (i+5)%6 * 2 + 8, # ACW
                         -1]
            
            cornerHexes = [-1,
                           -1,
                           (i+1)%6 * 2 + 7, # CW
                           i + 1,         # IN
                           2*i + 7,       # ACW
                           -1]
            
            self.hexes.append(Hex(hexes=rotate(edgeHexes, -i))) # create Hex and add to list
            self.hexes.append(Hex(hexes=rotate(cornerHexes, -i))) # create Hex and add to list
        
        # set verts on hexes ===========================================================================================================
        for i in range(6):
            # 4 new verts
            verts = [i*3 + 7,       # Out ACW      new
                     i*3 + 8,       # Out CW       new
                     (i+1)%6*3 + 6, # Next CW      from next
                     (i+1)%6,       # Center CW    from next
                     i,             # Center ACW   new
                     i*3 + 6,]      # Next ACW     new

            for _ in range(4):
                self.verts.append(Vertex())
            
            self.hexes[i+1].verts = rotate(verts, -i)
        
        for i in range(6):
            # 5 new verts
            edgeVerts = [i*5 + 25,        # Outside       # new
                         i*5 + 26,        # Next Outside  # new
                         i*3 + 7,         # Next Inside   # old
                         i*3 + 6,         # Inside        # old
                         (i+5)%6 * 3 + 8, # Prev Inside   # old
                         i*5 + 24,]       # Prev outside  # new
            
            cornerVerts = [i*5 + 27,       # Outside ACW   # new
                           i*5 + 28,       # Outside CW    # new
                           (i+1)%6*5 + 24, # Next Outside  # from next
                           i*3 + 8,        # Next Inside   # old
                           i*3 + 7,        # Prev Inside   # old
                           i*5 + 26,]      # Prev outside  # from prev
            
            self.hexes[2*i+7].verts = rotate(edgeVerts, -i) # edge
            self.hexes[2*i+8].verts = rotate(cornerVerts, -i) # corner
            
            for _ in range(5):
                self.verts.append(Vertex())

        # set verts on edges ==============================================================================================================
        # inner tangents
        for i in range(6):
            # create edge
            self.edges.append(Edge(verts=[i, (i+1)%6]))
            # set "pointers" in verts
            self.verts[i].edges[(i+2)%6] = i
            
            self.verts[(i+1)%6].edges[(i+5)%6] = i
        
        # inner normals
        for i in range(6):
            # create edge
            self.edges.append(Edge(verts=[i, i*3 + 6]))
            # set "pointers" in verts
            self.verts[i].edges[i] = i + 6
            
            self.verts[i*3 + 6].edges[(i+3)%6] = i + 6
        
        # middle tangents
        for i in range(6):
            # create edges
            self.edges.append(Edge(verts=[i*3 + 6, i*3 + 7]))
            self.edges.append(Edge(verts=[i*3 + 7, i*3 + 8]))
            self.edges.append(Edge(verts=[i*3 + 8, (i+1)%6*3 + 6]))
            # set "pointers" to verts
            self.verts[i*3 + 6].edges[(i+1)%6] = i*3 + 12
            self.verts[i*3 + 7].edges[(i+2)%6] = i*3 + 13
            self.verts[i*3 + 8].edges[(i+3)%6] = i*3 + 14
            
            self.verts[i*3 + 7].edges[(i+4)%6] = i*3 + 12
            self.verts[i*3 + 8].edges[(i+5)%6] = i*3 + 13
            self.verts[(i+1)%6*3 + 6].edges[i] = i*3 + 14
        
        # outer normals
        for i in range(6):
            # create edges
            self.edges.append(Edge(verts=[i*3 + 7, i*5 + 26]))
            self.edges.append(Edge(verts=[i*3 + 8, (i+1)%6*5 + 24]))
            # set "pointers"
            self.verts[i*3 + 7].edges[i] = i*2 + 30
            self.verts[i*3 + 8].edges[(i+1)%6] = i*2 + 31
            
            self.verts[i*5 + 26].edges[(i+3)%6] = i*2 + 30
            self.verts[(i+1)%6*5 + 24].edges[(i+4)%6] = i*2 + 31
        
        # outer tangents
        for i in range(6):
            # create edges
            self.edges.append(Edge(verts=[i*5 + 24, i*5 + 25]))
            self.edges.append(Edge(verts=[i*5 + 25, i*5 + 26]))
            self.edges.append(Edge(verts=[i*5 + 26, i*5 + 27]))
            self.edges.append(Edge(verts=[i*5 + 27, i*5 + 28]))
            self.edges.append(Edge(verts=[i*5 + 28, (i+1)%6*5 + 24]))
            # set "pointers"
            self.verts[i*5 + 24].edges[(i+1)%6] = i*5+42
            self.verts[i*5 + 25].edges[(i+2)%6] = i*5+43
            self.verts[i*5 + 26].edges[(i+1)%6] = i*5+44
            self.verts[i*5 + 27].edges[(i+2)%6] = i*5+45
            self.verts[i*5 + 28].edges[(i+3)%6] = i*5+46
            
            self.verts[i*5 + 25].edges[(i+4)%6] = i*5+42
            self.verts[i*5 + 26].edges[(i+5)%6] = i*5+43
            self.verts[i*5 + 27].edges[(i+4)%6] = i*5+44
            self.verts[i*5 + 28].edges[(i+5)%6] = i*5+45
            self.verts[(i+1)%6*5 + 24].edges[i] = i*5+46
        
        # set vert positions
        # hexes
        for i in range(6):
            theta = i * math.pi/3
            theta2 = (i+1)%6 * math.pi/3
            self.hexes[i+1].relative_pos =   (math.sin(theta) + math.sin(theta2), math.cos(theta) + math.cos(theta2))
            self.hexes[2*i+8].relative_pos = (2*(math.sin(theta) + math.sin(theta2)), 2*(math.cos(theta) + math.cos(theta2)))
            self.hexes[2*i+7].relative_pos = (3*math.sin(theta), 3*math.cos(theta))
            
        # verts
        # root hex
        for i in range(6):
            theta = i * math.pi/3
            self.verts[i].relative_pos = (math.sin(theta), math.cos(theta))
        
        # outer corners
        for hex_i in range(6):

            for theta_i, i in enumerate(self.hexes[hex_i*2 + 8].verts):
                theta = theta_i * math.pi/3
                self.verts[i].relative_pos = (math.sin(theta) + self.hexes[hex_i*2 + 8].relative_pos[0],
                                                math.cos(theta) + self.hexes[hex_i*2 + 8].relative_pos[1])
        
        # middle edges outer and inner verts
        for i in range(6):
            theta = i * math.pi/3
            self.verts[3*i+6].relative_pos = (2*math.sin(theta), 2*math.cos(theta))
            self.verts[5*i+25].relative_pos = (4*math.sin(theta), 4*math.cos(theta))
            
        
        # set values and resources of hexes ========================================================================================
        
        if data == None: # board set-up not specified
            
            #                 A  B  C ...                                  ... P  Q  R
            probablilities = [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11]
            # ordered as per letters on the backs of the chits
            
            # list of all resource hexes, 4 grain, 4 wool, 4 wood, 3 ore, 3 brick, 1 dessert
            resources = [Resource.GRAIN]*4 + [Resource.WOOL]*4 + [Resource.WOOD]*4 + [Resource.ORE]*3 + [Resource.BRICK]*3 + [Resource.DESERT]*1
            random.shuffle(resources) # randomise them so they are placed differently
            
            for i in self.hexes:
                i.resource = resources.pop()
                if i.resource != Resource.DESERT:
                    i.diceValue = probablilities.pop()
                else:
                    i.diceValue = 7
                    i.hasRobber = True
            
            # set ports
            resources = [Resource.GRAIN, Resource.WOOL, Resource.WOOD, Resource.ORE, Resource.BRICK] + [Resource.DESERT]*4
            random.shuffle(resources)
            
            gaps = [2,2,3,2,2,3,2,3,2]
            random.shuffle(gaps)
            # ofset from start
            gaps[0] -= random.randint(0, gaps[0])
            
            positions = [sum(gaps[:i+1]) + 42 + i for i in range(len(gaps))]
            
            for i in positions:
                self.edges[i].port = Port(resources.pop())
        
        else:
            # hexes
            for i, hex in enumerate(self.hexes):
                hex.resource = Resource[data["resources"][i]["resource"]]
                hex.diceValue = data["resources"][i]["value"]
                if hex.resource == Resource.DESERT:
                    hex.hasRobber = True
            
            # ports
            for port in data["ports"]:
                self.edges[port["position"]].port = Port(Resource[port["resource"]])

    def enumerate_adjacent_hexes(self, vert: int):
        for i, hex in enumerate(self.hexes):
            if vert in hex.verts:
                yield i, hex
    
    # MARK: Placement
    def can_place(self, building: Building, owner: Colour, position: int, hand: dict[Resource, int] | None = None, *, need_road: bool = True) -> bool:
        """test if a certain AI can build a building.\n\n
        
        this takes into account the hand of cards and the current board
        
        Args:
            building (`Building`): the building to test
            owner (`Colour`): the owner of the building
            position (`int`): the index location for the building
            hand (`dict[Resource, int]` (optional)): a hand of cards
        
        KWArgs:
            need_road (`bool`): needs road
        
        Returns:
            bool: True if you can place that building
        
        """
        
        match building:
            case Building.ROAD:
                try:
                    self.place_road(owner, hand=hand, position=position)
                except BuildingError:
                    # can't place road
                    return False
                else:
                    self.delete_road(position)
                    return True
                
            case Building.SETTLEMENT:
                try:
                    self.place_settlement(owner, hand=hand, position=position, need_road=need_road)
                except BuildingError:
                    # can't place road
                    return False
                else:
                    self.delete_settlement(position)
                    return True
                
            case Building.CITY:
                try:
                    self.place_city(owner, hand=hand, position=position)
                except BuildingError:
                    # can't place road
                    return False
                else:
                    self.delete_city(position)
                    return True
                
            case Building.DEVELOPMENT_CARD:
                raise ValueError("you can't place a development card")
            case _:
                raise ValueError(f"{building} is not of type: Building")
    
    
    def place_settlement(self, owner: Colour, position: int, hand: dict[Resource, int] | None = None, *, need_road: bool = True) -> None:
        """places a settlement\n\n
        
        Args:
            owner (`Colour`): the owner of the building
            position (`int`): the index location for the building
            hand (`dict[Resource, int]` (optional)): a hand of cards
        
        KWArgs:
            need_road (`bool`): needs road
        
        Raises:
            BuildingError: The building can't be placed
        """
        
        if hand != None and not can_afford(hand, Building.SETTLEMENT):
            raise BuildingError("Cannot afford a settlement")
        
        if sum(1 for i in self.verts if i.structure == Structure(owner, Building.SETTLEMENT)) >= 5:
            raise BuildingError("You have used all of you settlements")
        
        vert = self.verts[position]
                
        if vert.structure.owner != Colour.NONE: # building already exists there
            raise BuildingError("Cannot build a settlement over another building")
        
        adj_edges = [self.edges[i] for i in vert.edges if i != None]
        for edge in adj_edges:
            adj_vert = self.verts[[i for i in edge.verts if i != position][0]] # always 2 without condition
            if adj_vert.structure.owner != Colour.NONE: # building exists 1 road away from target
                raise BuildingError("Cannot build a settlement that close to another one")
        
        if need_road:
            for edge in adj_edges:
                if edge.structure == Structure(owner, Building.ROAD): # road owned by this person
                    self.verts[position].structure = Structure(owner, Building.SETTLEMENT)
                    return
            
            raise BuildingError("Settlements can only be built on a vertex along one of your roads")
        
        else:
            self.verts[position].structure = Structure(owner, Building.SETTLEMENT)
            return
    
    def place_city(self, owner: Colour, position: int, hand: dict[Resource, int] | None = None) -> None:
        """places city\n\n
        
        Args:
            owner (`Colour`): the owner of the building
            position (`int`): the index location for the building
            hand (`dict[Resource, int]` (optional)): a hand of cards
        
        Raises:
            BuildingError: The building can't be placed
        """
        
        if hand != None and not can_afford(hand, Building.CITY):
            raise BuildingError("Cannot afford a city")
        
        if sum(1 for i in self.verts if i.structure == Structure(owner, Building.CITY)) >= 4:
            raise BuildingError("You have used all of you cities")
        
        # upgrade to players own settlement
        if self.verts[position].structure == Structure(owner, Building.SETTLEMENT): # settlement owned by the same person
            self.verts[position].structure = Structure(owner, Building.CITY)
        
        else:
            raise BuildingError("Cities must be placed on one of your own settlements")
    
    def place_road(self, owner: Colour, position: int, hand: dict[Resource, int] | None = None) -> None:
        """places road\n\n
        
        Args:
            owner (`Colour`): the owner of the building
            position (`int`): the index location for the building
            hand (`dict[Resource, int]` (optional)): a hand of cards
        
        Raises:
            BuildingError: The building can't be placed
        """
        
        if hand != None and not can_afford(hand, Building.ROAD):
            raise BuildingError("Cannot afford a road")
        
        if sum(1 for i in self.edges if i.structure == Structure(owner, Building.ROAD)) >= 15:
            raise BuildingError("You have used all of you roads")
        
        road = self.edges[position]
        
        # must be connected to players road or city / settlement. cant place through another player's settlement
        if road.structure != Structure(): # not empty
            raise BuildingError("Cannot build a road over another one")
        
        adj_verts = [self.verts[i] for i in road.verts]
        
        for vert in adj_verts:
            if vert.structure.owner == owner: # city or settlement owned by this player adjacent to road target
                self.edges[position].structure = Structure(owner, Building.ROAD)
                break
            
            adj_edges = [self.edges[i] for i in vert.edges if i != None]
            for edge in adj_edges:
                if edge.structure == Structure(owner, Building.ROAD) and vert.structure.owner == Colour.NONE: # road owned by this person AND not interupted by settlement / city
                    self.edges[position].structure = Structure(owner, Building.ROAD)
                    break
                
        else:
            raise BuildingError("Cannot build a road not connected to one of your other roads, settlements or cities")
        
        self.update_longest_road()
    
    def delete_settlement(self, position: int):
        """removes settlement
        
        Args:
            position (`int`): the index location for the building
        """
        self.verts[position].structure = Structure()
    
    def delete_city(self, position: int):
        """downgrades city to settlement
        
        Args:
            position (`int`): the index location for the building
        """
        self.verts[position].structure = Structure(self.verts[position].structure.owner, Building.SETTLEMENT)
        
    def delete_road(self, position: int):
        """removes road
        
        Args:
            position (`int`): the index location for the building
        """
        self.edges[position].structure = Structure()
    
    @property
    def robber_pos(self) -> int:
        """gets where the robber is
        
        Returns:
            int: the index of the robber location
        
        Raises:
            Exception: Robber was not found
        """
        pos = None
        
        for i, hex in enumerate(self.hexes):
            if hex.hasRobber:
                pos = i
                break
        
        assert pos is not None
        return pos
    
    # MARK: Game concepts
    
    def get_resources(self, dice_value: int | None, only_vert: int | None = None) -> dict[Colour, dict[Resource, int]]:
        """works out which AI would recieve what resources, given a dice roll"""
        
        assert dice_value is None or 1 <= dice_value <= 12
        assert dice_value is None or dice_value != 7
        
        resources = {
            Colour.RED: {i: 0 for i in Resource if i != Resource.DESERT},
            Colour.ORANGE: {i: 0 for i in Resource if i != Resource.DESERT},
            Colour.BLUE: {i: 0 for i in Resource if i != Resource.DESERT},
            Colour.WHITE: {i: 0 for i in Resource if i != Resource.DESERT},
        }
        
        for hex in self.hexes:
            if (hex.diceValue == dice_value and not hex.hasRobber) or (dice_value is None and hex.diceValue != 7):
                # resource producing hex
                for vert_i in hex.verts:
                    if vert_i is not None and (only_vert is None or vert_i == only_vert):
                        # vertex that could have settlement
                        vert = self.verts[vert_i]
                        if vert.structure.type == Building.SETTLEMENT:
                            # settlement
                            resources[vert.structure.owner][hex.resource] += 1
                            
                        elif vert.structure.type == Building.CITY:
                            # city
                            resources[vert.structure.owner][hex.resource] += 2
        
        return resources
    
    def set_robber_pos(self, pos: int):
        """places the robber on a hex"""
        if pos < 0 or pos > 18:
            raise ValueError("you must choose a hex number between 0 and 18 inclusive")
        
        if pos == self.robber_pos:
            raise ValueError("you can't put the robber on the same hex it started on")
        
        for hex in self.hexes:
            hex.hasRobber = False
        
        self.hexes[pos].hasRobber = True
    
    def shortest_path(self, start: int, end: int, player: Colour, max_depth:int = 15) -> list[int]:
        
        distances: dict[int, int] = {start: 0}
        
        for _ in range(max_depth):
            to_add = {}
            for vert_i, d in distances.items():
                vert = self.verts[vert_i]
                
                for edge_i in vert.edges:
                    if edge_i is not None:
                        edge = self.edges[edge_i]
                        if edge.structure.owner == player or edge.structure.owner == Colour.NONE:
                            # valid road position
                            next_vert_i = edge.verts[1] if edge.verts[0] == vert_i else edge.verts[0]
                            next_vert = self.verts[vert_i]
                            if next_vert.structure.owner == player or next_vert.structure.owner == Colour.NONE:
                                # can go through vertex
                                if next_vert_i not in distances.keys() or distances[next_vert_i] > d+1:
                                    to_add.update({next_vert_i: d+1})
            distances.update(to_add)
        
        path = [end]
        vert_i = end
        while path[0] != start:
            vert = self.verts[path[0]]
            
            
            for edge_i in vert.edges:
                if edge_i is not None:
                    # valid edge around current end of path
                    edge = self.edges[edge_i]
                    # find vertex at other end of edge
                    next_vert_i = edge.verts[1] if edge.verts[0] == path[0] else edge.verts[0]
                    
                    if next_vert_i in distances.keys() and distances[next_vert_i] < distances[path[0]]:
                        # vertex is in list & 
                        path.insert(0, next_vert_i)
                        break
        
        return path
                
                
    
    def get_longest_road(self, colour: Colour) -> list[int]:
        # for each starting vertex:
            # find adjacent roads
            # if they are correct
            # recurse on other vertex on the edge
        
        # returns list of VERTECIES
        
        
        def search(start: int, visited_edges: set[int] = set()) -> list[int]:
            # start is a vertex
            max_path = []
            
            found_edge = False
            
            for edge_i in self.verts[start].edges:
                if edge_i is not None and edge_i not in visited_edges:
                    edge = self.edges[edge_i]
                    if edge.structure.owner == colour:
                        # edge has road
                        found_edge = True
                        
                        next_vert = edge.verts[1] if edge.verts[0] == start else edge.verts[0]
                        path = search(next_vert, visited_edges | {edge_i})
                        
                        if len(path) > len(max_path):
                            max_path = path
            
            return max_path + [start] if found_edge else [start]

        max_path = []
        
        for i in range(len(self.verts)):
            path = search(i)
            if len(path) > len(max_path):
                max_path = path
        
        return max_path
    
    def update_longest_road(self):
        max_length = 4
        best_player = Colour.NONE
        
        for player in Colour:
            if player != Colour.NONE:
                length = len(self.get_longest_road(player))
                if length > max_length:
                    max_length = length
                    best_player = player
        
        self.longest_road = best_player
                
    
    @property
    def safe_copy(self):
        """hide info the AIs are not allowed to see"""
        new_board = deepcopy(self)
        new_board.development_cards = [DevelopmentCard.NONE]*len(new_board.development_cards) # don't reveal the stack of developmeant cards
        
        return new_board
    
    # MARK: Display
    @property
    def encoding(self) -> dict:
        """produces a dictionary representation of the board, ignores anything built on it"""
        return {
            "resources": [{"resource": i.resource.name, "value": i.diceValue} for i in self.hexes],
            "ports": [{"resource": edge.port.resource.name, "position": i} for i, edge in enumerate(self.edges) if edge.port != None]
        }
    
    def __str__(self) -> str:
        return str(self.encoding)
    
    def draw(self):
        """updates GUI"""
        dpg.delete_item("hexes", children_only=True) # clear
        dpg.delete_item("edges", children_only=True) # clear
        dpg.delete_item("verts", children_only=True) # clear
        dpg.delete_item("debug", children_only=True) # clear
        
        hex_colour_lookup = {Resource.DESERT: (204, 176, 104, 255),
                             Resource.WOOD:   (45,  82,  44,  255),
                             Resource.WOOL:   (82,  230, 78,  255),
                             Resource.BRICK:  (204, 82,  20,  255),
                             Resource.ORE:    (115, 131, 156, 255),
                             Resource.GRAIN:  (237, 237, 69,  255)}
        
        player_colour_lookup = {Colour.RED:    (255, 0,   0,   255),
                                Colour.ORANGE: (255, 127, 44,  255),
                                Colour.BLUE:   (0,   0,   255, 255),
                                Colour.WHITE:  (255, 255, 255,  255)}
        
        # get size of each hex
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        
        vert_size = height//8
        horizontal_size = width//8.660254038 # 5*sqrt(3)
        
        size = min(vert_size, horizontal_size)*.9 # side length
        center = (width//2, height//2)

        for hex_i, hex in enumerate(self.hexes):
            # get positions
            vert_positions = [self.verts[i].relative_pos for i in hex.verts if i != None]
            vert_positions = [[i[0]*size + center[0], i[1]*size + center[1]] for i in vert_positions]
            
            dpg.draw_polygon(vert_positions, fill=hex_colour_lookup[hex.resource], parent="hexes", color=(0,0,0,0))
            
            # dice number / robber
            if hex.hasRobber:
                col = (61, 68, 79, 255)
            else:
                col = (232, 232, 181, 255 if hex.resource != Resource.DESERT else 0)
                
            dpg.draw_circle((hex.relative_pos[0]*size + center[0], hex.relative_pos[1]*size + center[1]), size/4, fill=col, parent="hexes", color=(0,0,0,0))
                

            if hex.resource != Resource.DESERT:
                if hex.diceValue == 6 or hex.diceValue == 8:
                    col = (255, 0, 0, 255)
                else:
                    col = (0  , 0, 0, 255)
                dpg.draw_text((hex.relative_pos[0]*size + center[0] - size/18*len(str(hex.diceValue)), hex.relative_pos[1]*size + center[1] - size/9), f"{hex.diceValue}", color=col, size=size/4, parent="debug")
                
            
            # debug text
            if DEBUG: dpg.draw_text((hex.relative_pos[0]*size + center[0], hex.relative_pos[1]*size + center[1]), f"{hex_i}", color=(0, 255, 0, 255), size=20, parent="debug")
        
        for vert_i, vert in enumerate(self.verts):
            
            if vert.structure.owner != Colour.NONE:
                colour = player_colour_lookup[vert.structure.owner]
                
                dpg.draw_circle((vert.relative_pos[0]*size + center[0], vert.relative_pos[1]*size + center[1]), size/6, fill=colour, parent="verts", color=(0,0,0,0))
            
            if vert.structure.type == Building.CITY:
                dpg.draw_circle((vert.relative_pos[0]*size + center[0], vert.relative_pos[1]*size + center[1]), size/8, fill=(0,0,0,255), parent="verts", color=(0,0,0,0))
            
            # debug text
            if DEBUG: dpg.draw_text((vert.relative_pos[0]*size + center[0], vert.relative_pos[1]*size + center[1]), f"{vert_i}", color=(255, 0, 0, 255), size=20, parent="debug")
            
        for edge_i, edge in enumerate(self.edges):
            if edge.structure.owner != Colour.NONE:
                colour = player_colour_lookup[edge.structure.owner]
                
                p0 = (self.verts[edge.verts[0]].relative_pos[0]*size + center[0], self.verts[edge.verts[0]].relative_pos[1]*size + center[1])
                p1 = (self.verts[edge.verts[1]].relative_pos[0]*size + center[0], self.verts[edge.verts[1]].relative_pos[1]*size + center[1])
                    
                dpg.draw_line(p0, p1, thickness=size/12, color=colour, parent="edges")
            
            if edge.port is not None:
                # find road direction
                # index:     0  1    2    3  4     5
                # direction: N  NE   SE   S  SW    NW
                # angle:     π  2/3π 1/3π 0  -1/3π -2/3π
                
                for index, coastal_edge in enumerate(self.verts[edge.verts[0]].edges):
                    if coastal_edge == edge_i:
                        # found this edge
                        direction = ["N", "NE", "SE", "S", "SW", "NW"][index]
                        angle = [math.pi, 2/3*math.pi, 1/3*math.pi, 0, -1/3*math.pi, -2/3*math.pi][index]
                        
                        p0 = (self.verts[edge.verts[0]].relative_pos[0]*size + center[0], self.verts[edge.verts[0]].relative_pos[1]*size + center[1])
                        p1 = (self.verts[edge.verts[1]].relative_pos[0]*size + center[0], self.verts[edge.verts[1]].relative_pos[1]*size + center[1])
                        
                        p = ((p0[0] + p1[0])/2 + size/3*math.cos(angle), (p0[1] + p1[1])/2 + size/3*math.sin(angle))
                        
                        if DEBUG: dpg.draw_text((p[0] + size/3*math.cos(angle), p[1] + size/3*math.sin(angle)), f"{edge.port.resource.name.capitalize()}", color=(0, 0, 255, 255), size=20, parent="debug")
                        
                        dpg.draw_line(p0, p, color=(80,60,0), parent="edges", thickness=size/18)
                        dpg.draw_line(p1, p, color=(80,60,0), parent="edges", thickness=size/18)
                        
                        dpg.draw_circle(p, size/5, fill=hex_colour_lookup[edge.port.resource], color=(0,0,0), parent="edges")
                        dpg.draw_text((p[0]-size/12, p[1]-size/16), f"{"3:1" if edge.port.resource == Resource.DESERT else "2:1"}", color=(0,0,0), size=size/8, parent="debug")
                
            
            if DEBUG: 
                p0 = (self.verts[edge.verts[0]].relative_pos[0]*size + center[0], self.verts[edge.verts[0]].relative_pos[1]*size + center[1])
                p1 = (self.verts[edge.verts[1]].relative_pos[0]*size + center[0], self.verts[edge.verts[1]].relative_pos[1]*size + center[1])
                
                dpg.draw_text(((p0[0] + p1[0])/2, (p0[1] + p1[1])/2), f"{edge_i}", color=(0, 0, 255, 255), size=20, parent="debug")

# MARK: testing
if __name__ == "__main__":
    def main():
        def loop():
            while 1:
                v = int(input())
                board.edges[v].structure = Structure(Colour.WHITE, Building.ROAD) if board.edges[v].structure.owner == Colour.NONE else Structure(Colour.NONE, Building.EMPTY)
                
        from threading import Thread
        dpg.create_context()

        # init viewport
        dpg.create_viewport(title='Catan', width=1920, height=1080)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        board = Board()
        
        Thread(target=loop).start()
        
        while 1:
            board.draw()
            dpg.render_dearpygui_frame()
    
    main()