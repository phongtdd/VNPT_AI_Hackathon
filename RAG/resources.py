from core.llm_interface import Embedding_VNPTAI
from RAG.retriever import load_faiss_multi

STORES = load_faiss_multi(index_dir="faiss_data")

CORPUS_TEXTS = {}
for store in STORES:
    name = store["name"]
    CORPUS_TEXTS[name] = [m.get("text", "") for m in store["metadata"]]

EMBEDDER = Embedding_VNPTAI(embedding_name="LLM embedings", max_workers=4)
