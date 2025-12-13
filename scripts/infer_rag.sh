#!/usr/bin/env bash
set -e
set -x


python3 -m RAG.infer \
    --input data/test.json \
    --output prediction/test_rag_40_200_1.csv \
    --llm "LLM large" \
    --start 40 \
    --end 200 \
    --use_sim