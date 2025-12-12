from typing import List, Literal

import requests

from prompt.utils import general_prompt, rag_prompt
from utils.get_config import get_endpoint, get_model_config


class LLM_VNPTAI:
    def __init__(
        self,
        llm_name: Literal["LLM large", "LLM small", "LLM embedings"],
        system_prompt="",
        temperature=0.1,
        top_p=0.9,
        top_k=20,
        n=1,
        max_completion_tokens=64,
        seed=42,
    ):
        self.model = llm_name.split()[-1].lower()
        self.model_cfg = get_model_config(llm_name=llm_name)
        self.endpoint = get_endpoint(llm_name)
        self.url = f"https://api.idg.vnpt.vn/data-service{self.endpoint}"

        self.system_prompt = system_prompt

        self.headers = {
            "Authorization": self.model_cfg["authorization"],
            "Token-id": self.model_cfg["tokenId"],
            "Token-key": self.model_cfg["tokenKey"],
            "Content-Type": "application/json",
        }

        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.n = n
        self.max_completion_tokens = max_completion_tokens
        self.seed = seed

    def get_single_answer(self, user_prompt: str):
        json_data = {
            "model": "vnptai_hackathon_large"
            if self.model == "large"
            else "vnptai_hackathon_small",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "n": self.n,
            "max_completion_tokens": self.max_completion_tokens,
            "seed": self.seed,
        }

        response = requests.post(self.url, headers=self.headers, json=json_data)

        if response.status_code != 200:
            print("HTTP Error:", response.status_code, response.text)
            return "X"

        response_js = response.json()

        if "choices" not in response_js:
            print("API Error:", response_js)
            return "X"

        return response_js["choices"][0]["message"]["content"]

    def get_batch_answers(self, questions: list[str]):
        batch_prompt = (
            "Trả lời lần lượt các câu hỏi dưới đây. "
            "Phản hồi DUY NHẤT dưới dạng JSON với format:\n"
            "{ 'answers': [ ... ] }\n\n"
            "Các câu hỏi:\n"
        )
        for i, q in enumerate(questions, 1):
            batch_prompt += f"{i}. {q}\n"

        json_data = {
            "model": "vnptai_hackathon_large",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": batch_prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "n": 1,
            "max_completion_tokens": self.max_completion_tokens,
            "seed": self.seed,
        }

        response = requests.post(self.url, headers=self.headers, json=json_data)

        if response.status_code != 200:
            print("HTTP Error:", response.status_code, response.text)
            return ["X"] * len(questions)

        response_js = response.json()

        if "choices" not in response_js:
            print("API Error:", response_js)
            return ["X"] * len(questions)

        text = response_js["choices"][0]["message"]["content"]

        # Parse JSON output
        import json

        try:
            ans = json.loads(text)
            return ans["answers"]
        except:
            print("Parse error:", text)
            return ["X"] * len(questions)

    def predict(self, ex: dict[str, str], question_type: str):
        if question_type == "RAG":
            user_prompt = rag_prompt(ex)
        else:
            user_prompt = general_prompt(ex)
        answer = self.get_single_answer(user_prompt)
        return answer
    
    def post_process(self, output: str):
        pass

class Embedding_VNPTAI:
    def __init__(
        self,
        embedding_name: Literal["LLM embedings"],
    ):
        self.model_cfg = get_model_config(llm_name=embedding_name)
        self.endpoint = get_endpoint(embedding_name)
        self.url = f"https://api.idg.vnpt.vn/data-service{self.endpoint}"

        self.headers = {
            "Authorization": self.model_cfg["authorization"],
            "Token-id": self.model_cfg["tokenId"],
            "Token-key": self.model_cfg["tokenKey"],
            "Content-Type": "application/json",
        }

    def get_embedding(self, text: str) -> List[float]:
        json_data = {
            "model": "vnptai_hackathon_embedding",
            "input": text,
        }

        response = requests.post(self.url, headers=self.headers, json=json_data)

        if response.status_code != 200:
            print("HTTP Error:", response.status_code, response.text)
            return []

        response_js = response.json()

        if "data" not in response_js:
            print("API Error:", response_js)
            return []

        return response_js["data"][0]["embedding"]
