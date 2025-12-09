import json
from core.llm_interface import LLM_VNPTAI, get_api_key, get_endpoint

KR_PROMPT = """
Bạn là module LLM Knowledge Retriever cho hệ thống giải STEM.

Nhiệm vụ:
1. Phân tích câu hỏi.
2. Quyết định xem có cần sinh Knowledge không.
3. Nếu cần, hãy tạo:
   - Bối cảnh toán học / vật lý / dữ kiện nền
   - Định nghĩa quan trọng
   - Công thức hoặc định lý liên quan
   - Các bước giải KHÁI QUÁT (step-by-step outline), nhưng KHÔNG giải bài.
4. Nếu không cần → trả về knowledge = "".

Yêu cầu quan trọng:
- Tuyệt đối không giải đề.
- Chỉ cung cấp kiến thức giúp Python generator hoặc solver dùng được.
- Ngắn gọn, đúng bản chất, tối đa 10 dòng.
- Bước gợi ý phải là bước giải tổng quát, không thay số.
- Output CHỈ JSON:

{
  "need_knowledge": true/false,
  "knowledge": "..."
}

"""

class LLMKnowledgeRetriever(LLM_VNPTAI):
    def __init__(
        self,
        model_cfg=None,
        endpoint=None,
        system_prompt="",
        temperature=0.1,
        max_completion_tokens=1000
    ):
        super().__init__(
            model_cfg=model_cfg,
            endpoint=endpoint,
            system_prompt=system_prompt,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
        )

    def retrieve(self, question: str) -> dict:
        """
        Output:
        {
            "need_knowledge": bool,
            "knowledge": str
        }
        """
        
        output = self.get_single_answer(question)

        if not output:
            return {"need_knowledge": False, "knowledge": ""}

        text = output.strip()

        # Check JSON Validity
        try:
            data = json.loads(text)
        except:
            raise ValueError(f"Cannot parse JSON from output:\n{text}")
            # return {"need_knowledge": False, "knowledge": ""}

        need = data.get("need_knowledge", False)
        knowledge = data.get("knowledge", "") or ""

        return {
            "need_knowledge": bool(need),
            "knowledge": knowledge.strip()
        }

if __name__ == "__main__":
    llm_name = "LLM small"
    cfg = get_api_key(llm_name=llm_name)
    endpoint = get_endpoint(llm_name)
    
    kr_llm = LLMKnowledgeRetriever(
        model_cfg=cfg,
        endpoint=endpoint,
        system_prompt=KR_PROMPT
    )
    
    question = "Một phân tử của một hợp chất nhất định có mô men lưỡng cực $ \\mu $ và được đặt trong một trường điện đều $ E $. Phân tử có thể định hướng theo trường, và năng lượng thế $ U $ của phân tử trong trường có thể được mô tả bởi phương trình $ U = -\\mu E \\cos(\\theta) $, trong đó $ \\theta $ là góc giữa mô men lưỡng cực và trường điện. Nếu phân tử ban đầu được định hướng ở góc $ 60^\\circ $ so với trường điện, và sau đó định hướng hoàn toàn theo trường (tức là $ \\theta = 0^\\circ $), thì độ biến thiên của năng lượng thế $ \\Delta U $ là bao nhiêu?"
    result = kr_llm.retrieve(question)
    print(result)