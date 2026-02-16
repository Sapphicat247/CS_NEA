#!/usr/bin/env bash

test_f () {
    result=$(python3 ./AI_benchmarking.py --onlyAIs --noGUI)
    echo "$1: $result"
    echo $result | grep -oE "[0-9]+\.[0-9]+" >> "timing.txt"
    echo $result | grep -oE "RED|ORANGE|BLUE|WHITE|NONE" >> "winners.txt"
}

export -f test_f

parallel test_f ::: {1..5000}