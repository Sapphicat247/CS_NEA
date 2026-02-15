#!/bin/bash

for i in {1..200}; do
    result=$(python3 ./AI_benchmarking.py)
    echo $result
    echo $result | grep -oE "[0-9]+\.[0-9]+" >> timing.txt
    echo $result | grep -oE "RED|ORAGE|BLUE|WHITE|NONE" >> winners.txt
done