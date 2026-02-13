# Computer Science NEA

## Project Idea & overview

This is an AI to play the boardgame Catan, it consists of 3 main files, each serving a different purpose.

I will uer R to analyse the results to work out if changes improve the disign of the AI, or not.

## Useful Sites

- [Catan wiki](https://en.wikipedia.org/wiki/Catan)
- [Gui library github](https://github.com/hoffstadt/DearPyGui)
- [Gui library documentation](https://dearpygui.readthedocs.io/en/latest/)

## Documentation

### AI_benchmarking.py

- lets 4 AIs play against each other, this allows you to test improvments to their algorithms and could be used to implement re-enforcement learning
- these AIs can be users or bots, as they are both just superclasses.

### src

- folder to hold backend scripts
- to write a custom AI, create a subclass in ai.py