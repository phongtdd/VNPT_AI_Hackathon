import argparse
import csv
import os
import time

from tqdm import tqdm

from core.llm_interface import LLM_VNPTAI
from post_processing import choice_to_letter
from prompt.agent_prompt import SYSTEM_RAG_PROMPT, USER_RAG_PROMPT
from RAG.get_top_param import top_similarity
from utils.helper import get_data


def run_rag_inference(
    test_data_path,
    output_path,
    llm_name,
    start: int,
    end: int = 40,
    sleep_time=0.1,
    use_sim=False,
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
    llm = LLM_VNPTAI(llm_name=llm_name, system_prompt=SYSTEM_RAG_PROMPT)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if mode == "v":
            writer.writerow(["qid", "answer", "ground_truth"])
        else:
            writer.writerow(["qid", "answer"])
        iterator = tqdm(enumerate(rag_data), total=len(rag_data))
        for i, test_case in iterator:
            if use_sim:
                questions = test_case["question"]
                choices = test_case["choices"]
                start_key = "Đoạn thông tin:"
                end_key = "Câu hỏi:"
                start_index = questions.find(start_key)
                end_index = questions.find(end_key)
                content = questions[start_index:end_index].strip()
                question = questions[end_index:].strip()
                top_paras = top_similarity(question, content, top_k=3)
                retrieved_content = "\n\n".join([para for para, score in top_paras])
                user_prompt = USER_RAG_PROMPT.format(
                    content=retrieved_content, question=question, choices=choices
                )
                try:
                    raw_answer = llm.get_single_answer(user_prompt)
                    letter_answer = choice_to_letter(raw_answer, test_case["choices"])
                except Exception as e:
                    print(f"Error processing qid {test_case['qid']}: {e}")
                    letter_answer = ""
            else:
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
    parser.add_argument(
        "--use_sim",
        action="store_true",
        help="Whether to use similarity-based retrieval",
    )

    args = parser.parse_args()

    run_rag_inference(
        args.input,
        args.output,
        args.llm,
        start=args.start,
        end=args.end,
        use_sim=args.use_sim,
    )
