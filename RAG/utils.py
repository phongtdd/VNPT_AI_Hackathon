import json
import re
import time

from pydantic import BaseModel

from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import RAG_GATE_USER_PROMPT


class DecisionResponse(BaseModel):
    need_rag: bool
    confidence: float
    domain: str
    reason: str


def _safe_parse_json(text: str) -> dict:
    """
    Try to safely extract a JSON object from LLM output.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("Unparseable JSON")


def need_rag(llm: LLM_VNPTAI, question: str, max_retries: int = 1):
    """
    Decide whether RAG is needed.
    NEVER crashes the pipeline.
    """

    for attempt in range(max_retries + 1):
        response = llm.get_single_answer(
            user_prompt=RAG_GATE_USER_PROMPT.format(question=question),
        )

        try:
            decision = DecisionResponse.model_validate(_safe_parse_json(response))

            return decision.need_rag, decision.domain

        except Exception as e:
            if attempt < max_retries:
                time.sleep(3)
                continue

            # ---- Final fallback (SAFE DEFAULT) ----
            return False, "other"
