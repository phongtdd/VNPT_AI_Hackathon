import argparse
import hashlib
import json
import os
import re

from datasets import load_dataset
from tqdm import tqdm

OVERLAP_PARAGRAPHS = 1


def normalize(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def split_sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?…])\s+", text)


# ================= Chunking =================
def chunk_document(
    text: str,
    min_chars: int,
    max_chars: int,
    overlap_paragraphs: int = OVERLAP_PARAGRAPHS,
) -> list[str]:
    text = normalize(text)
    paragraphs = split_paragraphs(text)

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        # Large paragraph → sentence split
        if para_len > max_chars:
            for sent in split_sentences(para):
                sent_len = len(sent)

                if current_len + sent_len > max_chars:
                    if current_len >= min_chars:
                        chunks.append(" ".join(current))
                    current = []
                    current_len = 0

                current.append(sent)
                current_len += sent_len
            continue

        if current_len + para_len > max_chars:
            if current_len >= min_chars:
                chunks.append("\n\n".join(current))

            overlap = current[-overlap_paragraphs:] if overlap_paragraphs > 0 else []
            current = overlap.copy()
            current_len = sum(len(p) for p in current)

        current.append(para)
        current_len += para_len

    if current_len >= min_chars:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_name(name: str) -> str:
    """Make dataset name filesystem-safe"""
    return name.replace("/", "__")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Chunk HuggingFace dataset into JSONL for FAISS"
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="HF dataset name (e.g. namnguyenvu/ho-chi-minh-dataset)",
    )

    parser.add_argument(
        "--text-field",
        default="text",
        help="Text field name in dataset (default: text)",
    )

    parser.add_argument(
        "--split",
        default="train",
        help="Dataset split (default: train)",
    )

    parser.add_argument(
        "--out-dir",
        default="chunking_data",
        help="Output directory",
    )

    parser.add_argument(
        "--min-chars",
        type=int,
        default=50,
        help=f"Minimum characters per chunk (default: {50})",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=2400,
        help=f"Maximum characters per chunk (default: {2400})",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    dataset_name = args.dataset
    split = args.split
    text_field = args.text_field
    min_chars = args.min_chars
    max_chars = args.max_chars

    print(f"🔹 Loading dataset: {dataset_name} [{split}]")
    ds = load_dataset(dataset_name)[split]
    # ds = load_dataset("json", data_files=dataset_name, split=split)

    safe_dataset = safe_name(dataset_name)
    out_path = os.path.join(args.out_dir, f"{safe_dataset}.jsonl")
    os.makedirs(args.out_dir, exist_ok=True)

    total_chunks = 0

    print("🔹 Chunking documents...")
    with open(out_path, "w", encoding="utf-8") as f:
        for row in tqdm(ds, desc="Chunking", unit="doc", total=len(ds)):
            text = row.get(text_field)
            if not text:
                continue

            chunks = chunk_document(text, min_chars=min_chars, max_chars=max_chars)

            for chunk in chunks:
                record = {
                    "id": chunk_id(chunk),
                    "text": chunk,
                    "dataset": dataset_name,
                    "length": len(chunk),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_chunks += 1

    print("Done")
    print(f"Output: {out_path}")
    print(f"Total chunks: {total_chunks}")


if __name__ == "__main__":
    main()
