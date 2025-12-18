import csv
import json
import re

from rapidfuzz import fuzz

from core.answer_extracter import LLM_AnswerExtractor


# ---------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------
def normalize_text(s: str) -> str:
    """Lowercase + trim spaces. DO NOT remove accents."""
    if not isinstance(s, str):
        return ""
    return s.strip().lower()


def normalize_text_keep(s: str) -> str:
    """Preserve accents, normalize casing + whitespace."""
    if s is None:
        return ""
    s = str(s)
    s = " ".join(s.casefold().split())
    return s

def normalize_date_or_month(text: str) -> str:
    if not text:
        return ""

    t = normalize_text(text)

    t = re.sub(
        r"ng(?:à|a)y\s+(\d{1,2})\s+th(?:á|a)ng\s+(\d{1,2})\s+n(?:ă|a)m\s+(\d{4})",
        lambda m: f"{int(m.group(1)):02d}-{int(m.group(2)):02d}-{m.group(3)}",
        t,
    )

    t = re.sub(
        r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b",
        lambda m: f"{int(m.group(1)):02d}-{int(m.group(2)):02d}-{m.group(3)}",
        t,
    )

    t = re.sub(
        r"th(?:á|a)ng\s+(\d{1,2})\s+n(?:ă|a)m\s+(\d{4})",
        lambda m: f"{int(m.group(1)):02d}-{m.group(2)}",
        t,
    )

    t = re.sub(
        r"\b(\d{1,2})[-/](\d{4})\b",
        lambda m: f"{int(m.group(1)):02d}-{m.group(2)}",
        t,
    )

    return t

# ---------------------------------------------------------
# clean_answer
# ---------------------------------------------------------
def clean_answer(answer: str) -> str:
    """Extract core answer text, remove trailing reasoning."""
    if answer is None:
        return ""

    # remove <tags>
    answer = re.sub(r"<[^>]+>", " ", answer)

    # normalize whitespace
    answer = answer.replace("\r", "\n").replace("\t", " ")
    answer = "\n".join(" ".join(line.split()) for line in answer.split("\n"))

    # remove explanation parts
    for sep in ["\n", "lý do", "ly do", "reason"]:
        pos = answer.lower().find(sep)
        if pos > 0:
            answer = answer[:pos].strip()
            break

    return answer.strip()


# ---------------------------------------------------------
# Main mapping logic
# ---------------------------------------------------------
def choice_to_letters(
    answer_text: str, choices: list[str], fuzzy_threshold: float = 0.65
) -> list[str]:
    if not answer_text:
        return []

    matches: list[int] = []

    # Normalize answer
    ans_norm = normalize_date_or_month(answer_text)
    ans_norm_simple = normalize_text(ans_norm)

    pred_core = clean_answer(answer_text)
    norm_pred_keep = normalize_text_keep(pred_core)

    ans_years = re.findall(r"\b(19|20)\d{2}\b", ans_norm_simple)

    for i, c in enumerate(choices):
        choice_norm = normalize_date_or_month(c)
        choice_norm_simple = normalize_text(choice_norm)
        choice_norm_keep = normalize_text_keep(c)

        matched = False

        # 1) DATE / MONTH-YEAR EXACT MATCH
        if choice_norm_simple == ans_norm_simple:
            matched = True

        # 2) YEAR MATCH
        if not matched and ans_years and choice_norm_simple in ans_years:
            matched = True

        # 3) DIRECT MATCH (accent preserved)
        if not matched and choice_norm_keep == norm_pred_keep:
            matched = True

        # 4) FUZZY MATCH
        if not matched:
            score = fuzz.partial_ratio(
                ans_norm_simple, choice_norm_simple
            ) / 100.0
            if score >= fuzzy_threshold:
                matched = True

        if matched:
            matches.append(i)

    return [chr(ord("A") + i) for i in matches]


# -------------------------------
# LLM fallback wrapper
# -------------------------------
def model_output2letter(
    answer_text: str, choices: list[str], fuzzy_threshold: float = 0.65
) -> str:
    cleaned_answer = clean_answer(answer_text)

    letters = choice_to_letters(
        cleaned_answer, choices, fuzzy_threshold=fuzzy_threshold
    )
    
    # Only accept exactly ONE rule-based match
    if len(letters) == 1:
        return letters[0]

    # 0 match OR multiple matches → fallback to model
    answer_extractor_llm = LLM_AnswerExtractor()
    llm_input = json.dumps(
        {"choices": choices, "answer": answer_text}, ensure_ascii=False
    )
    print("LLM answer extractor triggered")
    llm_output = answer_extractor_llm.get_single_answer(llm_input)

    try:
        parsed = json.loads(llm_output)
        return parsed.get("answer_label", "")
    except Exception:
        return ""


# -------------------------------
# Example
# -------------------------------
if __name__ == "__main__":
    test =     {
        "choices": [
            "2-3-1946",
            "1945",
            "1946",
            "1954"
        ],
        "answer": "Không có thông tin về Quốc hội khóa I nước Việt Nam Dân chủ Cộng hòa trong các đoạn văn trên. Tuy nhiên, dựa trên kiến thức lịch sử, Quốc hội khóa I nước Việt Nam Dân chủ Cộng hòa được thành lập vào ngày 2 tháng 3 năm 1946."
    }

    result = model_output2letter(test["answer"], test["choices"])
    print(result)
