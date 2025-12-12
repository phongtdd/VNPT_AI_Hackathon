import argparse
import csv
import os
import time
from pdb import run

from tqdm import tqdm

from core.llm_interface import LLM_VNPTAI
from post_processing import choice_to_letter
from prompt.agent_prompt import STEM_PROMPT, RAG_PROMPT
from stem_solver.stem import LLMStem
from utils.helper import get_data


def run_inference(test_path, output_path, llm_name, sleep_time=0.1):
    test_data = get_data(test_path)

    with open(output_path, "w", encoding="utf-8") as f:
        iterator = tqdm(enumerate(test_data), total=len(test_data))
        for i, test_case in iterator:
            llm = LLM_VNPTAI(llm_name=llm_name, system_prompt=RAG_PROMPT)
            answer = llm.predict(test_case, question_type="RAG")
            f.write(f"{test_case['qid'], answer}\n")

    print(f"Predictions saved to {output_path}")


def run_rag_inference(
    test_data_path, output_path, llm_name, start: int, end: int = 40, sleep_time=0.1
):
    filename = os.path.basename(test_data_path).lower()

    if "val" in filename:
        mode = "v"
    else:
        mode = "t"

    test_data = get_data(test_data_path)
    rag_data = [
        item for item in test_data if "Đoạn thông tin" in item.get("question", "")
    ]
    if start > 0:
        rag_data = rag_data[start:end]
    else:
        rag_data = rag_data[:end]
    llm = LLM_VNPTAI(llm_name=llm_name, system_prompt=RAG_PROMPT)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["qid", "answer"])
        iterator = tqdm(enumerate(rag_data), total=len(rag_data))
        for i, test_case in iterator:
            try:
                raw_answer = llm.predict(test_case, question_type="RAG")
                letter_answer = choice_to_letter(raw_answer, test_case["choices"])
            except Exception as e:
                print(f"Error processing qid {test_case['qid']}: {e}")
                letter_answer = ""
            if mode == "v":
                writer.writerow([test_case["qid"], letter_answer, test_case["answer"]])
            else:
                writer.writerow([test_case["qid"], letter_answer])

            if sleep_time:
                time.sleep(sleep_time)

    print(f"CSV saved to {output_path}")


def run_stem_inference(
    test_path, output_path, llm_name, sleep_time=0.1, start: int = 0, end: int = 0
):
    test_data = get_data(test_path)
    stem_data = [item for item in test_data if item.get("label", "") == "STEM"]
    if start > 0:
        stem_data = stem_data[start:end]
    else:
        stem_data = stem_data[:end]

    filename = os.path.basename(test_path).lower()

    if "val" in filename:
        mode = "v"
    else:
        mode = "t"

    stem_llm = LLMStem(
        llm_name=llm_name,
        system_prompt=STEM_PROMPT,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=2048,
    )

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if mode == "v":
            writer.writerow(["qid", "answer", "ground_truth"])
        else:
            writer.writerow(["qid", "answer"])
        iterator = tqdm(enumerate(stem_data), total=len(stem_data))
        for i, test_case in iterator:
            question = test_case["question"]
            choices = test_case["choices"]
            user_prompt = f"Câu hỏi:\n{question}\n\nLựa chọn:\n{choices}\n\n"
            try:
                answer = stem_llm.get_single_answer(user_prompt)
                letter = answer[0]["answer"]
            except Exception as e:
                print(f"Error processing qid {test_case['qid']}: {e}")
                letter = ""
            if mode == "v":
                writer.writerow([test_case["qid"], letter, test_case["answer"]])
            else:
                writer.writerow([test_case["qid"], letter])

            if sleep_time:
                time.sleep(sleep_time)

    print(f"Predictions saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to test dataset JSON")
    parser.add_argument("--output", required=True, help="Path to save predictions")
    parser.add_argument("--llm", default="LLM large", help="LLM model name")
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index for samples to run for testing",
    )
    parser.add_argument(
        "--end", type=int, default=0, help="End index for samples to run for testing"
    )

    args = parser.parse_args()

    # run_rag_inference(args.input, args.output, args.llm, start=args.start, end=args.end)
    run_stem_inference(
        args.input, args.output, args.llm, start=args.start, end=args.end
    )
