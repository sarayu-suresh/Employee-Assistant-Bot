import datetime
import os
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

def fetch_recent_emails(user_email=None, max_emails=10):
    service = get_gmail_service()
    date_after = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y/%m/%d")
    results = service.users().messages().list(userId='me', q=f"after:{date_after}", maxResults=max_emails).execute()
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
