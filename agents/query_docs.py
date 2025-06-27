import numpy as np
import faiss
import json
from models.query_embedding import get_remote_embedding
from models.query_llm import query_mistral_dkubex

index = faiss.read_index("embeddings/faiss_index.idx")
with open("embeddings/chunk_data.json") as f:
    data = json.load(f)
chunks = data["chunks"]

def answer_from_docs(query: str) -> str:
    query_vec = get_remote_embedding(query)
    if not query_vec:
        return "⚠️ Couldn't fetch embeddings for your query right now."

    _, indices = index.search(np.array([query_vec]), 3)
    context = "\n\n".join([chunks[i] for i in indices[0][:2]])

    messages = [
        {"role": "system", "content": "You are a helpful assistant trained to answer questions based on company policy documents."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    return query_mistral_dkubex(messages)

# def answer_from_docs(query: str) -> str:
#     from sentence_transformers import SentenceTransformer
#     embedder = SentenceTransformer("all-MiniLM-L6-v2")
#     query_vec = embedder.encode([query])
#     _, indices = index.search(np.array(query_vec), 3)
#     context = "\n\n".join([chunks[i] for i in indices[0][:2]])
#     messages = [
#         {"role": "system", "content": "You are a helpful assistant trained to answer questions based on company policy documents."},
#         {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
#     ]
#     return query_mistral_dkubex(messages)