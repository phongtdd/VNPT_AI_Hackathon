import json
import os
from collections import defaultdict


def get_data(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON phải là dạng list: [{}, {}, ...]")

    return data


def merge_by_qid(list1, list2):
    dict2 = {item["qid"]: item for item in list2}

    merged = []
    for obj in list1:
        qid = obj["qid"]
        if qid in dict2:
            merged.append({**obj, **dict2[qid]})  # merge dictionary
        else:
            merged.append(obj)  # nếu không có qid matching

    return merged


def classify_data(
    data,
    output_dir="seperated_data",
    merge_labels=("Compulsory", "Multi-Domain"),
    merged_label_name="Multi-Domain",
):
    os.makedirs(output_dir, exist_ok=True)

    grouped_data = defaultdict(list)

    for item in data:
        label = item["label"]

        if label in merge_labels:
            item = item.copy()
            item["label"] = merged_label_name
            grouped_data[merged_label_name].append(item)
        else:
            grouped_data[label].append(item)

    for label, items in grouped_data.items():
        filename = f"{label}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)


def load_separated_data(separated_dir):
    for filename in os.listdir(separated_dir):
        if not filename.endswith(".json"):
            continue

        label = filename.replace(".json", "")
        file_path = os.path.join(separated_dir, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        yield label, data
