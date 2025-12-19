import json
from pathlib import Path

import faiss
import numpy as np


def _load_jsonl(path: Path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no} invalid JSON") from e
    return items


def load_faiss_multi(index_dir: str):
    index_dir = Path(index_dir)
    stores = []

    for domain_dir in index_dir.iterdir():
        if not domain_dir.is_dir():
            continue

        index_files = list(domain_dir.glob("*.index"))
        meta_files = list(domain_dir.glob("*_metadata.jsonl"))

        if not index_files or not meta_files:
            continue

        index = faiss.read_index(
            str(index_files[0]),
            faiss.IO_FLAG_MMAP | faiss.IO_FLAG_READ_ONLY,
        )

        metadata = _load_jsonl(meta_files[0])

        stores.append(
            {
                "name": domain_dir.name,
                "index": index,
                "metadata": metadata,
            }
        )

    if not stores:
        raise RuntimeError("No FAISS index found")

    return stores


def embed_query(embedder, question: str):
    vec = embedder.embed_texts([f"passage: {question}"])
    faiss.normalize_L2(vec)
    return vec

DOMAIN_THRESHOLDS = {
    "law": 0.75,
    "medical": 0.5,
    "ho_chi_minh": 0.6,
    "civic_knowledge": 0.7,
    "political_science": 0.7
}

def retrieve_context_single_domain(
    question: str,
    *,
    domain: str,
    stores,
    embedder,
    corpus_texts,
    top_k=5,
    faiss_k=50,
)->str:
    global DOMAIN_THRESHOLDS
    store = next(s for s in stores if s["name"] == domain)

    query_vec = embed_query(embedder, question)

    # ---- FAISS search ----
    threshold = DOMAIN_THRESHOLDS.get(domain)
    scores, ids = store["index"].search(query_vec, faiss_k)
    pairs = list(zip(scores[0], ids[0]))

    # keep only scores above threshold
    good = [(s, i) for (s, i) in pairs if i != -1 and s >= threshold]
    good = sorted(good, reverse=True)[:top_k]

    if not good:
        return ""

    ids = [i for (s, i) in good]

    texts = corpus_texts[domain]

    return "\n\n".join(texts[i] for i in ids)