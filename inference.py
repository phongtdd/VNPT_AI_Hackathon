import argparse
import csv
import time
from ast import arg

from tqdm import tqdm

from core.label_registry import LABEL_REGISTRY
from core.llm_factory import build_llm
from core.llm_interface import LLM_VNPTAI
from core.question_classify import seperate_data
from utils.helper import load_separated_data
from utils.post_processing import choice_to_letter


def infer(test_case: dict[str, str], llm: LLM_VNPTAI, label_config: dict[str, str]):
    if label_config["llm_type"] == "stem":
        prompt = f"Câu hỏi:\n{test_case['question']}\n\nLựa chọn:\n{test_case['choices']}\n\n"
        raw = llm.get_single_answer(prompt)
        return raw[0]["answer"]

    raw = llm.predict(
        test_case,
        question_type=label_config.get("question_type"),
    )

    if label_config["postprocess"] == "choice_to_letter":
        return choice_to_letter(raw, test_case["choices"])

    return raw


def run_inference(
    separated_dir: str,
    output_path: str,
    llm_name: str,
    batch_size: int = 40,
    sleep_seconds: int = 3600,
):
    llm_cache = {}

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["qid", "answer"])

        for label, test_data in load_separated_data(separated_dir):
            print(f"Running inference for label: {label}")

            label_config = LABEL_REGISTRY[label]

            if label not in llm_cache:
                llm_cache[label] = build_llm(label_config, llm_name)

            llm = llm_cache[label]

            for i, test_case in tqdm(
                enumerate(test_data),
                total=len(test_data),
                desc=f"{label}",
            ):
                try:
                    answer = infer(test_case, llm, label_config)
                except Exception as e:
                    print(f"Error qid {test_case['qid']}: {e}")
                    answer = ""

                writer.writerow([test_case["qid"], answer])
                f.flush()

                if (i + 1) % batch_size == 0:
                    time.sleep(sleep_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to test dataset JSON")
    parser.add_argument(
        "--separated_dir", required=True, help="Path to save separated data"
    )
    parser.add_argument("--output", required=True, help="Path to save predictions")
    parser.add_argument("--llm", default="LLM large", help="LLM model name")
    parser.add_argument(
        "--batch_size",
        type=int,
        default=40,
        help="Number of samples to process before sleeping",
    )

    args = parser.parse_args()

    seperate_data(args.input, output_dir=args.separated_dir)

    run_inference(
        separated_dir=args.separated_dir,
        output_path=args.output,
        llm_name=args.llm,
        batch_size=args.batch_size,
        sleep_seconds=3600,
    )
