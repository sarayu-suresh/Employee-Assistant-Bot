from models.query_llm import query_mistral_dkubex

def detect_intent(message: str):
    if "github.com" in message:
        return "github_repo_query"
    
    messages = [
        {
            "role": "system",
            "content": "You are an intent classifier. Classify the user message based on the question they are asking into one of these intents only: raise_leave_request, raise_it_ticket, raise_hr_ticket, general_query, greeting. Just return the intent label. No explanation. Understand whether they are asking for an action or a doubt/question"
        },
        {"role": "user", "content": message}
    ]
    result = query_mistral_dkubex(messages)
    
    intent = result.strip().lower()
    if "raise_leave_request" in intent:
        return "raise_leave_request"
    elif "raise_it_ticket" in intent:
        return "raise_it_ticket"
    elif "raise_hr_ticket" in intent:
        return "raise_hr_ticket"
    elif "greeting" in intent:
        return "greeting"
    else:
        return "general_query"