from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import AE_PROMPT


class LLM_AnswerExtractor(LLM_VNPTAI):
    def __init__(
        self,
        llm_name="LLM small",
        system_prompt=AE_PROMPT,
        temperature=0.1,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=64,
        response_format={"type": "json_object"},
    ):
        super().__init__(
            llm_name=llm_name,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            n=n,
            max_completion_tokens=max_completion_tokens,
            response_format=response_format,
        )

    def get_single_answer(self, input: str) -> str:
        output = super().get_single_answer(input)
        return self.post_process(output)

    def post_process(self, output: str):
        return output.strip()


if __name__ == "__main__":
    llm_name = "LLM small"

    answer_extractor_llm = LLM_AnswerExtractor()

    input = """
    {
  "choices": [
    "2-3-1946",
    "1945",
    "1946",
    "1954"
  ],
  "answer": "Không có thông tin về Quốc hội khóa I nước Việt Nam Dân chủ Cộng hòa trong các đoạn văn trên. Tuy nhiên, dựa trên kiến thức lịch sử, Quốc hội khóa I nước Việt Nam Dân chủ Cộng hòa được thành lập vào ngày 2 tháng 3 năm 1946."
}
    """

    result = answer_extractor_llm.get_single_answer(input)

    print(type(result))
    print(result)
