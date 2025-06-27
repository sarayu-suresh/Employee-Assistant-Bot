# index_builder_dkubex.py
import os
import json
import faiss
import fitz
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT")
EMBEDDING_TOKEN = os.getenv("EMBEDDING_TOKEN")

headers = {
    "Authorization": f"Bearer {EMBEDDING_TOKEN}",
    "Content-Type": "application/json"
}

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])

def get_embedding(text):
    payload = {
        "input": [text]  # Wrap in list to match typical embedding APIs
    }
    try:
        response = requests.post(EMBEDDING_ENDPOINT, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        print("Embedding error:", e)
        return None

data_dir = "data"
chunks = []
chunk_sources = []

# Step 1: Chunk PDFs
for filename in os.listdir(data_dir):
    if filename.endswith(".pdf"):
        file_path = os.path.join(data_dir, filename)
        text = extract_text_from_pdf(file_path)
        doc_chunks = text.split("\n\n")
        chunks.extend(doc_chunks)
        chunk_sources.extend([filename] * len(doc_chunks))

# Step 2: Get embeddings from DKubeX
embeddings = []
valid_chunks = []

MAX_CHARS = 1000  # You can tune this to 800–1500 depending on your model's limit

for chunk in chunks:
    if len(chunk) > MAX_CHARS:
        subchunks = [chunk[i:i+MAX_CHARS] for i in range(0, len(chunk), MAX_CHARS)]
    else:
        subchunks = [chunk]

    for sub in subchunks:
        emb = get_embedding(sub)
        if emb:
            embeddings.append(emb)
            valid_chunks.append(sub)


# for chunk in chunks:
#     emb = get_embedding(chunk)
#     if emb:
#         embeddings.append(emb)
#         valid_chunks.append(chunk)

embeddings_np = np.array(embeddings).astype("float32")
dimension = embeddings_np.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings_np)

faiss.write_index(index, "embeddings/faiss_index.idx")

with open("embeddings/chunk_data.json", "w") as f:
    json.dump({"chunks": valid_chunks, "sources": chunk_sources[:len(valid_chunks)]}, f)
