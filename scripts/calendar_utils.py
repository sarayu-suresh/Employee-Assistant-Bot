import os
import pickle
from datetime import datetime, timedelta, timezone
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import dateparser
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = "config/token.pickle"
CREDS_PATH = "config/credentials.json"

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def get_free_slots(email: str, date: str, duration_min=30):
    service = get_calendar_service()

    # ✅ Validate duration
    try:
        duration_min = int(duration_min)
        if duration_min not in [15, 30, 45, 60]:
            duration_min = 30
    except Exception:
        duration_min = 30

    # ✅ Prepare time range for 9 AM to 5 PM in UTC
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    start_dt = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, tzinfo=timezone.utc)
    end_dt = datetime.combine(date_obj, datetime.min.time()).replace(hour=17, tzinfo=timezone.utc)

    # ✅ Get current UTC time + 10-minute buffer
    now = datetime.now(timezone.utc)
    min_start_time = now + timedelta(minutes=10)

    # ✅ If meeting date is today, skip slots before `min_start_time`
    if date_obj == now.date():
        start_dt = max(start_dt, min_start_time)

    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "items": [{"id": email}]
    }

    try:
        result = service.freebusy().query(body=body).execute()
        busy_slots = result['calendars'][email]['busy']
        busy_intervals = [
            (
                datetime.fromisoformat(b['start'].replace('Z', '+00:00')),
                datetime.fromisoformat(b['end'].replace('Z', '+00:00'))
            )
            for b in busy_slots
        ]

        free_slots = []
        current = start_dt

        while current + timedelta(minutes=duration_min) <= end_dt:
            candidate_end = current + timedelta(minutes=duration_min)

            # ✅ Skip if the *start* time is before `min_start_time`
            if current < min_start_time:
                current += timedelta(minutes=15)
                continue

            # ✅ Check overlap
            overlap = any(
                not (candidate_end <= b_start or current >= b_end)
                for b_start, b_end in busy_intervals
            )

            if not overlap:
                free_slots.append({
                    'start': current.isoformat().replace("+00:00", "Z"),
                    'end': candidate_end.isoformat().replace("+00:00", "Z")
                })

            current += timedelta(minutes=15)

        return free_slots

    except Exception as e:
        print(f"❌ Failed to fetch free slots for {email}: {e}")
        return []

def normalize_to_iso_date(date_str: str) -> str:
    if date_str.strip().lower() == "not mentioned":
        return datetime.today().date().isoformat()

    parsed = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'future'})
    if parsed:
        return parsed.date().isoformat()
    return datetime.today().date().isoformat()

def create_calendar_event(title, start_time_str, duration_min, attendees, description=""):
    service = get_calendar_service()

    allowed_durations = {15, 30, 45, 60}
    try:
        duration_int = int(duration_min)
        if duration_int not in allowed_durations:
            duration_int = 30
    except (ValueError, TypeError):
        duration_int = 30

    start_dt = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = start_dt + timedelta(minutes=duration_int)

    event = {
        'summary': title or "Meeting",
        'description': description or "Scheduled via AskX bot",
        'start': {
            'dateTime': start_dt.isoformat() + 'Z',
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_dt.isoformat() + 'Z',
            'timeZone': 'UTC',
        },
        'attendees': [{'email': email} for email in attendees],
        'conferenceData': {
            'createRequest': {
                'requestId': f"meet_{int(datetime.utcnow().timestamp())}"
            }
        },
    }

    event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1,
        sendUpdates='all'
    ).execute()

    return event.get('htmlLink'), event.get('hangoutLink')