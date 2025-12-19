#!/usr/bin/env bash
set -e
set -x

input_file="${1:-private_test.json}"

separated_dir="separated_data"
output_file="submission.csv"
llm="LLM large"

python3 predict.py \
    --input "$input_file" \
    --separated_dir "$separated_dir" \
    --output "$output_file" \
    --llm "$llm"