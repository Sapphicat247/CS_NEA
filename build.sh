#!/usr/bin/env bash

echo "started compiliation"

python3 -m PyInstaller --onefile --optimize 2 AI_benchmarking.py

echo "done"