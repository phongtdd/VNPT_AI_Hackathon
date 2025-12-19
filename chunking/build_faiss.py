import os, json
import numpy as np
import faiss
from tqdm import tqdm
import argparse
from core.llm_interface import Embedding_VNPTAI

def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def batched(it, batch_size):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= batch_size:
            yield buf
            buf = []
    if buf:
        yield buf

def build_faiss(
    jsonl_path,
    out_dir,
    index_name,
    batch_size=512,
    use_ivf=False,
    nlist=4096,          # IVF clusters
    train_size=200_000,  # samples for training IVF
):
    os.makedirs(out_dir, exist_ok=True)

    embedder = Embedding_VNPTAI(
        embedding_name="LLM embedings",
        max_workers=8,
    )

    index_path = os.path.join(out_dir, f"{index_name}.index")
    meta_path  = os.path.join(out_dir, f"{index_name}_metadata.jsonl")

    # 1) Create / init index lazily after we know dim
    index = None
    dim = None

    # 2) If IVF: collect a training sample first (streaming, bounded RAM)
    train_texts = []
    if use_ivf:
        for batch in tqdm(batched(iter_jsonl(jsonl_path), batch_size), desc="Collect IVF train sample"):
            for obj in batch:
                train_texts.append(f"passage: {obj['text']}")
                if len(train_texts) >= train_size:
                    break
            if len(train_texts) >= train_size:
                break

        train_emb = embedder.embed_texts(train_texts)
        train_emb = np.asarray(train_emb, dtype="float32")
        faiss.normalize_L2(train_emb)
        dim = train_emb.shape[1]

        quantizer = faiss.IndexFlatIP(dim)
        index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
        index.train(train_emb)
        del train_emb, train_texts

    # 3) Main pass: stream -> batch embed -> normalize -> add -> write metadata lines
    total = 0
    with open(meta_path, "w", encoding="utf-8") as mf:
        for batch in tqdm(batched(iter_jsonl(jsonl_path), batch_size), desc="Embedding + Indexing"):
            texts = [f"passage: {obj['text']}" for obj in batch]

            emb = embedder.embed_texts(texts)
            emb = np.asarray(emb, dtype="float32")

            if index is None:
                dim = emb.shape[1]
                if use_ivf:
                    raise RuntimeError("IVF index should have been initialized in training step.")
                index = faiss.IndexFlatIP(dim)

            faiss.normalize_L2(emb)
            index.add(emb)

            # stream metadata out (jsonl)
            for obj in batch:
                meta = {
                    "id": obj.get("id"),
                    "dataset": obj.get("dataset"),
                    "length": obj.get("length"),
                    # optionally DON'T store full text to reduce file size
                    "text": obj.get("text"),
                }
                mf.write(json.dumps(meta, ensure_ascii=False) + "\n")

            total += len(batch)

    faiss.write_index(index, index_path)
    print(f"Done. Total vectors: {total}")
    print(f"Index: {index_path}")
    print(f"Metadata: {meta_path}")


def parse_args():
    p = argparse.ArgumentParser("Build FAISS index from JSONL (streaming + batching)")

    p.add_argument("--data-jsonl", required=True, help="Path to input JSONL chunk file")
    p.add_argument("--out-dir", default="faiss_data", help="Output directory")
    p.add_argument("--index-name", default="faiss_index", help="FAISS index name (without extension)")

    p.add_argument("--batch-size", type=int, default=512, help="Embedding batch size (controls RAM)")
    p.add_argument("--use-ivf", action="store_true", help="Use IVF index (faster search for large corpora)")
    p.add_argument("--nlist", type=int, default=4096, help="IVF: number of clusters")
    p.add_argument("--train-size", type=int, default=200_000, help="IVF: number of samples used to train")

    return p.parse_args()


def main():
    args = parse_args()
    build_faiss(
        jsonl_path=args.data_jsonl,
        out_dir=args.out_dir,
        index_name=args.index_name,
        batch_size=args.batch_size,
        use_ivf=args.use_ivf,
        nlist=args.nlist,
        train_size=args.train_size,
    )


if __name__ == "__main__":
    main()
