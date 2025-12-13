#!/usr/bin/env python3
"""
Read a directory tree like:
  extracted/
    AA/
      wiki_00
      wiki_01
    AB/
      wiki_00
      ...
Parse each wiki_* file (contains many <doc ...>...</doc>) and
export each <doc> as its own JSON file and create a .jsonl per wiki file.

Usage:
  python split_wiki_docs.py
"""

import html
import json
import re
from pathlib import Path
from typing import Dict, Iterator, List

from tqdm import tqdm

# =========== CONFIG ===========
INPUT_ROOT = Path("Wiki/extracted")  # point this at your extracted folder
OUTPUT_ROOT = Path("Wiki/processed_docs")  # where we'll write per-doc JSON files
WRITE_JSONL = True  # also write one .jsonl file per wiki file (each line = one doc)
# ==============================

# Regex to capture <doc ...> ... </doc>
DOC_RE = re.compile(r"<doc\s+([^>]*)>(.*?)</doc>", flags=re.DOTALL | re.IGNORECASE)
ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')  # capture key="value"


def is_trivial_doc(doc: dict) -> bool:
    """
    Skip docs that contain only 1 line of text (title only or empty).
    """
    text = doc.get("text", "").strip()
    if not text:
        return True

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) <= 1:
        return True

    title = doc.get("attrs", {}).get("title", "").strip()
    if len(lines) == 1 and lines[0].lower() == title.lower():
        return True

    return False


def parse_doc_file_text(text: str) -> List[Dict]:
    """
    Parse string containing many <doc ...>...</doc> blocks.
    Return list of dicts: {"attrs": {...}, "text": "..." }
    """
    docs = []
    for m in DOC_RE.finditer(text):
        attr_text = m.group(1)
        body = m.group(2).strip()
        attrs = {k: v for k, v in ATTR_RE.findall(attr_text)}
        body = html.unescape(body)
        docs.append({"attrs": attrs, "text": body})
    return docs


def parse_doc_file_path(path: Path) -> List[Dict]:
    """Read file and parse docs. Returns empty list on error."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] Unable to read {path}: {e}")
        return []
    return parse_doc_file_text(text)


def iter_wiki_files(root: Path) -> Iterator[Path]:
    """Yield all files under root matching 'wiki*' (non-recursive into hidden)."""
    if not root.exists():
        raise FileNotFoundError(f"Input root not found: {root}")
    for child in sorted(root.rglob("wiki_*")):
        if child.is_file():
            yield child


def make_output_paths(input_file: Path, output_root: Path):
    """
    Given input e.g. extracted/AA/wiki_00
    Create output dir: output_root/AA/wiki_00_docs/
    Return (out_dir, jsonl_path)
    """
    # find relative path under INPUT_ROOT's parent (so we preserve AA/... structure)
    try:
        rel = input_file.relative_to(INPUT_ROOT)
    except Exception:
        # fallback: just use name
        rel = Path(input_file.name)
    # create directory path like output_root/AA/wiki_00_docs
    parent_parts = rel.parent.parts  # e.g. ("AA",)
    out_dir = output_root.joinpath(*parent_parts, input_file.stem + "_docs")
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_root.joinpath(*parent_parts, input_file.stem + ".jsonl")
    return out_dir, jsonl_path


def save_doc_json(doc: Dict, out_dir: Path, idx: int):
    """
    Save a single doc dict to out_dir with filename: <docid>_<idx>.json
    Use doc['attrs'].get('id') or uuid-like fallback.
    """
    attrs = doc.get("attrs", {})
    doc_id = (
        attrs.get("id") or attrs.get("docid") or attrs.get("curid") or f"noid_{idx}"
    )
    # sanitize filename (very simple)
    safe_id = str(doc_id).replace("/", "_").replace(" ", "_")
    filename = f"doc_{safe_id}_chunk_{idx}.json"
    fp = out_dir / filename
    # Ensure we don't lose anything: write attrs + text
    out = {"attrs": attrs, "text": doc.get("text", "")}
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


def process_all(input_root: Path, output_root: Path, write_jsonl: bool = True):
    files = list(iter_wiki_files(input_root))
    print(f"Found {len(files)} wiki files under {input_root}")
    for wiki_file in tqdm(files, desc="Processing wiki files"):
        raw_docs = parse_doc_file_path(wiki_file)
        docs = [d for d in raw_docs if not is_trivial_doc(d)]

        if not docs:
            continue
        out_dir, jsonl_path = make_output_paths(wiki_file, output_root)
        # Save each doc individually
        for i, doc in enumerate(docs):
            save_doc_json(doc, out_dir, i)
        # Optionally write one .jsonl (newline delimited) file per input wiki filecd
        if write_jsonl:
            try:
                with jsonl_path.open("w", encoding="utf-8") as fh:
                    for doc in docs:
                        fh.write(json.dumps(doc, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[WARN] Failed to write jsonl {jsonl_path}: {e}")


if __name__ == "__main__":
    INPUT_ROOT = Path(INPUT_ROOT)
    OUTPUT_ROOT = Path(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    process_all(INPUT_ROOT, OUTPUT_ROOT, WRITE_JSONL)
    print("Done. Output root:", OUTPUT_ROOT)
