import csv
import difflib
import json
import unicodedata
from core.answer_extracter import LLM_AnswerExtractor
import re

def normalize_text(s: str) -> str:
    """Lowercase, remove accents/diacritics, normalize whitespace."""
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = " ".join(s.casefold().split())
    return s

def clean_answer(answer: str) -> str:
    """Loại bỏ các thẻ, ký tự dư thừa, xuống dòng, chỉ giữ phần thực tế"""
    if answer is None:
        return ""
    # loại bỏ các tag dạng <...>
    answer = re.sub(r"<[^>]+>", " ", answer)
    # loại bỏ ký tự đặc biệt dư thừa
    answer = re.sub(r"[\n\r\t]", " ", answer)
    # loại bỏ khoảng trắng thừa
    answer = " ".join(answer.split())
    return answer.strip()

def choice_to_letter(
    pred_text: str, choices: list[str], fuzzy_threshold: float = 0.65
) -> str:
    if pred_text is None:
        return ""
    pred = str(pred_text).strip()
    # if already a single letter like "A" or "b", handle quickly
    if len(pred) == 1 and pred.isalpha():
        return pred.upper()
    print(f"Raw model prediction: {pred}")
    norm_pred = normalize_text(pred)
    norm_choices = [normalize_text(c) for c in choices]

    # exact normalized match
    if norm_pred in norm_choices:
        idx = norm_choices.index(norm_pred)
        return chr(ord("A") + idx)

    # fuzzy match
    best_idx = None
    best_ratio = 0.0
    for i, c in enumerate(norm_choices):
        ratio = difflib.SequenceMatcher(None, norm_pred, c).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i
    if best_idx is not None and best_ratio >= fuzzy_threshold:
        return chr(ord("A") + best_idx)

    # substring fallback
    for i, c in enumerate(norm_choices):
        if norm_pred in c or c in norm_pred:
            return chr(ord("A") + i)

    return ""

def model_output2letter(answer_text: str, choices: list[str], fuzzy_threshold: float = 0.65) -> str:
    """
    Convert model output (answer text) to choice letter (A/B/C/...) 
    using internal mapping first; if fails, fallback to LLM.
    """
    try:
        cleaned_answer = clean_answer(answer_text)
        letter = choice_to_letter(cleaned_answer, choices, fuzzy_threshold=0.65)
        if letter:
            return letter
        else:
            raise ValueError("No match found")
    except Exception:
        answer_extractor_llm = LLM_AnswerExtractor()
        llm_input = json.dumps({
            "choices": choices,
            "answer": answer_text
        }, ensure_ascii=False)
        print("LLM answer extracter triggered")
        llm_output = answer_extractor_llm.get_single_answer(llm_input)
        
        try:
            parsed = json.loads(llm_output)
            letter = parsed.get("answer_label", "")
            return letter
        except Exception:
            return ""
        
        
if __name__ == "__main__":
    test = {
    "qid": "test_0101",
    "question": "Điểm khác biệt căn bản của hệ thống chính trị Việt Nam so với hệ thống chính trị được tổ chức theo cơ chế tam quyền phân lập là:",
    "choices": [
      "Tính độc lập của các cơ quan trong hệ thống chính trị Việt Nam khi thực hiện các chức năng lập pháp, hành pháp và tư pháp.",
      "Tính phụ thuộc của các cơ quan trong hệ thống chính trị Việt Nam khi thực hiện các chức năng lập pháp, hành pháp và tư pháp.",
      "Tính kế thừa của các cơ quan trong hệ thống chính trị Việt Nam khi thực hiện các chức năng lập pháp, hành pháp và tư pháp.",
      "Tính loại bỏ của các cơ quan trong hệ thống chính trị Việt Nam khi thực hiện các chức năng lập pháp, hành pháp và tư pháp."
    ],
    "label": "Multi-Domain",
    "answer": "Tính phụ thuộc của các cơ quan trong hệ thống chính trị Việt Nam khi thực hiện các chức năng lập pháp, hành pháp và tư pháp. \nLý do: Hệ thống chính trị Việt Nam được tổ chức theo nguyên tắc tập trung dân chủ, trong đó các cơ quan lập pháp,"
    }
    
    result = model_output2letter(test['answer'], test['choices'])
    print(result)