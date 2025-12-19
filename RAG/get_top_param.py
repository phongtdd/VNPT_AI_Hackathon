import numpy as np



def _split_paragraph(text):
    return text.split("\n\n")


def _cosine_similarity(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def top_similarity(question, context, top_k=None):
    from core.llm_interface import Embedding_VNPTAI

    embedding_model = Embedding_VNPTAI(embedding_name="LLM embedings")
    paragraphs = _split_paragraph(context)

    # Get embedding for question
    q_vec = embedding_model.get_embedding(question)

    results = []
    for para in paragraphs:
        sent_vec = embedding_model.get_embedding(para)
        score = _cosine_similarity(q_vec, sent_vec)
        results.append((para, score))

    # Sort by similarity DESC
    results.sort(key=lambda x: x[1], reverse=True)

    if top_k:
        return results[:top_k]
    return results
