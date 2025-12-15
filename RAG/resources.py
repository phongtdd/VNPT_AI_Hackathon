# rag/resources.py

from core.llm_interface import Embedding_VNPTAI
from RAG.retriever import build_bm25, load_faiss

# -------- Load FAISS  --------
FAISS_INDEX, METADATA = load_faiss(index_dir="faiss_data")

# -------- Corpus texts --------
CORPUS_TEXTS = [m["text"] if "text" in m else "" for m in METADATA]

# -------- Embedder --------
EMBEDDER = Embedding_VNPTAI(
    embedding_name="LLM embedings",
    max_workers=4,
)

# -------- BM25 --------
BM25 = build_bm25(CORPUS_TEXTS)
