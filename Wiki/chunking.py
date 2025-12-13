import json
import re

HEADING_RE = re.compile(r"^[A-ZÀ-Ỵ][^.\n]{1,100}\.$")


def is_heading(line):
    return bool(HEADING_RE.match(line))


def heading_level(title):
    words = title.split()
    if len(words) <= 2:
        return 1
    elif len(words) <= 4:
        return 2
    else:
        return 3


def build_hierarchy(text):
    lines = text.splitlines()

    root = {"level": 0, "title": "Lead", "content": [], "children": []}

    stack = [root]

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if is_heading(line):
            title = line.rstrip(".")
            level = heading_level(title)

            node = {"level": level, "title": title, "content": [], "children": []}

            # Find correct parent
            while stack and stack[-1]["level"] >= level:
                stack.pop()

            stack[-1]["children"].append(node)
            stack.append(node)
        else:
            stack[-1]["content"].append(line)

    return root


def flatten_hierarchy(node, parents=None):
    parents = parents or []
    chunks = []

    path = parents[1:] + ([node["title"]] if node["level"] > 0 else [])

    if node["level"] <= 2:
        content_blocks = []

        if node["content"]:
            content_blocks.append("\n".join(node["content"]))

        for child in node.get("children", []):
            if child["level"] == 3:
                content_blocks.append(
                    f"{child['title']}\n" + "\n".join(child["content"])
                )

        if content_blocks:
            text = f"{node['title']}\n\n" + "\n\n".join(content_blocks)

            chunks.append(
                {
                    "text": text,
                    "metadata": {
                        "lang": "vi",
                        "level": node["level"],
                        "path": " > ".join(path),
                        "h1": path[0] if len(path) > 0 else None,
                        "h2": path[1] if len(path) > 1 else None,
                        "h3": None,
                    },
                }
            )

    # Recurse ONLY into children that are not H3
    for child in node.get("children", []):
        if child["level"] <= 2:
            chunks.extend(flatten_hierarchy(child, parents + [node["title"]]))

    return chunks


def merge_chunks(chunks, max_chars=1800):
    merged = []
    buffer = ""
    meta = None
    count = 0

    for c in chunks:
        if len(buffer) + len(c["text"]) > max_chars:
            merged.append(
                {"id": f"chunk-{len(merged)}", "text": buffer.strip(), "metadata": meta}
            )
            buffer = c["text"]
            meta = c["metadata"]
            count = 0
        else:
            buffer += "\n\n" + c["text"]
            meta = c["metadata"]
            count += 1

    if buffer:
        merged.append({"id": f"chunk-{len(merged)}", "text": buffer.strip()})

    return merged


MIN_CHARS = 0
MAX_CHARS = 5000


def normalize(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def chunk_document(text: str) -> list[dict]:
    tree = build_hierarchy(text)
    flat = flatten_hierarchy(tree)
    merged = merge_chunks(flat)

    chunks = []
    for c in merged:
        txt = normalize(c["text"])
        if MIN_CHARS <= len(txt) <= MAX_CHARS:
            chunks.append(txt)
    return chunks


if __name__ == "__main__":
    with open(
        "processed_docs/AA/wiki_00_docs/doc_13_chunk_2.json", "r", encoding="utf-8"
    ) as f:
        text = json.load(f)["text"]

    chunk_document = chunk_document(text)
    for i, chunk in enumerate(chunk_document):
        print(chunk)
        print(len(chunk))
        print("\n")

    # tree = build_hierarchy(text)
    # flat = flatten_hierarchy(tree)
    # merged = merge_chunks(flat)
    # for i, chunk in enumerate(merged):
    #     print(chunk)
    #     print("\n")
