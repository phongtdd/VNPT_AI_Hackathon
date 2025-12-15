import argparse
import csv
import json
import os
import time

from tqdm import tqdm

from core.label_registry import LABEL_REGISTRY
from core.llm_factory import build_llm
from core.llm_interface import LLM_VNPTAI
from core.question_classify import seperate_data
from MD_LLM.multi_domain import solve_multi_domain
from prompt.agent_prompt import (
    GENERAL_SYSTEM_PROMPT,
    RAG_DECISION_SYSTEM_PROMPT,
)
from utils.helper import load_separated_data, load_single_file
from utils.post_processing import choice_to_letter


def infer(test_case, llm, label_config, *, gate_llm=None, answer_llm=None):
    # ---- Multi-Domain ----
    if label_config.get("solver") == "multi_domain":
        return solve_multi_domain(
            test_case=test_case,
            gate_llm=gate_llm,
            answer_llm=answer_llm,
        )

    # ---- STEM ----
    if label_config["llm_type"] == "stem":
        user_prompt = json.dumps(
            {"question": test_case["question"], "choices": test_case["choices"]},
            ensure_ascii=False,
        )
        return llm.get_single_answer_letter(user_prompt)

    # ---- Default ----
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

    # ---- Multi-Domain LLMs (ONCE) ----
    gate_llm = LLM_VNPTAI(
        llm_name="LLM small",
        system_prompt=RAG_DECISION_SYSTEM_PROMPT,
    )

    answer_llm = LLM_VNPTAI(llm_name="LLM large")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["qid", "answer"])

        if os.path.isfile(separated_dir):
            datasets = load_single_file(separated_dir)
        elif os.path.isdir(separated_dir):
            datasets = load_separated_data(separated_dir)
        else:
            raise FileNotFoundError(f"Path not found: {separated_dir}")

        for label, test_data in datasets:
            label_config = LABEL_REGISTRY[label]

            if label_config.get("solver") != "multi_domain":
                if label not in llm_cache:
                    llm_cache[label] = build_llm(label_config, llm_name)
                llm = llm_cache[label]
            else:
                llm = None  # handled separately

            for i, test_case in tqdm(
                enumerate(test_data),
                total=len(test_data),
                desc=label,
            ):
                try:
                    answer = infer(
                        test_case,
                        llm,
                        label_config,
                        gate_llm=gate_llm,
                        answer_llm=answer_llm,
                    )
                except Exception as e:
                    print(f"Error qid {test_case['qid']}: {e}")
                    answer = ""

                writer.writerow([test_case["qid"], answer])
                f.flush()

                if (i + 1) % batch_size == 0:
                    time.sleep(sleep_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to raw test dataset JSON")
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

    if args.input:
        seperate_data(args.input, output_dir=args.separated_dir)

    run_inference(
        separated_dir=args.separated_dir,
        output_path=args.output,
        llm_name=args.llm,
        batch_size=args.batch_size,
        sleep_seconds=3600,
    )
