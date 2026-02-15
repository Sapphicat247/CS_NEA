#!/bin/bash

for i in {1..200}; do
    result=$(python3 ./AI_benchmarking.py)
    echo $result
    echo $result | grep -E -o "[0-9]+\.[0-9]+" >> results.txt
done