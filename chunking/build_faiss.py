import argparse
import json
import os

import faiss
from tqdm import tqdm

from core.llm_interface import Embedding_VNPTAI


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def build_faiss(jsonl_path, out_dir, index_name):
    os.makedirs(out_dir, exist_ok=True)

    embedder = Embedding_VNPTAI(
        embedding_name="LLM embedings",
        max_workers=4,
    )

    texts, metadata = [], []

    for obj in tqdm(load_jsonl(jsonl_path), desc="Reading JSONL"):
        texts.append(f"passage: {obj['text']}")
        metadata.append(
            {
                "id": obj["id"],
                "dataset": obj.get("dataset"),
                "text": obj.get("text"),
                "length": obj.get("length"),
            }
        )

    print(f"Total chunks: {len(texts)}")

    embeddings = embedder.embed_texts(texts)

    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, f"{out_dir}/{index_name}.index")

    with open(f"{out_dir}/{index_name}_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("FAISS index built successfully")


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
