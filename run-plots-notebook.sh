#!/bin/bash

export PROJ_DIR=$(dirname "$(readlink -f "$0")")
source .venv/bin/activate
log_dirs=$(find logs -type f -name "User.csv" -exec dirname {} \; | sed 's|^logs||' | sort | uniq)
plots_script=$(jupyter nbconvert --to python --stdout espy_user_mobility/espy-notebooks/results_plots.ipynb)
cdfs_script=$(jupyter nbconvert --to python --stdout espy_user_mobility/espy-notebooks/cdf_plots.ipynb)

while IFS= read -r line; do
    export DIR_SUFFIX="$line"
    echo "Processing $line"
    echo "$plots_script" | python3
    echo
done <<< "$log_dirs"

echo "Processing CDFs"
echo "$cdfs_script" | python3
