from enum import Enum, Flag
from dataclasses import dataclass, field
import random, math
from pprint import pprint
from collections import Counter
import dearpygui.dearpygui as dpg
from copy import deepcopy

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
    DEVELOPMENT_CARD = 4

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
    NONE = 5

Action = tuple[str, None | int | tuple[Development_card, dict[str, int | Colour | Resource]] | dict[str, list[Resource]]]
# TODO add support for extra options only sent to AIs as this only supports Recieving

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
    
    relative_pos: tuple[float, float] = (0, 0)

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
    verts: list[int] =        field(default_factory = lambda: [-1]*6)   # N   NE  SE  S   SW  NW
    
    relative_pos: tuple[float, float] = (0, 0)

def rotate(l: list, n: int) -> list:
    return l[n:] + l[:n]

def can_afford(hand: list[Resource], building: Building | list[Resource]) -> bool:
    match building:
        case Building.SETTLEMENT:
            needed = (Resource.BRICK, Resource.WOOD, Resource.GRAIN, Resource.WOOL)
            
        case Building.CITY:
            needed = (Resource.ORE, Resource.ORE, Resource.ORE, Resource.GRAIN, Resource.GRAIN)
            
        case Building.ROAD:
            needed = (Resource.BRICK, Resource.WOOD)
        
        case Building.DEVELOPMENT_CARD:
            needed = (Resource.ORE, Resource.GRAIN, Resource.WOOL)
        
        case _ as list_of_resources if type(list_of_resources) == list:
            needed = tuple(list_of_resources)
        
        case _:
            raise ValueError(f"{building} is not of type Building; it is of type {type(building)}???")            
        
    hand_counter = Counter(hand)
    needed_counter = Counter(needed)
        
    return all(needed_counter[element] <= hand_counter[element] for element in needed_counter)

