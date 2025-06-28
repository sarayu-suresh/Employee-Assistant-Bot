import datetime
import os
import dateparser
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# If modifying scopes, delete token.pickle
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    token_path = "config/token.pickle"
    creds_path = "config/credentials.json"

    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or get new token if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save token
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def fetch_recent_emails(user_email=None, max_emails=5, from_sender=None, since=None):
    service = get_gmail_service()

    # 🕒 Parse `since` to Gmail-compatible format
    if since:
        parsed_date = dateparser.parse(since)
        if parsed_date:
            date_after = parsed_date.strftime("%Y/%m/%d")
        else:
            # Default to 7 days ago if parsing fails
            date_after = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y/%m/%d")
    else:
        date_after = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y/%m/%d")

    # 🔍 Build Gmail search query
    query = f"after:{date_after}"
    if from_sender:
        query += f" from:{from_sender}"

    results = service.users().messages().list(userId='me', q=query, maxResults=max_emails).execute()
    messages = results.get('messages', [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
        snippet = msg_data.get("snippet", "")
        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        emails.append({
            "from": sender,
            "subject": subject,
            "snippet": snippet,
        })
    return emails
