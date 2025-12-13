#!/usr/bin/env bash
set -e
set -x


python3 infer.py \
    --input processed_data/classified_test.json \
    --output prediction/test_pr_1.csv \
    --llm "LLM large" \
    --start 0 \
    --end 200