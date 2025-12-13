import json

import requests

from prompt.agent_prompt import CLASSIFY_SYSTEM_PROMPT
from utils.helper import get_api_entry_by_llm, get_data, merge_by_qid


def question_classify(dataset, model):
    question_str = ""
    for _, data in enumerate(dataset):
        question_str += f"{data['qid']}. {data['question']}\n\n"
    system_prompt = CLASSIFY_SYSTEM_PROMPT
    user_prompt = f"""
        Danh sách các câu hỏi cần phân loại:
        {question_str}
        """
    # 4. Cấu hình Request
    headers = {
        "Authorization": model["authorization"],
        "Token-id": model["tokenId"],
        "Token-key": model["tokenKey"],
        "Content-Type": "application/json",
    }

    json_data = {
        "model": "vnptai_hackathon_small",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": 0,
        "n": 1,
        "max_completion_tokens": 512,
    }
    endpoint = "/v1/chat/completions/vnptai-hackathon-small"
    response = requests.post(
        f"https://api.idg.vnpt.vn/data-service{endpoint}",
        headers=headers,
        json=json_data,
    )
    response_js = response.json()
    result = json.loads(response_js["choices"][0]["message"]["content"])
    return result


def classify(data_path, model_name="LLM small"):
    """
    Args:
        data_path (_str_): Path to dataset need classifying
        model_name (_str_): Name of VNPT model that you want to use

    Returns:
        list(_json-object_): Dataset is already joined with label for each item
    """
    vnpt_model = get_api_entry_by_llm(model_name)
    data = get_data(data_path)

    BATCH_SIZE_CLASSIFY = 20
    classified_results = []

    print(f"{int(len(data) / BATCH_SIZE_CLASSIFY)} batches")

    for i in range(0, len(data), BATCH_SIZE_CLASSIFY):
        print(f"Processing batch {i / BATCH_SIZE_CLASSIFY}")
        if i + BATCH_SIZE_CLASSIFY > len(data):
            result = question_classify(data[i : len(data)], vnpt_model)
            classified_results.extend(result)
        else:
            result = question_classify(data[i : (i + BATCH_SIZE_CLASSIFY)], vnpt_model)
            classified_results.extend(result)

    classified_data = merge_by_qid(data, classified_results)
    return classified_data


if __name__ == "__main__":
    data_path = "data/test1.json"
    classified = classify(data_path)

    import os

    output_folder = "processed_data_single_attempt"
    output_file = "1.json"
    output_path = os.path.join(output_folder, output_file)

    os.makedirs(output_folder, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=4, ensure_ascii=False)
