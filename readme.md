# Computer Science NEA: Catan AI

## Project Idea & Overview

This is an AI to play the boardgame Catan, it consists of 3 main files, each serving a different purpose.

## Running

you will need to install python 3.13 or above and the dearpygui library, this can be installed with `pip install dearpygui`. Then just run `AI_benchmarking.py`.

## Useful Sites

- [Catan wiki](https://en.wikipedia.org/wiki/Catan)
- [Catan rules](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf)
- [Gui library github](https://github.com/hoffstadt/DearPyGui)
- [Gui library documentation](https://dearpygui.readthedocs.io/en/latest/)

## Documentation

### AI_benchmarking.py

- lets 4 AIs play against each other, or a player to play against 3 AIs

### src

- folder to hold backend scripts
- to write a custom AI, create a subclass in ai.py