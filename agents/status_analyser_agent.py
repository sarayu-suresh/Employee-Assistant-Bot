from models.query_llm import query_mistral_dkubex
from scripts.sheet_utils import get_status_doc_url, get_google_doc_text

class StatusDocAgent:
    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "status_doc"

    def handle(self, message: str, user: str, session: dict) -> dict:
        try:
            # Extract person name from message
            name = query_mistral_dkubex([
                {
                    "role": "system",
                    "content": "Extract only the person's name from the following sentence. Return just the name."
                },
                {
                    "role": "user",
                    "content": message
                }
            ]).strip()

            if not name:
                return {"response": {"text": "❌ Could not extract name. Try saying 'What is the status of <name>'."}}

            doc_url = get_status_doc_url(name)
            if not doc_url:
                return {"response": {"text": f"❌ Could not find a document for {name}."}}

            doc_text = get_google_doc_text(doc_url)
            summary = self.analyze_status_doc(doc_text, question=message, person_name=name)

            return {"response": {"text": f"📄 *Status summary for {name}*:\n\n{summary}"}}

        except Exception as e:
            print("StatusDocAgent error:", str(e))
            return {"response": {"text": "❌ Error analyzing the status document."}}

    def analyze_status_doc(self, doc_text: str, question: str = "", person_name: str = "") -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant tasked with answering questions based on an employee's weekly status report.\n"
                    "Given the employee's name, their status report text, and a user question, generate a direct, insightful, and formal response.\n"
                    "Always answer based only on the status report content. If the information is missing, say 'Not mentioned in the report.'"
                )
            },
            {
                "role": "user",
                "content": f"""Employee: {person_name}
                
Question: {question}

--- Status Report ---
{doc_text.strip()}
--- End of Report ---"""
            }
        ]
        return query_mistral_dkubex(messages)
