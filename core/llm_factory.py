from core.llm_interface import LLM_VNPTAI
from stem_solver.stem import LLMStem


def build_llm(label_config, llm_name):
    if label_config["llm_type"] == "vnptai":
        return LLM_VNPTAI(
            llm_name=llm_name,
            system_prompt=label_config["system_prompt"],
        )

    if label_config["llm_type"] == "stem":
        return LLMStem(
            llm_name=llm_name,
            system_prompt=label_config["system_prompt"],
            temperature=0.0,
            top_p=1.0,
            n=1,
            max_completion_tokens=2048,
        )

    raise ValueError("Unknown LLM type")
