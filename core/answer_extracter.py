from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import AE_PROMPT

class LLM_AnswerExtractor(LLM_VNPTAI):
    def __init__(
        self,
        llm_name = "LLM small",
        system_prompt=AE_PROMPT,
        temperature=0.1,
        top_p=1.0,
        top_k=0,
        n=1,
        max_completion_tokens=64,
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
        
    def get_single_answer(self, input: str) -> str:
        output = super().get_single_answer(input)
        return self.post_process(output)
    
    def post_process(self, output: str):
        return output.strip()
    
    
if __name__ == "__main__":
    llm_name = "LLM small"

    answer_extractor_llm = LLM_AnswerExtractor()

    input = """
    PHASE 1 — EXTERNAL REASONING

### Câu hỏi: Tính Chỉ số Herfindahl-Hirschman (HHI) và mô tả mức độ tập trung thị trường.

#### Dữ kiện:

- Thị phần của Doanh nghiệp A: 50%
- Thị phần của Doanh nghiệp B: 25%
- Thị phần của Doanh nghiệp C: 15%
- Thị phần của Doanh nghiệp D: 7%
- Thị phần của Doanh nghiệp E: 3%

#### Yêu cầu:

1. Tính Chỉ số Herfindahl-Hirschman (HHI).
2. Mô tả mức độ tập trung thị trường dựa trên HHI.

#### Công thức:

Chỉ số Herfindahl-Hirschman (HHI) được tính bằng cách lấy tổng bình phương thị phần của tất cả các doanh nghiệp trong thị trường, với thị phần được biểu thị dưới dạng thập phân.

\[ \text{HHI} = (\text{Thị phần A})^2 + (\text{Thị phần B})^2 + (\text{Thị phần C})^2 + (\text{Thị phần D})^2 + (\text{Thị phần E})^2 \]       

#### Tính toán:

- Thị phần A: \(0.50\)
- Thị phần B: \(0.25\)
- Thị phần C: \(0.15\)
- Thị phần D: \(0.07\)
- Thị phần E: \(0.03\)

\[ \text{HHI} = (0.50)^2 + (0.25)^2 + (0.15)^2 + (0.07)^2 + (0.03)^2 \]
\[ \text{HHI} = 0.25 + 0.0625 + 0.0225 + 0.0049 + 0.0009 \]
\[ \text{HHI} = 0.3408 \]

#### Mô tả mức độ tập trung thị trường:

- HHI < 1000: Thị trường cạnh tranh hoàn hảo.
- 1000 ≤ HHI < 1800: Thị trường cạnh tranh độc quyền.
- 1800 ≤ HHI < 2500: Thị trường độc quyền nhóm với mức độ tập trung thấp.
- 2500 ≤ HHI < 3500: Thị trường độc quyền nhóm với mức độ tập trung trung bình.
- HHI ≥ 3500: Thị trường độc quyền nhóm với mức độ tập trung cao.

Vì HHI = 3408, nên thị trường này thuộc loại độc quyền nhóm với mức độ tập trung cao.

#### So sánh với lựa chọn:

- choice[0]: Thị trường là cạnh tranh hoàn hảo. (Sai)
- choice[1]: Thị trường là cạnh tranh độc quyền. (Sai)
- choice[2]: Thị trường là độc quyền nhóm với mức độ tập trung thấp. (Sai)
- choice[3]: Thị trường là độc quyền nhóm với mức độ tập trung trung bình. (Sai)
- choice[4]: Thị trường là độc quyền nhóm với mức độ tập trung cao. (Đúng)
- choice[5]: Thị trường là độc quyền thuần túy. (Sai)
- choice[6]: Không thể xác định mức độ tập trung thị trường với thông tin đã cho. (Sai)
- choice[7]: Thị trường là đôi cạnh tranh. (Sai)
- choice[8]: Mức độ tập trung thị trường là thấp. (Sai)
- choice[9]: Mức độ tập trung thị trường là rất cao. (Đúng, nhưng không cụ thể như choice[4])

#### Kết quả:

- qid: q1
- answer: D (choice[4])
    """

    result = answer_extractor_llm.get_single_answer(input)

    print(type(result))
    print(result)
