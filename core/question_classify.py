import json
from typing import Literal

from tqdm import tqdm

from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import CLASSIFY_SYSTEM_PROMPT
from utils.helper import classify_data, get_data, merge_by_qid


def question_classify(dataset: list[dict[str, str]], llm: LLM_VNPTAI):
    question_str = ""
    for _, data in enumerate(dataset):
        question_str += f"{data['qid']}. {data['question']}\n\n"
    user_prompt = f"""
        Danh sách các câu hỏi cần phân loại:
        {question_str}
        """
    response = llm.get_single_answer(user_prompt)
    result = json.loads(response)
    return result


def classify(data_path, model_name: Literal["LLM large", "LLM small"] = "LLM small"):
    data = get_data(data_path)
    llm = LLM_VNPTAI(
        llm_name=model_name,
        system_prompt=CLASSIFY_SYSTEM_PROMPT,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        max_completion_tokens=512,
    )

    BATCH_SIZE_CLASSIFY = 20
    classified_results = []

    total_batches = (len(data) + BATCH_SIZE_CLASSIFY - 1) // BATCH_SIZE_CLASSIFY

    for i in tqdm(
        range(0, len(data), BATCH_SIZE_CLASSIFY),
        total=total_batches,
        desc="Classifying questions",
        unit="batch",
    ):
        batch = data[i : i + BATCH_SIZE_CLASSIFY]
        result = question_classify(batch, llm)
        classified_results.extend(result)

    classified_data = merge_by_qid(data, classified_results)
    return classified_data


def seperate_data(data_path, output_dir="seperated_data"):
    classified = classify(data_path)
    classify_data(classified, output_dir=output_dir)
    print(f"Data separated and saved to {output_dir}")
