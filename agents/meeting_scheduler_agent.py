# agents/meeting_scheduler_agent.py

import uuid
from models.query_llm import query_mistral_dkubex
from scripts.calendar_utils import get_free_slots
from scripts.sheet_utils import get_email_from_name
from datetime import datetime, timezone, timedelta
import pytz
import json
from scripts.cards import build_meeting_slot_selection_card

class MeetingSchedulerAgent:

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "schedule_meeting"

    def handle(self, message: str, user: str, session: dict) -> dict:
        info = self.extract_meeting_request(message)
        print("hi")
        print(info)
        participants = self.resolve_participant_emails(info.get("participants", []))
        if user not in participants:
            participants.append(user)

        date = self.normalize_to_iso_date(info.get("date", ""))
        slot = self.find_common_free_slot(participants, date, info.get("duration", ""), info.get("priority", "Normal"))

        if not slot:
            return {"response": {"text": "❌ No common free time found."}, "session": session}

        available_slots = [slot] if isinstance(slot, str) else slot
        request_id = str(uuid.uuid4())

        return {
            "response": build_meeting_slot_selection_card(
                employee_email=user,
                participants=participants,
                available_slots=available_slots,
                title=info.get("title", "Team Meeting"),
                request_id=request_id
            ),
            "session": session
        }

    def extract_meeting_request(self, message: str) -> dict:
        today_str = datetime.now().strftime("%Y-%m-%d")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a meeting assistant. Extract these fields and return a valid JSON only. "
                    "If the message mentions relative dates like today, tomorrow, or day after tomorrow, "
                    f"convert them to an absolute date in YYYY-MM-DD format based on the current date "
                    f"which is {today_str}.\n"
                    "Return these fields:\n"
                    "{\n"
                    "  \"participants\": [\"name1\", \"name2\"],\n"
                    "  \"duration\": \"number in minutes\",\n"
                    "  \"date\": \"YYYY-MM-DD\",\n"
                    "  \"time\": \"HH:MM am/pm or HH:MM\",\n"
                    "  \"priority\": \"High\" or \"Normal\",\n"
                    "  \"title\": \"...\"\n"
                    "}\n"
                    "Ensure:\n"
                    "- Date is always in YYYY-MM-DD format.\n"
                    "- If no date is mentioned, return null for date.\n"
                    "- Do not include any text outside the JSON."
                )
            },
            {"role": "user", "content": message}
        ]

        raw_response = query_mistral_dkubex(messages)
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            print("❌ Failed to parse JSON:", raw_response)
            return {}

    def resolve_participant_emails(self, participant_list):
        emails = []
        for participant in participant_list:
            participant = participant.strip()
            if "@" in participant:
                emails.append(participant)
            else:
                email = get_email_from_name(participant)
                if email:
                    emails.append(email)
                else:
                    print(f"⚠️ Could not resolve email for: {participant}")
        return emails

    def normalize_to_iso_date(self, date_string):
        # Simplified version for now — can improve later
        try:
            return datetime.strptime(date_string, "%Y-%m-%d").date().isoformat()
        except:
            return datetime.now().date().isoformat()

    def round_up_to_next_quarter(self, dt: datetime) -> datetime:
        discard = timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)
        return (dt + timedelta(minutes=15)) - discard if discard else dt

    def find_common_free_slot(self, emails, date, duration_min, priority="Normal", display_tz="Asia/Kolkata"):
        all_slots = []

        now_utc = datetime.now(timezone.utc) + timedelta(minutes=10)
        now_rounded = self.round_up_to_next_quarter(now_utc)

        for email in emails:
            raw_slots = get_free_slots(email, date, duration_min)
            slot_pairs = []
            for slot in raw_slots:
                try:
                    start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                    slot_pairs.append((start, end))
                except Exception as e:
                    print(f"Slot parse error for {email}: {e}")
            all_slots.append(set(slot_pairs))

        if not all(all_slots):
            return None

        common_slots = set.intersection(*all_slots)
        if not common_slots:
            return None

        future_slots = [(s, e) for s, e in common_slots if s >= now_rounded]
        if priority.lower() == "normal":
            future_slots = [(s, e) for s, e in future_slots if s.hour != 13]

        try:
            user_tz = pytz.timezone(display_tz)
        except Exception:
            user_tz = timezone.utc

        formatted = []
        for s_utc, e_utc in sorted(future_slots)[:3]:
            s_local = s_utc.astimezone(user_tz)
            e_local = e_utc.astimezone(user_tz)
            formatted.append(f"{s_local.strftime('%H:%M')}–{e_local.strftime('%H:%M')}")

        return formatted if formatted else None
