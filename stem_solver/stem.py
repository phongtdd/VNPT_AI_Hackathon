import json
import re
from typing import Literal

from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import STEM_PROMPT


class LLMStem(LLM_VNPTAI):
    def __init__(
        self,
        llm_name: Literal["LLM large", "LLM small", "LLM embedings"],
        system_prompt="",
        temperature=0.1,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=1000,
    ):
        super().__init__(
            llm_name=llm_name,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            n=n,
            max_completion_tokens=max_completion_tokens,
        )

    def get_single_answer(self, question_with_choices: str) -> str:
        output = super().get_single_answer(question_with_choices)
        return self.post_process(output)

    def post_process(self, output: str):
        # Ensure output is in valid JSON format
        s = output.split("PHASE 2 — FINAL OUTPUT")[-1].strip()
        
        original = s
        match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', s)
        if match:
            s = match.group(0)

        s = s.replace("“", "\"").replace("”", "\"").replace("‘", "\"").replace("’", "\"")

        s = re.sub(r',\s*([\]}])', r'\1', s)

        s = re.sub(r'(\{|,)\s*([A-Za-z0-9_]+)\s*:', r'\1 "\2":', s)

        s = re.sub(r'"answer":\s*([A-Za-z])', r'"answer": "\1"', s)

        s = s.replace("}{", "},{")

        try:
            return json.loads(s)
        except Exception as e:
            print("Parse still failed. Input:")
            print(original)
            print("After auto-fix:")
            print(s)
            raise e

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
    )

    question = "Một quả bóng bay hình cầu có bán kính $ R $ đang được bơm phồng. Áp suất bên trong quả bóng tỷ lệ thuận với lực căng bề mặt $ \\sigma $ và tỷ lệ nghịch với bán kính $ R $. Nếu bán kính của quả bóng được nhân đôi, áp suất bên trong quả bóng thay đổi theo nhân tử nào?"
    choices = [
        "$ \\frac{1}{4} $",
        "$ \\frac{1}{2} $",
        "$ 1 $",
        "$ 2 $",
        "$ 4 $",
        "$ 8 $",
        "$ 16 $",
        "$ \\frac{1}{8} $",
        "$ \\frac{1}{16} $",
        "$ 3 $",
    ]

    full_input = f"Câu hỏi:\n{question}\n\nLựa chọn:\n{choices}\n\n"

    result = stem_llm.get_single_answer(full_input)

    print(type(result))
    print(result[0]["answer"])
