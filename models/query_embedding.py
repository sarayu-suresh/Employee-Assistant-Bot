import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_remote_embedding(text: str) -> list:
    embedding_endpoint = os.getenv("EMBEDDING_ENDPOINT")  # e.g., "https://your-dkubex-host/v1/"
    embedding_token = os.getenv("EMBEDDING_TOKEN")        # Bearer token

    headers = {
        "Authorization": f"Bearer {embedding_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": [text]
    }

    try:
        res = requests.post(embedding_endpoint, headers=headers, json=payload, verify=False, timeout=30)
        res.raise_for_status()
        return res.json()["data"][0]["embedding"]
    except Exception as e:
        print("Embedding error:", e)
        return []
    
