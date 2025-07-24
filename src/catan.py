from enum import Enum, Flag
from dataclasses import dataclass, field
import random
from pprint import pprint

class BuildingError(Exception):
    def __init__(self, message):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

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

class Development_card(Enum):
    KNIGHT = 0
    VICTORY_POINT = 1
    YEAR_OF_PLENTY = 2
    ROAD_BUILDING = 3
    MONOPOLY = 4

action = tuple[str, None | int | Development_card | dict[str, list[Resource]]]

@dataclass
class Port:
    resource: Resource
    direction: Direction # for drawing on screen

# MARK: board construction

# "pointers" to objects are dictionaries with set keys

@dataclass
class Vertex:
    structure: Structure = field(default_factory=Structure)
    #                                                                     0   1   2   3   4   5
    edges: list[int | None] = field(default_factory = lambda: [None]*6) # N   NE  SE  S   SW  NW

@dataclass
class Edge:
    structure: Structure = field(default_factory=Structure)
    port: Port | None = None
    
    verts: list[int] = field(default_factory = lambda: [-1]*2) # N S | NE SW | NW SE

@dataclass
class Hex:
    resource: Resource = Resource.DESERT
    diceValue: int = 0
    hasRobber: bool = False
    #                                                                     0   1   2   3   4   5
    hexes: list[int | None] = field(default_factory = lambda: [None]*6) # NE  E   SE  SW  W   NW
    verts: list[int | None] = field(default_factory = lambda: [None]*6) # N   NE  SE  S   SW  NW

def rotate(l: list, n: int) -> list:
    return l[n:] + l[:n]

class Board:
    hexes: list[Hex] = []
    edges: list[Edge] = []
    verts: list[Vertex] = []
    development_cards: list[Development_card] = []
    
    def __init__(self, data: dict | None = None) -> None:
        self.development_cards = [Development_card.KNIGHT]*14 + [Development_card.VICTORY_POINT]*5 + [Development_card.YEAR_OF_PLENTY]*2 + [Development_card.ROAD_BUILDING]*2 + [Development_card.MONOPOLY]*2
        random.shuffle(self.development_cards)
        
        # optional data dictionary to specify the board layout
        # set hexes on hexes ===========================================================================================================
        # create root
        self.hexes.append(Hex(hexes=[1,2,3,4,5,6], verts=[0,1,2,3,4,5]))
        # first ring
        for i in range(6):
            # set "pointers"
            hexes = [i*2 + 8,       # corner
                     (i+1)%6 * 2 + 7, # edge (CW)
                     (i+1)%6 + 1,   # clockwise
                     0,             # center
                     (i+5)%6 + 1,   # anticlockwise
                     i*2 + 7]       # edge (ACW)
            
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
            
        # set values and resources of hexes
        
        if data == None: # board set-up not specified
            
            #                 A  B  C ...
            probablilities = [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11] # ordered as per letters on the backs of the chits
            
            # list of all resource hexes, 4 grain, 4 wool, 4 wood, 3 ore, 3 brick, 1 dessert
            resources = [Resource.GRAIN]*4 + [Resource.WOOL]*4 + [Resource.WOOD]*4 + [Resource.ORE]*3 + [Resource.BRICK]*3 + [Resource.DESERT]*1
            random.shuffle(resources) # randomise them so they are placed differently
            
            for i in self.hexes:
                i.resource = resources.pop(0)
                if i.resource != Resource.DESERT:
                    i.diceValue = probablilities.pop(0)
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
                self.edges[i].port = Port(resources.pop(), Direction.NE) # MARK: TODO
        
        else:
            # hexes
            for i, hex in enumerate(self.hexes):
                hex.resource = Resource[data["resources"][i]["resource"]]
                hex.diceValue = data["resources"][i]["value"]
                if hex.resource == Resource.DESERT:
                    hex.hasRobber = True
            
            # ports
            for port in data["ports"]:
                self.edges[port["position"]].port = Port(Resource[port["resource"]], Direction.NE) # MARK: TODO
                
    
    def encode(self) -> dict:
        return {
            "resources": [{"resource": i.resource.name, "value": i.diceValue} for i in self.hexes],
            "ports": [{"resource": edge.port.resource.name, "position": i} for i, edge in enumerate(self.edges) if edge.port != None]
        }
    
    def __str__(self) -> str:
        return str(self.encode())
    
    def get_resources(self, dice_value: int) -> dict[Colour, list[Resource]]:
        resources = {
            Colour.RED: [],
            Colour.ORANGE: [],
            Colour.BLUE: [],
            Colour.WHITE: [],
        }
        
        for hex in self.hexes:
            if hex.diceValue == dice_value:
                # resource producing hex
                for vert_i in hex.verts:
                    if vert_i != None:
                        # vertex that could have settlement
                        vert = self.verts[vert_i]
                        if vert.structure.type == Building.SETTLEMENT:
                            # settlement
                            resources[vert.structure.owner].append(hex.resource)
                            
                        elif vert.structure.type == Building.CITY:
                            # city
                            resources[vert.structure.owner].append(hex.resource)
                            resources[vert.structure.owner].append(hex.resource)
        
        return resources

    def place_settlement(self, owner: Colour, position: int, do_it: bool = True, need_road: bool = True) -> None:
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
                    if do_it: self.verts[position].structure = Structure(owner, Building.SETTLEMENT)
                    return
            
            raise BuildingError("Settlements can only be built on a vertex along one of your roads")
        
        else:
            if do_it: self.verts[position].structure = Structure(owner, Building.SETTLEMENT)
            return
    
    def place_city(self, owner: Colour, position: int, do_it: bool = True) -> None:
        # upgrade to players own settlement
        if self.verts[position].structure == Structure(owner, Building.SETTLEMENT): # settlement owned by the same person
            if do_it: self.verts[position].structure = Structure(owner, Building.CITY)
        
        else:
            raise BuildingError("Cities must be placed on one of your own settlements")
    
    def place_road(self, owner: Colour, position: int, do_it: bool = True) -> None:
        road = self.edges[position]
        
        # must be connected to players road or city / settlement. cant place through another player's settlement
        if road.structure != Structure(): # not empty
            raise BuildingError("Cannot build a road over another one")
        
        adj_verts = [self.verts[i] for i in road.verts]
        
        for vert in adj_verts:
            if vert.structure.owner == owner: # city or settlement owned by this player adjacent to road target
                if do_it: self.edges[position].structure = Structure(owner, Building.ROAD)
                return
            
            adj_edges = [self.edges[i] for i in vert.edges if i != None]
            for edge in adj_edges:
                if edge.structure == Structure(owner, Building.ROAD) and vert.structure.owner == Colour.NONE: # road owned by this person AND not interupted by settlement / city
                    if do_it: self.edges[position].structure = Structure(owner, Building.ROAD)
                    return

        raise BuildingError("Cannot build a road not connected to one of your other roads, settlements or cities")
    
    def delete_settlement(self, position: int):
        self.verts[position].structure = Structure()
    
    def delete_city(self, position: int):
        self.verts[position].structure = Structure()
        
    def delete_road(self, position: int):
        self.edges[position].structure = Structure()

if __name__ == "__main__":
    temp = Board()
    pprint(temp.encode())