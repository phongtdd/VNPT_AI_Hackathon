#!/usr/bin/env bash
set -e
set -x

DATASET="VTSNLP/base_yTe"
text_field="text"
split="train"
out_dir="chunking_data"


python3 chunking/build_chunk.py \
    --dataset "$DATASET" \
    --text-field "$text_field" \
    --split "$split" \
    --out-dir "$out_dir" \