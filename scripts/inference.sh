#!/usr/bin/env bash
set -e
set -x


python3 inference.py \
    --input data/test.json \
    --separated_dir data/separated_data \
    --output data/prediction.csv \
    --llm "LLM large"