import numpy as np
import faiss
import json

from models.query_embedding import get_remote_embedding
from models.query_llm import query_mistral_dkubex

class PolicyQueryAgent:
    def __init__(self):
        self.index = faiss.read_index("embeddings/faiss_index.idx")
        with open("embeddings/chunk_data.json") as f:
            data = json.load(f)
        self.chunks = data["chunks"]

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "policy_query"

    def handle(self, message: str, user: str, session: dict) -> dict:
        query_vec = get_remote_embedding(message)
        if not query_vec:
            return {"response": {"text": "⚠️ Couldn't fetch embeddings for your query right now."}, "session": session}

        _, indices = self.index.search(np.array([query_vec]), 3)
        context = "\n\n".join([self.chunks[i] for i in indices[0][:2]])

        messages = [
            {"role": "system", "content": "You are a helpful assistant trained to answer questions based on company policy documents."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {message}"}
        ]
        answer = query_mistral_dkubex(messages)

        return {"response": {"text": answer.strip() if answer else "❌ Failed to generate answer."}, "session": session}
