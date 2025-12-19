#!/usr/bin/env bash
set -e
set -x

chunking_dir="chunking_data"
data_jsonl="vbnq_2023_2025.jsonl"
out_dir="faiss_data"

python3 -m chunking.build_faiss \
    --data-jsonl "$chunking_dir/$data_jsonl" \
    --out-dir "$out_dir" \
    --index-name "faiss_index_${data_jsonl%.jsonl}" \
    