#!/usr/bin/env bash
set -e
set -x


python3 inference.py \
    --separated_dir data/separated_data/test_data/STEM.json \
    --output data/prediction_STEM.csv \
    --llm "LLM large"