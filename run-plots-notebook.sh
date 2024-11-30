#!/bin/bash

log_dirs=$(find logs -type f -name "User.csv" -exec dirname {} \; | sed 's|^logs||' | sort | uniq)
script=$(jupyter nbconvert --to python --stdout espy_user_mobility/espy-notebooks/results_plots.ipynb)

while IFS= read -r line; do
    export DIR_SUFFIX="$line"
    echo "Processing $line"
    echo "$script" | python3 && echo "$line" >> done-dirs.txt
    echo
done <<< "$log_dirs"
