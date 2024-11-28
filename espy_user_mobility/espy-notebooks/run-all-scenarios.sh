#!/bin/bash

THERSHOLDS=(0.2 0.4 0.6 0.8)
RECENCIES=(8 16 32 64)
STEPS_LIMIT=2160

for threshold in "${THERSHOLDS[@]}"; do
    for recency in "${RECENCIES[@]}"; do
        echo "Running scenario with threshold: $threshold and recency: $recency"
        screen -dmLS "config-$threshold-$recency" .venv/bin/python3 main.py "$threshold" "$recency" "$STEPS_LIMIT"
    done
done
