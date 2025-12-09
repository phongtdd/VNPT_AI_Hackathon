#!/usr/bin/env bash
set -e
set -x


python3 -m RAG.infer \
    --input data/val.json \
    --output prediction/val_rag.csv \
    --llm "LLM small" \
    --start 0 \
    --end 200 \