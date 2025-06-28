from models.query_llm import query_mistral_dkubex
from scripts.drive_utils import list_files_in_folder

def search_drive_folder(query):
    FOLDER_ID = "11ZIkUQyWSH3RcvWfOHpE_ZBpTsP0me5q"  # your folder ID
    files = list_files_in_folder(FOLDER_ID)

    if not files:
        return "📂 No documents found in the folder."

    file_context = "\n".join(
        [f"{file['name']} — {file['webViewLink']}" for file in files]
    )

    prompt = (
        f"You are a helpful assistant. A user is asking to find a document from the company's internal Drive.\n"
        f"Here is the list of available documents with their links:\n\n"
        f"{file_context}\n\n"
        f"User query: '{query}'\n"
        f"Based on the query, return the **most relevant document link** (just the link, no extra explanation)."
    )

    response = query_mistral_dkubex([{"role": "user", "content": prompt}])

    return response.strip() if response else "❌ Couldn't find a relevant document."