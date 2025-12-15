import json
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi


def _merge_faiss_indexes(indexes: list[faiss.Index]):
    if not indexes:
        raise ValueError("No FAISS index to merge")

    base = indexes[0]

    for idx in indexes[1:]:
        base.merge_from(idx, base.ntotal)

    return base


def load_faiss(index_dir: str, index_name: str | None = None):
    index_dir = Path(index_dir)

    # ---------- Single index ----------
    if index_name:
        index_path = index_dir / f"{index_name}.index"
        meta_path = index_dir / f"{index_name}_metadata.json"

        index = faiss.read_index(str(index_path))
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return index, metadata

    # ---------- Multi index ----------
    indexes = []
    metadata = []

    for index_path in sorted(index_dir.glob("*.index")):
        meta_path = index_path.with_name(index_path.stem + "_metadata.json")

        idx = faiss.read_index(str(index_path))
        indexes.append(idx)

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata.extend(json.load(f))

    if not indexes:
        raise RuntimeError("No FAISS index found")

    merged_index = _merge_faiss_indexes(indexes)

    return merged_index, metadata


def build_bm25(corpus_texts):
    tokenized = [text.lower().split() for text in corpus_texts]
    return BM25Okapi(tokenized)


def embed_query(embedder, question: str):
    vec = embedder.embed_texts([f"passage: {question}"])
    faiss.normalize_L2(vec)
    return vec


def _min_max_normalize(scores):
    min_s, max_s = min(scores), max(scores)
    if max_s - min_s == 0:
        return [0.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


def retrieve_context_faiss_hybrid(
    question: str,
    *,
    embedder,
    faiss_index,
    metadata,
    bm25,
    corpus_texts,
    top_k: int = 5,
    faiss_k: int = 20,
    alpha: float = 0.6,  # semantic weight
):
    """
    alpha ↑ → more semantic (FAISS)
    alpha ↓ → more lexical (BM25)
    """

    # ---------- 1. FAISS semantic search ----------
    query_vec = embed_query(embedder, question)
    faiss_scores, faiss_ids = faiss_index.search(query_vec, faiss_k)

    faiss_scores = faiss_scores[0]
    faiss_ids = faiss_ids[0]

    semantic_scores = {
        idx: float(score) for idx, score in zip(faiss_ids, faiss_scores) if idx != -1
    }

    # ---------- 2. BM25 lexical search ----------
    tokenized_query = question.lower().split()
    bm25_raw_scores = bm25.get_scores(tokenized_query)

    # Restrict BM25 to FAISS candidates (important!)
    lexical_scores = {idx: bm25_raw_scores[idx] for idx in semantic_scores.keys()}

    # ---------- 3. Normalize scores ----------
    def normalize(d):
        if not d:
            return {}
        vals = np.array(list(d.values()))
        if vals.max() - vals.min() < 1e-8:
            return {k: 0.0 for k in d}
        return {k: (v - vals.min()) / (vals.max() - vals.min()) for k, v in d.items()}

    semantic_norm = normalize(semantic_scores)
    lexical_norm = normalize(lexical_scores)

    # ---------- 4. Hybrid fusion ----------
    hybrid_scores = {
        idx: alpha * semantic_norm.get(idx, 0.0)
        + (1 - alpha) * lexical_norm.get(idx, 0.0)
        for idx in semantic_scores
    }

    # ---------- 5. Rank ----------
    ranked_ids = sorted(
        hybrid_scores,
        key=lambda i: hybrid_scores[i],
        reverse=True,
    )[:top_k]

    # ---------- 6. Build context ----------
    contexts = []
    for idx in ranked_ids:
        contexts.append(corpus_texts[idx])

    return "\n\n".join(contexts)
