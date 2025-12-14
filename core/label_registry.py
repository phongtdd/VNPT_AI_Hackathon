from prompt.agent_prompt import (
    GENERAL_SYSTEM_PROMPT,
    PR_SYSTEM_PROMPT,
    STEM_PROMPT,
    SYSTEM_RAG_PROMPT,
)

LABEL_REGISTRY: dict[str, dict[str, str]] = {
    "RAG": {
        "llm_type": "vnptai",
        "system_prompt": SYSTEM_RAG_PROMPT,
        "question_type": "RAG",
        "postprocess": "choice_to_letter",
    },
    "Precision-Critical": {
        "llm_type": "vnptai",
        "system_prompt": PR_SYSTEM_PROMPT,
        "question_type": "Precision-Critical",
        "postprocess": "choice_to_letter",
    },
    "STEM": {
        "llm_type": "stem",
        "system_prompt": STEM_PROMPT,
        "question_type": "STEM",
        "postprocess": "stem_answer",
    },
    "Multi-Domain": {
        "llm_type": "vnptai",
        "system_prompt": GENERAL_SYSTEM_PROMPT,
        "question_type": "Multi-Domain",
        "postprocess": "choice_to_letter",
    },
}
