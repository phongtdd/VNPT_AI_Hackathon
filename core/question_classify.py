import json
from typing import Literal

from tqdm import tqdm

from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import CLASSIFY_SYSTEM_PROMPT
from utils.helper import classify_data, get_data, merge_by_qid
from typing import List, Dict, Any, Callable, Optional
import re
import argparse

def question_classify(dataset: list[dict[str, Any]], llm: LLM_VNPTAI):
    question_str = ""
    for _, data in enumerate(dataset):
        question_str += f"{data['qid']}. {data['question']}\n  Lựa chọn:\n {data['choices']} \n\n"
    user_prompt = f"""
        Danh sách các câu hỏi cần phân loại:
        {question_str}
        """
    response = llm.get_single_answer(user_prompt)
    result = json.loads(response)
    return result

def classify_rag(questions: List[Dict[str, Any]]):
    RAG_PREFIX_PATTERN = re.compile(r"^\s*đoạn\s+thông\s+tin\s*:\s*", re.IGNORECASE)

    rag_question = []
    remain_question= []

    for i, q in enumerate(questions):
        is_rag = bool(RAG_PREFIX_PATTERN.search(q["question"]))
        if is_rag:
            q["label"] = "RAG"
            rag_question.append(q)
        else:
            remain_question.append(q)
    return rag_question, remain_question

def classify(
    data_path,
    model_name: Literal["LLM large", "LLM small"] = "LLM small",
    batch_size: int = 20,
):
    data = get_data(data_path)
    rag_question, remain_question = classify_rag(data)
    print(f"RAG question: {len(rag_question)}")
    print(f"Remain question: {len(remain_question)}")
    llm = LLM_VNPTAI(
        llm_name=model_name,
        system_prompt=CLASSIFY_SYSTEM_PROMPT,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        max_completion_tokens=512,
    )

    BATCH_SIZE_CLASSIFY = batch_size
    remain_classified_results = []

    total_batches = (len(remain_question) + BATCH_SIZE_CLASSIFY - 1) // BATCH_SIZE_CLASSIFY
    print(CLASSIFY_SYSTEM_PROMPT)
    for i in tqdm(
        range(0, len(remain_question), BATCH_SIZE_CLASSIFY),
        total=total_batches,
        desc="Classifying questions",
        unit="batch",
    ):
        batch = remain_question[i : i + BATCH_SIZE_CLASSIFY]
        result = question_classify(batch, llm)
        print(result)
        remain_classified_results.extend(result)
    remain_classified_results.extend(rag_question)
    classified_data = merge_by_qid(data, remain_classified_results)
    return classified_data


def seperate_data(data_path, output_dir="seperated_data", batch_size: int = 20):
    classified = classify(data_path, batch_size=batch_size)
    classify_data(classified, output_dir=output_dir)
    print(f"Data separated and saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True, help="Path to test dataset JSON")
    parser.add_argument("--output_dir", required=False, help="Path to save predictions")

    args = parser.parse_args()

    if args.output_dir:
        seperate_data(args.data_path, args.output_dir)
    else:
        seperate_data(args.data_path)