import json
import re
from typing import Literal
import pandas as pd
import os

from stem_solver.stem import LLMStem
from prompt.agent_prompt import STEM_CLASSIFY_PROMPT, STEM_PROMPT_QUESTION_DRIVEN, STEM_PROMPT_ANSWER_VALIDATION, STEM_SECOND_THINK

def run_stem_infer(
    test_data_path: str,
    output_path: str,
    mode: Literal["strict", "allow_no_answer"] = "strict"
    ):
    """
    mode:
    - 'strict': bắt buộc chọn 1 đáp án trong choices
    - 'allow_no_answer': cho phép kết luận không có đáp án đúng
    """
    
    llm_name = "LLM large"

    classify_llm = LLMStem(
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
    
    data=pd.read_json(test_data_path)
    stem_data = data[data['label']=='STEM'].reset_index(drop=True)
    print(len(stem_data))
    
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        existing_qids = set(existing_df['qid'])
        print(f"Loaded {len(existing_qids)} existing QIDs.")
    else:
        existing_df = pd.DataFrame(columns=['qid', 'answer'])
        existing_qids = set()
        print("CSV not found, will create new file.")
        
    
    def save_prediction_csv(qid: str, answer: str, output_path):
        global existing_df, existing_qids

        if qid in existing_qids:
            print(f"[SKIP] {qid} already exists.")
            return

        new_row = pd.DataFrame([{
            'qid': qid,
            'answer': answer
        }])

        existing_df = pd.concat(
            [existing_df, new_row],
            ignore_index=True
        )

        existing_df.drop_duplicates(
            subset=['qid'],
            keep="last",
            inplace=True
        )

        existing_df.to_csv(
            output_path,
            index=False,
            encoding="utf-8"
        )

        existing_qids.add(qid)
        print(f"[SAVED] {qid}")
        
    for i in range(len(stem_data)):
        test = stem_data.iloc[i]
        current_qid = test['qid']

        if current_qid in existing_qids:
            print(f"QID {current_qid} already processed, skip.")
            continue

        user_prompt = json.dumps(
            {
                "question": test["question"],
                "choices": test["choices"]
            },
            ensure_ascii=False
        )

        print("QID:", current_qid)

        while True:
            stem_class = classify_llm.get_single_answer(user_prompt)
            
            if stem_class['analysis_mode'] == "ANSWER_VALIDATION":
                try:
                    result = stem_answer_driven_llm.get_single_answer(user_prompt)

                    if isinstance(result, str):
                        result = json.loads(result)

                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    prediction = result["PHASE_3"]["final_answer"]

                    save_prediction_csv(current_qid, prediction)
                    break

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"Retry QID {current_qid} due to error:", e)
                    continue
                
            if stem_class['analysis_mode'] == "QUESTION_DRIVEN":
                try:
                    result = stem_question_driven_llm.get_single_answer(user_prompt)

                    if isinstance(result, str):
                        result = json.loads(result)

                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    prediction = result["PHASE_4"]["final_answer"]
                    if prediction == "X":
                        if mode == "strict":
                            # fallback
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

                            second_input = json.dumps(
                                {
                                    "question": test["question"],
                                    "choices": test["choices"],
                                }
                            )
                            
                            result_2nd = stem_2nd.get_single_answer(second_input)
                            print(json.dumps(result_2nd, ensure_ascii=False, indent=2))
                        else:
                            # allow_no_answer
                            save_prediction_csv(current_qid, prediction)
                            break

                    save_prediction_csv(current_qid, prediction)
                    break

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"Retry QID {current_qid} due to error:", e)
                    continue
