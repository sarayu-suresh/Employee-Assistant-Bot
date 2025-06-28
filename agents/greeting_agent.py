
from models.query_llm import query_mistral_dkubex

class GreetingAgent:

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "greeting"

    def handle(self, message: str, user: str, session: dict) -> dict:
        instruction = "You are a friendly assistant. Greet the user."
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": message}
        ]
        response = query_mistral_dkubex(messages)
        return {
            "response": {"text": response},
            "session": session  # return same session if unchanged
        }
