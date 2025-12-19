import argparse
import csv
import os
from multiprocessing import Pool
from tqdm import tqdm

from core.label_registry import LABEL_REGISTRY
from core.llm_factory import build_llm
from core.llm_interface import LLM_VNPTAI
from core.question_classify import seperate_data
from MD_LLM.multi_domain import solve_multi_domain
from prompt.agent_prompt import (
    RAG_DECISION_SYSTEM_PROMPT,
)
from RAG.utils import DecisionResponse
from utils.helper import load_separated_data, load_single_file
from utils.post_processing import model_output2letter
from stem_solver.infer import solve_stem_question


# -------- GLOBAL CACHE ---------------------------------------
_worker_cache = {}


# -------- WORKER INITIALIZER ---------------------------------
def init_worker(label, label_config, llm_name):
    """
    Runs once per worker process.
    Loads model(s) into local worker memory.
    """

    global _worker_cache
    _worker_cache["label"] = label
    _worker_cache["label_config"] = label_config

    # multi-domain
    if label_config.get("tool_use") == "multi_domain":
        _worker_cache["gate_llm"] = LLM_VNPTAI(
            llm_name="LLM small",
            system_prompt=RAG_DECISION_SYSTEM_PROMPT,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "DecisionResponse",
                    "schema": DecisionResponse.model_json_schema(),
                },
            },
        )
        _worker_cache["answer_llm"] = LLM_VNPTAI(
            llm_name="LLM large",
            max_completion_tokens=256
        )
        _worker_cache["llm"] = None

    # normal single domain
    else:
        _worker_cache["llm"] = build_llm(label_config, llm_name)
        _worker_cache["gate_llm"] = None
        _worker_cache["answer_llm"] = None



# -------- WORKER EXECUTION -----------------------------------
def process_case(test_case):

    global _worker_cache

    label_config = _worker_cache["label_config"]
    llm = _worker_cache["llm"]
    gate_llm = _worker_cache["gate_llm"]
    answer_llm = _worker_cache["answer_llm"]

    qid = test_case["qid"]

    try:
        # ---- Multi-domain ----
        if label_config.get("tool_use") == "multi_domain":
            answer = solve_multi_domain(
                test_case=test_case,
                gate_llm=gate_llm,
                answer_llm=answer_llm,
            )

        # ---- STEM ----
        elif label_config["llm_type"] == "stem":
            question = test_case["question"]
            choices = test_case["choices"]
            answer = solve_stem_question(question, choices)

        # ---- Default ----
        else:
            raw = llm.predict(
                test_case,
                question_type=label_config.get("question_type"),
            )
            try:
                answer = model_output2letter(raw, test_case["choices"])
            except:
                answer = ""

    except Exception as e:
        print(f"Error qid {qid}: {e}")
        answer = ""

    return qid, answer



# -------- MAIN LOGIC -----------------------------------------
def run_inference(
    separated_dir: str,
    output_path: str,
    llm_name: str,
    workers: int = 4,
):

    # -------- read dataset ----------
    if os.path.isfile(separated_dir):
        datasets = load_single_file(separated_dir)
    elif os.path.isdir(separated_dir):
        datasets = load_separated_data(separated_dir)
    else:
        raise FileNotFoundError(f"Path not found: {separated_dir}")


    # -------- write csv ----------
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["qid", "answer"])


        # -------- per label parallel run ----------
        for label, test_data in datasets:

            label_config = LABEL_REGISTRY[label]

            # Create multiprocessing pool
            with Pool(
                processes=workers,
                initializer=init_worker,
                initargs=(label, label_config, llm_name)
            ) as pool:

                results = list(
                    tqdm(
                        pool.imap(process_case, test_data),
                        total=len(test_data),
                        desc=f"[{label}]"
                    )
                )

            # Save results from this label
            for qid, answer in results:
                writer.writerow([qid, answer])
                f.flush()



# -------- ENTRY POINT ----------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to raw test dataset JSON")
    parser.add_argument(
        "--separated_dir", required=True, help="Path to save separated data"
    )
    parser.add_argument("--output", required=True, help="Path to save predictions")
    parser.add_argument("--llm", default="LLM large", help="LLM model name")
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker processes",
    )

    args = parser.parse_args()

    if args.input:
        seperate_data(args.input, output_dir=args.separated_dir)

    run_inference(
        separated_dir=args.separated_dir,
        output_path=args.output,
        llm_name=args.llm,
        workers=args.workers,
    )
