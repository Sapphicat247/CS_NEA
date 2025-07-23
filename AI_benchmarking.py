from src import AI, catan
import random

def rotate(l: list, n: int) -> list:
    return l[n:] + l[:n]

# create a board
board = catan.Board()

# create AIs

players: list[AI.AI] = [
    AI.AI(), # red
    AI.AI(), # orange
    AI.AI(), # blue
    AI.AI(), # white
]

# MARK: set-up phaze
# choose starting player

for i in (0, 1, 2, 3):
    print(f"{catan.Colour(i+1).name} player placing first settlement")
    v, e =  players[i].place_first_settlement()
    

for i in (3, 2, 1, 0):
    print(f"{catan.Colour(i+1).name} player placing second settlement")
    v, e =  players[i].place_second_settlement()

game_won = False

while not game_won:
    ...