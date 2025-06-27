from models.query_llm import query_mistral_dkubex

def summarize_email(email):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant that summarizes emails into 1–2 sentences.\n"
                "Focus on the key message and context of the email. Keep it concise and clear."
            )
        },
        {
            "role": "user",
            "content": f"""Subject: {email['subject']}
From: {email['from']}

Content:
{email['snippet']}
"""
        }
    ]
    return query_mistral_dkubex(messages)

def extract_task(summary):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant that extracts actionable tasks from short summaries of emails.\n"
                "If there is a to-do or request, extract it using this format:\n\n"
                "- Task: <short task description>\n"
                "- Due Date: <date, deadline, or 'Not mentioned'>\n"
                "- Assigned By: <name or email or 'Unknown'>\n"
                "- Urgency: High / Medium / Low\n\n"
                "If there is no task, respond exactly with: No actionable task."
            )
        },
        {
            "role": "user",
            "content": f"""Summary: {summary}"""
        }
    ]
    return query_mistral_dkubex(messages)

def rank_and_format_tasks(task_responses):
    ranked = []

    for item in task_responses:
        if "Task:" in item:
            urgency_score = 0
            if "High" in item: urgency_score = 3
            elif "Medium" in item: urgency_score = 2
            elif "Low" in item: urgency_score = 1
            ranked.append((urgency_score, item.strip()))

    ranked.sort(reverse=True)

    final = "🗂️ *Your Weekly To-Do Summary (Ranked)*\n\n"
    for i, (_, task) in enumerate(ranked, 1):
        final += f"{i}. {task}\n\n"

    if any("High" in t for _, t in ranked):
        final += "🚨 *You have urgent tasks to act on!*\n"

    if not ranked:
        final += "✅ No actionable tasks found in your recent emails."

    return final.strip()
