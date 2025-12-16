import json
import re
from typing import Literal

from core.llm_interface import LLM_VNPTAI
from core.answer_extracter import LLM_AnswerExtractor
from prompt.agent_prompt import STEM_PROMPT
from utils.post_processing import choice_to_letter

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

    def get_single_answer_letter(self, user_prompt: str) -> str:
        result = self.get_single_answer(user_prompt)

        input_data = json.loads(user_prompt)
        choices = input_data["choices"]

        final_answer_text = result["PHASE_3"]["final_answer"]
        return choice_to_letter(final_answer_text, choices=choices)

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
        system_prompt=STEM_PROMPT,
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

    user_prompt = json.dumps(
        {
            "question": test["question"],
            "choices": test["choices"]
        },
        ensure_ascii=False
    )
    
    print("User prompt:", json.dumps(user_prompt, ensure_ascii=False, indent=2))
    
    result = stem_llm.get_single_answer(user_prompt)
    result = json.dumps(result, ensure_ascii=False, indent=2)
    print(result)
