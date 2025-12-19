#!/usr/bin/env bash
set -e
set -x

# -------- DEFAULT CONFIGURATION --------
DATASET="namnguyenvu/ho-chi-minh-dataset"
TEXT_FIELD="text"
SPLIT="train"
CHUNKING_DIR="chunking_data"
FAISS_OUT_DIR="faiss_data"

# -------- READ CUSTOM ARGUMENTS --------
# Usage: ./run_preprocess.sh <dataset> [text_field] [split]
if [ $# -ge 1 ]; then
    DATASET="$1"
fi

if [ $# -ge 2 ]; then
    TEXT_FIELD="$2"
fi

if [ $# -ge 3 ]; then
    SPLIT="$3"
fi

# -------- STEP 0: safe names --------
# Make dataset name filesystem-safe
SAFE_DATASET="${DATASET//\//__}"

# -------- STEP 1: Chunk dataset --------
mkdir -p "$CHUNKING_DIR"
python3 chunking/build_chunk.py \
    --dataset "$DATASET" \
    --text-field "$TEXT_FIELD" \
    --split "$SPLIT" \
    --out-dir "$CHUNKING_DIR"

# -------- STEP 2: Detect chunked JSONL --------
CHUNK_FILE=$(ls "$CHUNKING_DIR"/*.jsonl | head -n 1)
if [ ! -f "$CHUNK_FILE" ]; then
    echo "❌ Chunked JSONL file not found in $CHUNKING_DIR"
    exit 1
fi

# -------- STEP 3: Build FAISS index --------
mkdir -p "$FAISS_OUT_DIR"
INDEX_NAME="faiss_index_${SAFE_DATASET}"

python3 -m chunking.build_faiss \
    --data-jsonl "$CHUNK_FILE" \
    --out-dir "$FAISS_OUT_DIR" \
    --index-name "$INDEX_NAME"

echo "✅ Preprocessing complete."
echo "Chunks: $CHUNK_FILE"
echo "FAISS Index: $FAISS_OUT_DIR/$INDEX_NAME.index"
