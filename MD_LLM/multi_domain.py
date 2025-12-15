from core.llm_interface import LLM_VNPTAI
from prompt.agent_prompt import (
    GENERAL_USER_PROMPT,
    MULTI_DOMAIN_SYSTEM_PROMPT,
    SYSTEM_RAG_PROMPT,
    USER_RAG_PROMPT,
)
from RAG.resources import BM25, CORPUS_TEXTS, EMBEDDER, FAISS_INDEX, METADATA
from RAG.retriever import retrieve_context_faiss_hybrid
from RAG.utils import need_rag
from utils.post_processing import choice_to_letter


def solve_multi_domain(
    gate_llm: LLM_VNPTAI,
    answer_llm: LLM_VNPTAI,
    test_case: dict[str, str],
) -> str:
    question = test_case["question"]
    choices = test_case["choices"]

    use_rag = need_rag(gate_llm, question)
    print(f"Use RAG: {use_rag}")
    system_prompt = ""
    if use_rag:
        context = retrieve_context_faiss_hybrid(
            question=question,
            embedder=EMBEDDER,
            faiss_index=FAISS_INDEX,
            metadata=METADATA,
            bm25=BM25,
            corpus_texts=CORPUS_TEXTS,
            top_k=5,
            faiss_k=20,
            alpha=0.6,
        )

        print(context)

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

        system_prompt = MULTI_DOMAIN_SYSTEM_PROMPT

    # Step 3: Answer

    print("Prompt:", prompt)
    raw = answer_llm.get_single_answer(
        user_prompt=prompt,
        system_prompt=system_prompt,
    )

    # Step 4: Post-process
    return choice_to_letter(raw, choices)
