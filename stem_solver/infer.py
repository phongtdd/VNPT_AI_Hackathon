import json
import re
from typing import Literal
import pandas as pd
import os

from stem_solver.stem import LLMStem
from prompt.agent_prompt import STEM_CLASSIFY_PROMPT, STEM_PROMPT_QUESTION_DRIVEN, STEM_PROMPT_ANSWER_VALIDATION, STEM_SECOND_THINK

def initialize_llm(llm_name = "LLM large"):
    stem_classify_llm = LLMStem(
        llm_name='LLM small',
        system_prompt=STEM_CLASSIFY_PROMPT,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=128,
        response_format= {"type": "json_object"}
    )
        
    stem_question_driven_llm = LLMStem(
        llm_name=llm_name,
        system_prompt=STEM_PROMPT_QUESTION_DRIVEN,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=2048,
        response_format= {"type": "json_object"}
    )

    stem_answer_driven_llm = LLMStem(
        llm_name=llm_name,
        system_prompt=STEM_PROMPT_ANSWER_VALIDATION,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=2048,
        response_format= {"type": "json_object"}
    )
    
    stem_2nd = LLMStem(
        llm_name=llm_name,
        system_prompt=STEM_SECOND_THINK,
        temperature=0.1,
        top_p=0.9,
        top_k=0,
        n=1,
        max_completion_tokens=4096,
        response_format= {"type": "json_object"}
    )
    
    return stem_classify_llm, stem_question_driven_llm, stem_answer_driven_llm, stem_2nd
    

def solve_stem_question(
    question,
    choices,
    llm_name="LLM large",
    mode: Literal["strict", "allow_no_answer"] = "strict",
    max_retries = 1,
    ) -> str:

    stem_classify_llm, stem_question_driven_llm, stem_answer_driven_llm, stem_2nd = initialize_llm(llm_name=llm_name)
    user_prompt = json.dumps(
        {
            "question": question,
            "choices": choices
        },
        ensure_ascii=False
    )
    
    num_retry = 0
    while num_retry < max_retries:
        try:
            stem_class = stem_classify_llm.get_single_answer(user_prompt)
            analysis_mode = stem_class.get("analysis_mode")
            # print(analysis_mode)
            if analysis_mode == "ANSWER_VALIDATION":
                result = stem_answer_driven_llm.get_single_answer(user_prompt)
                # print(result)
                if isinstance(result, str):
                    result = json.loads(result)

                prediction = result["PHASE_4"]["final_answer"]

                return prediction
                
            elif analysis_mode == "QUESTION_DRIVEN":
                result = stem_question_driven_llm.get_single_answer(user_prompt)

                if isinstance(result, str):
                    result = json.loads(result)

                prediction = result["PHASE_4"]["final_answer"]
                
                if prediction != "X":
                    return prediction
                
                if mode == "allow_no_answer":
                    return "X"
                
                if mode == "strict":
                    # fallback
                    previous_solution = result["PHASE_2"]["solution_steps"]

                    second_input = json.dumps(
                        {
                            "question": question,
                            "choices": choices,
                            "previous_solution": previous_solution,
                        },
                        ensure_ascii=False,
                    )
                    
                    result_2nd = stem_2nd.get_single_answer(second_input)
                    if isinstance(result_2nd, str):
                        result_2nd = json.loads(result_2nd)
                        
                    prediction_2nd = result_2nd["PHASE_4"]["final_answer"]
                    return prediction_2nd
                
                raise ValueError(f"Invalid mode: {mode}")

            else:
                raise ValueError(f"Unknown analysis_mode: {analysis_mode}")
        
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            num_retry += 1
            print(f"[RETRY {num_retry}/{max_retries}] {e}")

    print("Exceed max retries")
    return "X"

def run_stem_infer(
    input_path: str,
    output_path: str,
    mode: Literal["strict", "allow_no_answer"] = "strict"
):
    """
    * input_path: path tới file json chứa câu hỏi
    * output_path: path csv lưu kết quả
    * mode:
        - 'strict': bắt buộc chọn 1 đáp án
        - 'allow_no_answer': cho phép trả 'X'
    """

    data = pd.read_json(input_path)
    stem_data = data[data["label"] == "STEM"].reset_index(drop=True)
    print(f"Total STEM questions: {len(stem_data)}")

    # init CSV nếu chưa tồn tại
    if not os.path.exists(output_path):
        pd.DataFrame(columns=["qid", "answer"]).to_csv(
            output_path,
            index=False,
            encoding="utf-8"
        )

    def save_prediction_csv(qid: str, answer: str, output_path: str):
        pd.DataFrame([{
            "qid": qid,
            "answer": answer
        }]).to_csv(
            output_path,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8"
        )
        print(f"[SAVED] {qid} → {answer}")

    for i in range(len(stem_data)):
        test = stem_data.iloc[i]
        current_qid = test["qid"]

        print("\n==============================")
        print("QID:", current_qid)

        try:
            prediction = solve_stem_question(
                question=test["question"],
                choices=test["choices"],
                mode=mode
            )

            save_prediction_csv(current_qid, prediction, output_path)

        except Exception as e:
            print(f"[FAILED] QID {current_qid}: {e}")
            # fallback
            save_prediction_csv(current_qid, "X", output_path)
