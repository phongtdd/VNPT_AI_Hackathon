import json
import re
from typing import Literal

from core.llm_interface import LLM_VNPTAI
from core.answer_extracter import LLM_AnswerExtractor
from prompt.agent_prompt import STEM_PROMPT, STEM_PROMPT_QUESTION_DRIVEN, STEM_PROMPT_ANSWER_VALIDATION, STEM_SECOND_THINK
from utils.post_processing import model_output2letter

class LLMStem(LLM_VNPTAI):
    def __init__(
        self,
        llm_name: Literal["LLM large", "LLM small"],
        system_prompt="",
        temperature=0.1,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=2048,
        response_format= {"type": "json_object"}
    ):
        super().__init__(
            llm_name=llm_name,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            n=n,
            max_completion_tokens=max_completion_tokens,
            response_format=response_format
        )

    def get_single_answer(self, user_prompt: str) -> dict:
        output = super().get_single_answer(user_prompt)
        return self.post_process(output)

    def post_process(self, raw_output: str) -> dict:
        text = raw_output.strip()

        # Remove markdown fences if any
        if text.startswith("```"):
            text = re.sub(r"^```(json)?", "", text)
            text = re.sub(r"```$", "", text)
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                "LLM output không phải JSON hợp lệ:\n" + text
            ) from e

if __name__ == "__main__":
    llm_name = "LLM small"

    stem_llm = LLMStem(
        llm_name=llm_name,
        system_prompt=STEM_PROMPT_ANSWER_VALIDATION,
        temperature=0.0,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=2048,
        response_format= {"type": "json_object"}
    )

    test =         {
        "qid": "test_0248",
        "question": "Công ty Kennie bán một máy in với giá 31.000 đô la sau ba năm sở hữu. Máy in có chi phí ban đầu là 58.000 đô la và cơ sở khấu hao là 48.000 đô la. Giá trị sổ sách của máy in vào thời điểm bán là bao nhiêu, và lợi nhuận từ việc bán là bao nhiêu?",
        "choices": [
            "Giá trị sổ sách: 20.000 đô la; Lợi nhuận: 11.000 đô la",
            "Giá trị sổ sách: 29.200 đô la; Lợi nhuận: 1.800 đô la",
            "Giá trị sổ sách: 29.200 đô la; Lợi nhuận: 11.000 đô la",
            "Giá trị sổ sách: 20.000 đô la; Lợi nhuận: 1.800 đô la"
        ],
        "label": "STEM"
    }

    test =     {
        "qid": "test_0277",
        "question": "Một hành tinh hình cầu có mật độ đều và bán kính $ R $. Nếu gia tốc trọng trường tại bề mặt của hành tinh là $ g $, thì gia tốc trọng trường tại khoảng cách $ \\frac{R}{2} $ từ tâm hành tinh là bao nhiêu?",
        "choices": [
            "$ \\frac{g}{4} $",
            "$ \\frac{g}{2} $",
            "$ \\frac{g}{\\sqrt{2}} $",
            "$ \\frac{g}{3} $",
            "$ \\frac{g}{\\sqrt{3}} $",
            "$ \\frac{g}{8} $",
            "$ \\frac{g}{9} $",
            "$ \\frac{g}{16} $",
            "$ \\frac{g}{27} $",
            "$ \\frac{g}{64} $"
        ],
        "label": "STEM"
    }
    
    user_prompt = json.dumps(
        {
            "question": test["question"],
            "choices": test["choices"]
        },
        ensure_ascii=False
    )

    result = stem_llm.get_single_answer(user_prompt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    answer = result["PHASE_4"]["final_answer"]
    print(answer)
    
    # answer = "X"
    if answer == "X":
        stem_2nd = LLMStem(
            llm_name=llm_name,
            system_prompt=STEM_PROMPT_ANSWER_VALIDATION,
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
        