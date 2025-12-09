import json
from typing import Literal

def get_model_config(
    llm_name : Literal["LLM large", "LLM small", "LLM embedings"], 
    path="api-keys.json"
    ):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON file has to be in list format: [{}, {}, ...]")

    for item in data:   
        if item.get("llmApiName") == llm_name:
            return item

    return None
def get_endpoint(
    llm_name: Literal["LLM large", "LLM small", "LLM embedings"]
    ): 
    mapping = {
        "LLM large": "/v1/chat/completions/vnptai-hackathon-large", 
        "LLM small": "/v1/chat/completions/vnptai-hackathon-small", 
        "LLM embedings": '/vnptai-hackathon-embedding', 
        } 
    return mapping.get(llm_name, "")