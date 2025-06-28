import re
import json
import requests
from models.query_llm import query_mistral_dkubex
from scripts.email_utils import fetch_recent_emails
from scripts.chat_auth import get_chat_access_token
from threading import Thread
from datetime import datetime


class EmailSummarizerAgent:

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "emails_summarizer"

    def handle(self, message: str, user: str, session: dict) -> dict:
        space_id = session.get("space_id")
        if not space_id:
            return {"response": {"text": "❌ Could not identify chat space."}, "session": session}

        # Start background thread for processing
        Thread(target=self.process_summary_and_post, args=(user, message, space_id)).start()

        # Return a loading message immediately
        loading_card = {
            "cardsV2": [{
                "cardId": "email-loading",
                "card": {
                    "sections": [{
                        "widgets": [{
                            "textParagraph": {
                                "text": "<b>📬 Fetching your emails...</b><br>Summarizing and extracting tasks. Please wait ⏳"
                            }
                        }]
                    }]
                }
            }]
        }
        return {"response": loading_card, "session": session}

    def process_summary_and_post(self, user: str, message: str, space_id: str):
        try:
            email_info = self.extract_email_request_info(message)
            print("Extracted email info:", email_info)
            emails = fetch_recent_emails(
                user,
                max_emails=email_info.get("count", 5),
                from_sender=email_info.get("from", None),
                since=email_info.get("since", None)
            )
            if not emails:
                self.send_followup(space_id, "📭 No recent emails found.")
                return

            task_responses = []
            for email in emails:
                summary = self.summarize_email(email)
                task = self.extract_task(summary)
                task_responses.append(task)
            print("Extracted tasks:", task_responses)
            final_summary = self.rank_and_format_tasks(task_responses, message) 
            self.send_followup(space_id, final_summary)

        except Exception as e:
            print("Email summarization error:", e)
            self.send_followup(space_id, "⚠️ Could not analyze emails.")

    def send_followup(self, space_id: str, text: str):
        token = get_chat_access_token("config/creds.json")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"https://chat.googleapis.com/v1/{space_id}/messages"
        payload = {"text": text}
        requests.post(url, headers=headers, json=payload)

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

    def classify_email_instruction(self, user_message: str) -> str:
        """
        Classifies user intent into one of: 'summarize', 'rank', 'filter_priority', or 'list_tasks'
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a classifier that labels a user message into one of the following intents:\n"
                    "- summarize: if user wants a summary of emails\n"
                    "- rank: if user wants ranked list of tasks by urgency\n"
                    "- filter_priority: if user only wants high-priority items\n"
                    "- list_tasks: if user wants all actionable tasks\n\n"
                    "Respond with only one word: summarize / rank / filter_priority / list_tasks"
                )
            },
            {"role": "user", "content": user_message}
        ]
        response = query_mistral_dkubex(messages).strip().lower()
        return response if response in ["summarize", "rank", "filter_priority", "list_tasks"] else "summarize"


    def rank_and_format_tasks(self, task_responses, user_message):
        intent = self.classify_email_instruction(user_message)
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an AI assistant. The user asked to: *{intent}*\n\n"
                    "You will receive a list of email responses that may include actionable tasks or summaries. "
                    "Respond with one of the following formats depending on the intent:\n\n"
                    "- summarize: Return a concise summary of each email in 1–2 lines.\n"
                    "- rank: Return tasks sorted by urgency with numbers.\n"
                    "- filter_priority: Show only tasks with 'High' urgency.\n"
                    "- list_tasks: Show all actionable tasks.\n\n"
                    "Use this heading:\n\n"
                    "🧠 *Smart Email Summary*\n\n"
                    "If no relevant items, respond: '✅ No relevant emails found.'"
                )
            },
            {
                "role": "user",
                "content": f"""User message: {user_message}

    Email Responses:
    {chr(10).join(f"- {resp.strip()}" for resp in task_responses)}
    """
            }
        ]

        return query_mistral_dkubex(messages).strip()


    def extract_email_request_info(self, user_message: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a smart assistant that extracts structured information from natural language email summary requests.\n"
                    "Return the result as a **strict JSON object only**, with the following keys:\n\n"
                    "- count: number of emails to fetch (an integer or 'all')\n"
                    "- from: name or email of the sender to filter by, or 'None'\n"
                    "- since: a **resolved date** in 'YYYY-MM-DD' format (not expressions like 'last week')\n\n"
                    "❗ Return only the JSON object. Do NOT include any notes or extra text."
                )
            },
            {"role": "user", "content": user_message}
        ]

        try:
            response = query_mistral_dkubex(messages)
            print("UnParsed response")
            print(response)

            # Extract first valid JSON block
            match = re.search(r'\{.*?\}', response, re.DOTALL)
            parsed = json.loads(match.group())
            print("Parsed JSON:\n", parsed)

            # Normalize 'count'
            if parsed.get("count") == "all":
                parsed["count"] = 50
            else:
                parsed["count"] = int(parsed.get("count", 5))

            # Clean 'from'
            parsed["from"] = None if parsed.get("from") in ["None", "", None] else parsed["from"]

            # Validate 'since' format
            since = parsed.get("since")
            try:
                datetime.strptime(since, "%Y-%m-%d")
            except:
                parsed["since"] = None  # or use default fallback:
                # parsed["since"] = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

            return parsed

        except Exception as e:
            print("❌ Failed to parse user email request info:", e)
            return {
                "count": 5,
                "from": None,
                "since": None
            }
