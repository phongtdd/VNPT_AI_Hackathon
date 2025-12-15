import argparse
import json
import os

import faiss
import numpy as np
from tqdm import tqdm

from core.llm_interface import Embedding_VNPTAI


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def build_faiss(jsonl_path: str, out_dir: str, index_name: str):
    os.makedirs(out_dir, exist_ok=True)

    embedding_model = Embedding_VNPTAI(embedding_name="LLM embedings")

    print("🔹 Loading chunks...")
    texts = []
    metadata = []

    for obj in tqdm(load_jsonl(jsonl_path), desc="Reading JSONL"):
        texts.append(f"passage: {obj['text']}")
        metadata.append(
            {
                "id": obj["id"],
                "dataset": obj.get("dataset"),
                "length": obj.get("length"),
            }
        )

    print(f"✅ Total chunks: {len(texts)}")

    print("🔹 Embedding...")
    embeddings = embedding_model.get_batch_embeddings(texts)

    embeddings = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    print("🔹 Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    index_path = os.path.join(out_dir, f"{index_name}.index")
    meta_path = os.path.join(out_dir, f"{index_name}_metadata.json")

    faiss.write_index(index, index_path)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("✅ FAISS index built successfully")
    print(f"📦 Index: {index_path}")
    print(f"📄 Metadata: {meta_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Build FAISS index from JSONL chunks")

    parser.add_argument(
        "--data-jsonl",
        required=True,
        help="Path to input JSONL chunk file",
    )

    parser.add_argument(
        "--out-dir",
        default="faiss_data",
        help="Output directory",
    )

    parser.add_argument(
        "--index-name",
        default="faiss_index",
        help="FAISS index name (without extension)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    build_faiss(
        jsonl_path=args.data_jsonl, out_dir=args.out_dir, index_name=args.index_name
    )
