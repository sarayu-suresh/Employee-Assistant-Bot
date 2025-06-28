# agents/email_summarizer.py
from models.query_llm import query_mistral_dkubex
from scripts.email_utils import fetch_recent_emails

class EmailSummarizerAgent:

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "emails_summarizer"

    def handle(self, message: str, user: str, session: dict) -> dict:
        try:
            emails = fetch_recent_emails(user, max_emails=5)
            if not emails:
                return {"response": {"text": "📭 No recent emails found."}, "session": session}

            task_responses = []
            for email in emails:
                summary = self.summarize_email(email)
                task = self.extract_task(summary)
                print("Task Extracted:", task)
                task_responses.append(task)

            final_summary = self.rank_and_format_tasks(task_responses)
            return {"response": {"text": final_summary}, "session": session}

        except Exception as e:
            print("Email summarization error:", e)
            return {"response": {"text": "⚠️ Could not analyze emails."}, "session": session}

    def summarize_email(self, email):
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

    def extract_task(self, summary):
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

    def rank_and_format_tasks(self, task_responses):
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
