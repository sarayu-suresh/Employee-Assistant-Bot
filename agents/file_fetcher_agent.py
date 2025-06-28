
from models.query_llm import query_mistral_dkubex
from scripts.drive_utils import list_files_in_folder

class FileFetcherAgent:

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "document_query"
    
    def handle(self, message: str, user: str, session: dict) -> dict:
        FOLDER_ID = "11ZIkUQyWSH3RcvWfOHpE_ZBpTsP0me5q"
        files = list_files_in_folder(FOLDER_ID)

        if not files:
            return {"response": {"text": "📂 No documents found in the folder."}, "session": session}

        file_context = "\n".join(
            [f"{file['name']} — {file['webViewLink']}" for file in files]
        )

        prompt = (
            f"You are a helpful assistant. A user is asking to find a document from the company's internal Drive.\n"
            f"Here is the list of available documents with their links:\n\n"
            f"{file_context}\n\n"
            f"User query: '{message}'\n"
            f"Based on the query, return the **most relevant document link** (just the link, no extra explanation)."
        )

        response = query_mistral_dkubex([{"role": "user", "content": prompt}])
        answer = response.strip() if response else "❌ Couldn't find a relevant document."

        return {"response": {"text": answer}, "session": session}
