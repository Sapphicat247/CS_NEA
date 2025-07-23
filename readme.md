# Computer Science NEA

## Project Idea & overview

This is an AI to play the boardgame Catan, it consists of 3 main files, each serving a different purpose.

I will uer R to analyse the results to work out if changes improve the disign of the AI, or not.

## Languages & Libraries Used

- Python
  - dearpygui
  - enum
  - dataclass
  - random
- R

## Useful Sites

- [Catan wiki](https://en.wikipedia.org/wiki/Catan)
- [Gui library github](https://github.com/hoffstadt/DearPyGui)
- [Gui library documentation](https://dearpygui.readthedocs.io/en/latest/)

## Documentation

### against_AI.py

- let 1 user play against 2 - 3 AIs. This will have a GUI that emulates a game board and hand of cards etc

### AI_benchmarking.py

- makes 3 or 4 AIs play against each other, this allows you to test improvments to their algorithms and could be used to implement re-enforcement learning

### over_the_table.py

- allows you to play an irl game using a bot as a player. this will have a GUI to imput what each player does, and to update the state of the board

### src

- folder to hold scripts