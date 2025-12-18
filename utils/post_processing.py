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
# Date extractor
# ---------------------------------------------------------
def extract_date(text: str):
    """
    Extract standardized date format: D-M-YYYY
    """
    if not text:
        return None

    t = normalize_text(text)

    # 1) Format: dd-mm-yyyy / d-m-yyyy
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", t)
    if m:
        d, mth, year = m.groups()
        return f"{int(d)}-{int(mth)}-{year}"

    # 2) Format: "ngày d tháng m năm yyyy"
    m = re.search(
        r"ng(à|a)y\s+(\d{1,2})\s+th(á|a)ng\s+(\d{1,2})\s+n(ă|a)m\s+(\d{4})",
        t,
    )
    if m:
        d = m.group(2)
        mth = m.group(4)
        year = m.group(6)
        return f"{int(d)}-{int(mth)}-{year}"

    return None


# ---------------------------------------------------------
# Year extractor
# ---------------------------------------------------------
def extract_year(text: str):
    """Return yyyy if appears in text."""
    if not text:
        return None
    m = re.search(r"\b(19|20)\d{2}\b", text)
    return m.group(0) if m else None


# ---------------------------------------------------------
# Main mapping logic
# ---------------------------------------------------------
def choice_to_letter(
    answer_text: str, choices: list[str], fuzzy_threshold: float = 0.65
) -> str:
    if answer_text is None:
        return ""

    answer_norm = normalize_text(answer_text)

    # 1) DATE MATCH
    extracted_date = extract_date(answer_norm)
    if extracted_date:
        for i, c in enumerate(choices):
            c_norm = normalize_text(c).replace("/", "-")
            if c_norm == extracted_date:
                return chr(ord("A") + i)

    # 2) YEAR MATCH
    extracted_year = extract_year(answer_norm)
    if extracted_year:
        for i, c in enumerate(choices):
            if normalize_text(c) == extracted_year:
                return chr(ord("A") + i)

    # 3) DIRECT MATCH (accent preserved)
    pred_core = clean_answer(answer_text)
    norm_pred_keep = normalize_text_keep(pred_core)
    norm_choices_keep = [normalize_text_keep(c) for c in choices]

    if norm_pred_keep in norm_choices_keep:
        idx = norm_choices_keep.index(norm_pred_keep)
        return chr(ord("A") + idx)

    # # 4) FUZZY MATCH
    # best_score = -1
    # best_index = None

    # for i, c in enumerate(choices):
    #     c_norm = normalize_text(c)
    #     score = fuzz.partial_ratio(answer_norm, c_norm)

    #     # Boost date-like answers
    #     if re.search(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}", c_norm):
    #         score *= 1.4

    #     if score > best_score:
    #         best_score = score
    #         best_index = i

    # if best_score >= fuzzy_threshold * 100:
    #     return chr(ord("A") + best_index)

    return ""


# -------------------------------
# LLM fallback wrapper
# -------------------------------
def model_output2letter(
    answer_text: str, choices: list[str], fuzzy_threshold: float = 0.65
) -> str:
    try:
        cleaned_answer = clean_answer(answer_text)

        letter = choice_to_letter(
            cleaned_answer, choices, fuzzy_threshold=fuzzy_threshold
        )

        if letter:
            return letter
        else:
            raise ValueError("No match found")

    except Exception:
        answer_extractor_llm = LLM_AnswerExtractor()
        llm_input = json.dumps(
            {"choices": choices, "answer": answer_text}, ensure_ascii=False
        )
        print("LLM answer extractor triggered")
        llm_output = answer_extractor_llm.get_single_answer(llm_input)

        try:
            parsed = json.loads(llm_output)
            letter = parsed.get("answer_label", "")
            return letter
        except Exception:
            return ""


# -------------------------------
# Example
# -------------------------------
if __name__ == "__main__":
    test = {
        "qid": "test_0032",
        "question": 'Điền từ còn thiếu vào chỗ trống: "Tấc đất, ... vàng"',
        "choices": ["tất", "tắc", "tắt", "tấc"],
        "label": "Multi-Domain",
        "answer": "tấc",
    }

    result = model_output2letter(test["answer"], test["choices"])
    print(result)
