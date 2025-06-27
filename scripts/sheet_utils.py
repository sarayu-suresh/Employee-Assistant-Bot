import gspread
import httpx
import re
import requests
import os
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from .chat_auth import get_chat_access_token
from .cards import build_leave_approval_card

from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()

SPACE_ID = os.getenv("MANAGER_SPACE_ID")  

def get_sheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("config/creds.json", scope)
    return gspread.authorize(creds)

def get_doc_client():
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    creds = service_account.Credentials.from_service_account_file(
        "config/creds.json", scopes=SCOPES
    )
    return build('docs', 'v1', credentials=creds)


def get_manager_email(employee_email: str) -> str:
    client = get_sheet_client()
    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1oKLqN_43u9jJAlbMlWQ1BxT7PAZPFM7tnXT6q5GzQLM/edit#gid=0"
    ).sheet1
    data = sheet.get_all_records()

    for row in data:
        if row["Employee Email"].strip().lower() == employee_email.strip().lower():
            return row["Manager Email"]
    return None

def notify_manager_in_space(employee_email: str, reason: str, request_id: str):
    manager_email = get_manager_email(employee_email)
    if not manager_email:
        print("Manager not found for:", employee_email)
        return False

    token = get_chat_access_token("creds.json")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"https://chat.googleapis.com/v1/spaces/{SPACE_ID}/messages"


    payload = build_leave_approval_card(employee_email, reason, manager_email, request_id)

    response = requests.post(url, headers=headers, json=payload)

    print("Manager notify response:", response.status_code, response)
    return response.status_code == 200



def get_status_doc_url(name: str) -> str:
    client = get_sheet_client()
    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1qsHAI2ReBfGG0BhH5iBRODsQ5ZZgLnlkRodIS8AaBjA/edit?gid=0#gid=0"
    ).sheet1
    data = sheet.get_all_records()

    for row in data:
        if row["Name"].strip().lower() == name.strip().lower():
            return row["Status Doc URL"]
    return None



def extract_doc_id(doc_url: str) -> str:
    match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid Google Docs URL")


def get_google_doc_text(doc_url: str) -> str:
    doc_id = extract_doc_id(doc_url)
    service = get_doc_client()
    document = service.documents().get(documentId=doc_id).execute()
    content = document.get('body', {}).get('content', [])

    text_output = ''
    for element in content:
        if 'paragraph' in element:
            for elem in element['paragraph'].get('elements', []):
                if 'textRun' in elem:
                    text_output += elem['textRun']['content']
    return text_output
