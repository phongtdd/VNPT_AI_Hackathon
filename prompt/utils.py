from prompt.agent_prompt import GENERAL_USER_PROMPT, USER_RAG_PROMPT
from RAG.get_top_param import top_similarity

def general_prompt(ex: dict[str, str]):
    question = ex["question"]
    choices = ex["choices"]
    user_prompt = GENERAL_USER_PROMPT.format(question=question, choices=choices)

    return user_prompt


def rag_prompt(ex: dict[str, str]) -> str:
    questions = ex["question"]
    choices = ex["choices"]
    start_key = "Đoạn thông tin:"
    end_key = "Câu hỏi:"
    start_index = questions.find(start_key)
    end_index = questions.find(end_key)
    content = questions[start_index:end_index].strip()
    question = questions[end_index:].strip()

    top_paras = top_similarity(question, content, top_k=3)
    retrieved_content = "\n\n".join([para for para, score in top_paras])
    user_prompt = USER_RAG_PROMPT.format(
        content=retrieved_content, question=question, choices=choices
    )
    return user_prompt