class Board:
    hexes: list[Hex] = []
    edges: list[Edge] = []
    verts: list[Vertex] = []
    development_cards: list[Development_card] = []
    
    def __init__(self, data: dict | None = None) -> None:
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
                self.edges[i].port = Port(resources.pop(), Direction.NE) # implement direction MARK: TODO
        
        else:
            # hexes
            for i, hex in enumerate(self.hexes):
                hex.resource = Resource[data["resources"][i]["resource"]]
                hex.diceValue = data["resources"][i]["value"]
                if hex.resource == Resource.DESERT:
                    hex.hasRobber = True
            
            # ports
            for port in data["ports"]:
                self.edges[port["position"]].port = Port(Resource[port["resource"]], Direction.NE) # implement direction MARK: TODO
                
    
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
            if hex.diceValue == dice_value and not hex.hasRobber:
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

    def can_place(self, building: Building, owner: Colour, hand: list[Resource] | None, position: int, /, *, need_road: bool = True) -> bool:
        match building:
            case Building.ROAD:
                try:
                    self.place_road(owner, hand, position)
                except BuildingError:
                    # can't place road
                    return False
                else:
                    self.delete_road(position)
                    return True
                
            case Building.SETTLEMENT:
                try:
                    self.place_settlement(owner, hand, position, need_road=need_road)
                except BuildingError:
                    # can't place road
                    return False
                else:
                    self.delete_settlement(position)
                    return True
                
            case Building.CITY:
                try:
                    self.place_city(owner, hand, position)
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
    
    
    def place_settlement(self, owner: Colour, hand: list[Resource] | None, position: int, /, *, need_road: bool = True) -> None:
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
    
    def place_city(self, owner: Colour, hand: list[Resource] | None, position: int) -> None:
        if hand != None and not can_afford(hand, Building.CITY):
            raise BuildingError("Cannot afford a city")
        
        if sum(1 for i in self.verts if i.structure == Structure(owner, Building.CITY)) >= 4:
            raise BuildingError("You have used all of you cities")
        
        # upgrade to players own settlement
        if self.verts[position].structure == Structure(owner, Building.SETTLEMENT): # settlement owned by the same person
            self.verts[position].structure = Structure(owner, Building.CITY)
        
        else:
            raise BuildingError("Cities must be placed on one of your own settlements")
    
    def place_road(self, owner: Colour, hand: list[Resource] | None, position: int) -> None:
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
                return
            
            adj_edges = [self.edges[i] for i in vert.edges if i != None]
            for edge in adj_edges:
                if edge.structure == Structure(owner, Building.ROAD) and vert.structure.owner == Colour.NONE: # road owned by this person AND not interupted by settlement / city
                    self.edges[position].structure = Structure(owner, Building.ROAD)
                    return

        raise BuildingError("Cannot build a road not connected to one of your other roads, settlements or cities")
    
    def delete_settlement(self, position: int):
        self.verts[position].structure = Structure()
    
    def delete_city(self, position: int):
        """downgrades city to settlement"""
        self.verts[position].structure = Structure(self.verts[position].structure.owner, Building.SETTLEMENT)
        
    def delete_road(self, position: int):
        self.edges[position].structure = Structure()
    
    def get_robber_pos(self) -> int:
        for i, hex in enumerate(self.hexes):
            if hex.hasRobber:
                return i
        
        raise Exception("Robber was not found anywhere on the board (this should never happen)")
    
    def set_robber_pos(self, pos: int):
        
        if pos < 0 or pos > 18:
            raise ValueError("you must choose a hex number between 0 and 18 inclusive")
        
        for hex in self.hexes:
            hex.hasRobber = False
        
        self.hexes[pos].hasRobber = True
    
    def draw(self):
        dpg.delete_item("hexes", children_only=True) # clear
        dpg.delete_item("edges", children_only=True) # clear
        dpg.delete_item("verts", children_only=True) # clear
        dpg.delete_item("debug", children_only=True) # clear
        
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
            
            colour = {"DESERT": (204, 176, 104, 255),
                      "WOOD":   (45,  82,  44,  255),
                      "WOOL":   (82,  230, 78,  255),
                      "BRICK":  (204, 82,  20,  255),
                      "ORE":    (115, 131, 156, 255),
                      "GRAIN":  (237, 237, 69,  255)}[hex.resource.name]
            
            dpg.draw_polygon(vert_positions, fill=colour, parent="hexes", color=(0,0,0,0))
            
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
                dpg.draw_text((hex.relative_pos[0]*size + center[0], hex.relative_pos[1]*size + center[1]), f"{hex.diceValue}", color=col, size=size/4, parent="debug")
                
            
            # debug text
            #dpg.draw_text((hex.relative_pos[0]*size + center[0], hex.relative_pos[1]*size + center[1]), f"{hex_i}", color=(0, 0, 0, 255), size=size/8, parent="debug")
        
        for vert_i, vert in enumerate(self.verts):
            pos = [i*size for i in vert.relative_pos]
            
            if vert.structure.owner != Colour.NONE:
                colour = {"RED":    (255, 0,   0,   255),
                          "ORANGE": (255, 127, 44,  255),
                          "BLUE":   (0,   0,   255, 255),
                          "WHITE":  (255, 255, 255,  255)}[vert.structure.owner.name]
                
                dpg.draw_circle((vert.relative_pos[0]*size + center[0], vert.relative_pos[1]*size + center[1]), size/6, fill=colour, parent="verts", color=(0,0,0,0))
            
            if vert.structure.type == Building.CITY:
                dpg.draw_circle((vert.relative_pos[0]*size + center[0], vert.relative_pos[1]*size + center[1]), size/8, fill=(0,0,0,255), parent="verts", color=(0,0,0,0))
            
            #dpg.draw_text((vert.relative_pos[0]*size + center[0], vert.relative_pos[1]*size + center[1]), f"{vert_i}", color=(255, 0, 0, 255), size=20, parent="debug")
            
        for edge_i, edge in enumerate(self.edges):
            if edge.structure.owner != Colour.NONE:
                colour = {"RED":    (255, 0,   0,   255),
                          "ORANGE": (255, 127, 0,   255),
                          "BLUE":   (0,   0,   255, 255),
                          "WHITE":  (255, 255, 255,  255)}[edge.structure.owner.name]
                
                p0 = (self.verts[edge.verts[0]].relative_pos[0]*size + center[0], self.verts[edge.verts[0]].relative_pos[1]*size + center[1])
                p1 = (self.verts[edge.verts[1]].relative_pos[0]*size + center[0], self.verts[edge.verts[1]].relative_pos[1]*size + center[1])
                    
                dpg.draw_line(p0, p1, thickness=size/12, color=colour, parent="edges")

def safe_copy(board: Board):
    new_board = deepcopy(board)
    new_board.development_cards = [Development_card.NONE]*len(new_board.development_cards) # don't reveal the stack of developmeant cards
    

if __name__ == "__main__":
    temp = Board()
    pprint(temp.encode())