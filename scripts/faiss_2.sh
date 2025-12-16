#!/usr/bin/env bash
set -e
set -x

data_jsonl="chunking_data/VTSNLP__base_yTe.jsonl"
out_dir="faiss_data"


python3 -m chunking.build_faiss_2 \
    --data-jsonl "$data_jsonl" \
    --out-dir "$out_dir" \