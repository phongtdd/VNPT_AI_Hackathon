import csv
import difflib
import json
import unicodedata


def normalize_text(s: str) -> str:
    """Lowercase, remove accents/diacritics, normalize whitespace."""
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = " ".join(s.casefold().split())
    return s


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
