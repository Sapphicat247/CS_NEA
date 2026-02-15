# Computer Science NEA

## Project Idea & Overview

This is an AI to play the boardgame Catan, it consists of 3 main files, each serving a different purpose.

## Running

you will need to install python 3.13 or above and dearpygui, this can be installed after python by running `py -m pip install dearpygui`

## Useful Sites

- [Catan wiki](https://en.wikipedia.org/wiki/Catan)
- [Catan rules](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf)
- [Gui library github](https://github.com/hoffstadt/DearPyGui)
- [Gui library documentation](https://dearpygui.readthedocs.io/en/latest/)

## Documentation

### AI_benchmarking.py

- lets 4 AIs play against each other, this allows you to test improvments to their algorithms and could be used to implement re-enforcement learning
- these AIs can be users or bots, as they are both just superclasses.

### src

- folder to hold backend scripts
- to write a custom AI, create a subclass in ai.py