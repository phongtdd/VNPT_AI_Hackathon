import json
import os

import faiss
import numpy as np
from tqdm import tqdm

from core.llm_interface import Embedding_VNPTAI

# ================= CONFIG =================
CHUNK_ROOT = "Wiki/chunks/AA"
OUT_DIR = "Wiki/data"
# =========================================

os.makedirs(OUT_DIR, exist_ok=True)

embedding_model = Embedding_VNPTAI(embedding_name="LLM embedings")


def load_chunks(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".json"):
                with open(os.path.join(dirpath, f), "r", encoding="utf-8") as fp:
                    for item in json.load(fp):
                        yield item


def main():
    print("🔹 Loading chunks...")
    chunks = list(load_chunks(CHUNK_ROOT))

    texts = [f"passage: {c['text']}" for c in chunks]
    metadata = [
        {
            "source": c["source"],
            "chunk_id": c["chunk_id"],
        }
        for c in chunks
    ]

    print(f"✅ Total chunks: {len(texts)}")

    print("🔹 Embedding...")
    embeddings = embedding_model.get_batch_embeddings(texts)
    faiss.normalize_L2(embeddings)

    assert embeddings.shape[0] == len(texts)

    print("🔹 Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, f"{OUT_DIR}/wiki.index")

    with open(f"{OUT_DIR}/wiki_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("✅ FAISS index built successfully")


if __name__ == "__main__":
    main()
