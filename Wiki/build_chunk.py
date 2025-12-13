import hashlib
import json
import os
import sys

from tqdm import tqdm

from Wiki.chunking import build_hierarchy, flatten_hierarchy, merge_chunks

# ================= CONFIG =================
INPUT_ROOT = "Wiki/processed_docs"
CHUNK_ROOT = "Wiki/chunks"
MIN_CHARS = 50
MAX_CHARS = 2000
OVERLAP_PARAGRAPHS = 1
# =========================================

os.makedirs(CHUNK_ROOT, exist_ok=True)


def normalize(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def load_docs(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".json"):
                yield os.path.join(dirpath, f)


def stable_chunk_id(source: str, text: str) -> str:
    return hashlib.md5(f"{source}:{text}".encode("utf-8")).hexdigest()


def split_long_chunk_semantic(text: str, max_chars: int):
    """
    Paragraph-aware splitting with strict max size and safe overlap.
    """
    lines = text.split("\n")
    if len(lines) < 2:
        return []

    title = lines[0]
    body = "\n".join(lines[1:])

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

    chunks = []
    cur = []f

    def cur_len():
        return sum(len(p) for p in cur)

    for p in paragraphs:
        if cur_len() + len(p) <= max_chars:
            cur.append(p)
        else:
            if cur:
                chunks.append(title + "\n\n" + "\n\n".join(cur))

            # overlap last paragraph(s) safely
            overlap = cur[-OVERLAP_PARAGRAPHS:] if cur else []
            cur = overlap + [p]

            # still too big → force split
            if cur_len() > max_chars:
                chunks.append(title + "\n\n" + p)
                cur = []

    if cur:
        chunks.append(title + "\n\n" + "\n\n".join(cur))

    return chunks


def chunk_document(text: str):
    tree = build_hierarchy(text)
    flat = flatten_hierarchy(tree)
    merged = merge_chunks(flat)

    chunks = []

    for c in merged:
        raw_text = c["text"]

        if len(raw_text) > MAX_CHARS:
            chunks.extend(split_long_chunk_semantic(raw_text, MAX_CHARS))
        else:
            chunks.append(raw_text)

    return chunks


def main():
    print("🔹 Chunking documents...")

    for path in tqdm(load_docs(INPUT_ROOT), file=sys.stdout, dynamic_ncols=True):
        rel = os.path.relpath(path, INPUT_ROOT)
        out_path = os.path.join(CHUNK_ROOT, rel)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        text = doc.get("text", "")
        if len(text.splitlines()) <= 1:
            continue

        chunks = chunk_document(text)

        records = []
        for c in chunks:
            c = normalize(c)

            # drop title-only or tiny chunks
            if "\n" not in c:
                continue

            if MIN_CHARS <= len(c) <= MAX_CHARS:
                records.append(
                    {
                        "chunk_id": stable_chunk_id(rel, c),
                        "text": c,
                        "source": rel,
                        "char_len": len(c),
                    }
                )

        if records:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

    print("✅ Chunking completed")


if __name__ == "__main__":
    main()
