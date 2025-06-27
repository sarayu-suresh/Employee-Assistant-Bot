import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def query_mistral_dkubex(messages, temperature=0.7):
    endpoint = os.getenv("MISTRAL_ENDPOINT")
    token = os.getenv("MISTRAL_TOKEN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": messages,
        "temperature": temperature
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, verify=False, timeout=30)
        response.raise_for_status()
        output = response.json()
        return output.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print("Mistral API error:", e)
        return "Sorry, I couldn't generate a response right now."