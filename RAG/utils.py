import json

from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import RAG_GATE_USER_PROMPT


def need_rag(llm: LLM_VNPTAI, question: str) -> bool:
    response = llm.get_single_answer(
        user_prompt=RAG_GATE_USER_PROMPT.format(question=question),
    )

    decision = json.loads(response)
    return decision["need_rag"]
