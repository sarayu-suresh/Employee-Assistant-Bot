from models.query_llm import query_mistral_dkubex

def detect_intent(message: str):
    if "github.com" in message:
        return "github_repo_query"
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an intent classification assistant. Based on the user's message, classify it into one of the following intent labels **only**:\n\n"
                "- `raise_leave_request`: when the user is requesting or asking to take leave\n"
                "- `raise_it_ticket`: when the user is reporting or requesting help for an IT issue (e.g., laptop issue, email problem)\n"
                "- `raise_hr_ticket`: when the user is asking about HR-related issues (e.g., salary, onboarding, benefits)\n"
                "- `greeting`: if the user is just saying hello, hi, or any greeting\n"
                "- `document_query`: if the user is asking to fetch or get any company document\n"
                "- `need_help`: when the user is stuck or asking for help in some technical or work-related task (e.g., React issue, deployment help)\n"
                "- `status_doc`: when the user is asking for status (e.g., status of, status)\n"
                "- `emails_summarizer`: when the user is asking for emails (e.g., important emails, summarize emails)\n"
                "- `general_query`: when the user is asking a general question that doesn't match the above categories\n\n"
                "Understand whether the message is an action (like requesting leave or raising a ticket) or a general query. "
                "Return **only** the correct intent label. No explanation, no formatting."
            )
        },
        {"role": "user", "content": message}
    ]

    result = query_mistral_dkubex(messages)
    print(result)

    intent = result.strip().lower()
    if "raise_leave_request" in intent:
        return "raise_leave_request"
    elif "raise_it_ticket" in intent:
        return "raise_it_ticket"
    elif "raise_hr_ticket" in intent:
        return "raise_hr_ticket"
    elif "greeting" in intent:
        return "greeting"
    elif "need_help" in intent:
        return "need_help"
    elif "document_query" in intent:
        return "document_query"
    elif "status_doc" in intent:
        return "status_doc"
    elif "emails_summarizer" in intent:
        return "emails_summarizer"
    else:
        return "general_query"
