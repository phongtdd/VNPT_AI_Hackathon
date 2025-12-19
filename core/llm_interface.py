import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

import numpy as np
import requests
from tqdm import tqdm

from prompt.utils import general_prompt, rag_prompt
from utils.get_config import get_endpoint, get_model_config


class LLM_VNPTAI:
    def __init__(
        self,
        llm_name: Literal["LLM large", "LLM small"],
        system_prompt: str = "",
        temperature: float = 0.1,
        top_p: float = 0.9,
        top_k: int = 20,
        n: int = 1,
        max_completion_tokens: int = 64,
        seed: int = 42,
        response_format=None,
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
        if response_format:
            self.response_format = response_format
        else:
            self.response_format = None

    def get_single_answer(self, user_prompt: str, system_prompt: str = ""):
        json_data = {
            "model": "vnptai_hackathon_large"
            if self.model == "large"
            else "vnptai_hackathon_small",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt if system_prompt else self.system_prompt,
                },
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "n": self.n,
            "max_completion_tokens": self.max_completion_tokens,
            "seed": self.seed,
        }
        if self.response_format:
            json_data["response_format"] = self.response_format

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
        if self.response_format:
            json_data["response_format"] = self.response_format

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
        max_workers: int = 4,
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

        # ===== Embedding limits =====
        # ===== Embedding limits =====
        self.MAX_TOKENS = 7500
        self.CHAR_PER_TOKEN = 4
        self.max_workers = max_workers

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // self.CHAR_PER_TOKEN)

    def _embed_batch(self, batch: list[str], max_retries: int = 5):
        for attempt in range(1, max_retries + 1):
            try:
                r = requests.post(
                    self.url,
                    headers=self.headers,
                    json={
                        "model": "vnptai_hackathon_embedding",
                        "input": batch,
                    },
                    timeout=60,
                )

                if r.status_code == 429:
                    raise RuntimeError("Rate limited")

                if r.status_code != 200:
                    raise RuntimeError(r.text)

                data = r.json().get("data")
                if not data:
                    raise RuntimeError("Invalid response")

                return [item["embedding"] for item in data]

            except Exception as e:
                if attempt == max_retries:
                    raise
                time.sleep(2**attempt)

    def get_embedding(self, text: str) -> list[float]:
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

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Token-aware + parallel embedding
        """
        batches = []
        batch, tokens = [], 0

        for t in texts:
            est = self._estimate_tokens(t)
            if batch and tokens + est > self.MAX_TOKENS:
                batches.append(batch)
                batch, tokens = [], 0

            batch.append(t)
            tokens += est

        if batch:
            batches.append(batch)

        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = [pool.submit(self._embed_batch, b) for b in batches]

            for f in tqdm(as_completed(futures), total=len(futures), desc="Embedding"):
                results.extend(f.result())

        return np.asarray(results, dtype="float32")
