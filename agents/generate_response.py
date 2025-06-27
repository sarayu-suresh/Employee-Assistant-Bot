from models.query_llm import query_mistral_dkubex

def generate_response(user_message: str, instruction: str = "You are a friendly assistant.") -> str:
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_message}
    ]
    return query_mistral_dkubex(messages)