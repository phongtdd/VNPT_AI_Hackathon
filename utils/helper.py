import json


def get_api_entry_by_llm(llm_name, path="api-keys.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON phải là dạng list: [{}, {}, ...]")

    for item in data:
        if item.get("llmApiName") == llm_name:
            return item

    return None


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
