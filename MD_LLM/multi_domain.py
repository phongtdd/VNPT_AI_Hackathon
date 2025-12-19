from core.answer_extracter import LLM_AnswerExtractor
from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import (
    GENERAL_USER_PROMPT,
    MULTI_DOMAIN_SYSTEM_PROMPT,
    SYSTEM_RAG_PROMPT,
    USER_RAG_PROMPT,
    GENERAL_SYSTEM_PROMPT
)
from RAG.resources import CORPUS_TEXTS, EMBEDDER, STORES
from RAG.retriever import retrieve_context_single_domain
from RAG.utils import need_rag
from utils.post_processing import model_output2letter

DOMAIN_THRESHOLDS = {
    "law": 0.85,
    "medical": 0.5,
    "ho_chi_minh": 0.6,
    "civic_knowledge": 0.7,
    "political_science": 0.6
}



def solve_multi_domain(
    gate_llm: LLM_VNPTAI,
    answer_llm: LLM_VNPTAI,
    test_case: dict[str, str | list[str]],
):
    question: str = test_case["question"]
    choices: list[str] = test_case["choices"]

    domain_set = [
        "law",
        "medical",
        "ho_chi_minh",
        "civic_knowledge",
        "political_science",
    ]

    # gate returns (use_rag, domain)
    use_rag, domain = need_rag(gate_llm, question)

    if use_rag and domain in domain_set:
        context = retrieve_context_single_domain(
            question=question,
            domain=domain,
            stores=STORES,
            embedder=EMBEDDER,
            corpus_texts=CORPUS_TEXTS,
            top_k=5,
            faiss_k=30,
        )
        if context.strip() != "":
            prompt = USER_RAG_PROMPT.format(
                content=context,
                question=question,
                choices=choices,
            )

            system_prompt = SYSTEM_RAG_PROMPT
        else:
            prompt = GENERAL_USER_PROMPT.format(
                question=question,
                choices=choices,
            )
            system_prompt = GENERAL_SYSTEM_PROMPT

    else:
        prompt = GENERAL_USER_PROMPT.format(
            question=question,
            choices=choices,
        )
        system_prompt = GENERAL_SYSTEM_PROMPT

    raw = answer_llm.get_single_answer(
        user_prompt=prompt,
        system_prompt=system_prompt,
    )

    try:
        answer = model_output2letter(raw, choices)
    except:
        answer = ""

    return answer
