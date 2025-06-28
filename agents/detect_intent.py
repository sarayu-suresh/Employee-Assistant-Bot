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
                "- `emails_summarizer`: when the user is asking to summarize emails (e.g., important emails, summarize emails)\n"
                "- `policy_query`: when the user is asking about company policies on leaves, work from home, employee referalls etc. So basically if he asks questions like that.\n"
                 "- `schedule_meeting`: when the user is asking for scheduling a meeting (e.g., meetings, schedule meeting, create a meeting, meeting with)\n"
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
    intent = intent.replace("`", "")
    print(intent)
    if intent in ["raise_leave_request", "raise\_leave\_request"]:
        return "raise_leave_request"
    elif intent in ["raise_it_ticket", "raise\_it\_ticket"]:
        return "raise_it_ticket"
    elif intent in ["raise_hr_ticket", "raise\_hr\_ticket"]:
        return "raise_hr_ticket"
    elif intent in ["greeting", "greeting"]:
        return "greeting"
    elif intent in ["need_help", "need\_help"]:
        return "need_help"
    elif intent in ["document_query", "document\_query"]:
        return "document_query"
    elif intent in ["status_doc", "status\_doc"]:
        return "status_doc"
    elif intent in ["emails_summarizer", "emails\_summarizer"]:
        return "emails_summarizer"
    elif intent in ["policy_query", "policy\_query"]:
        return "policy_query"
    elif intent in ["schedule_meeting", "schedule\_meeting"]:
        return "schedule_meeting"
    else:
        return "general_query"


