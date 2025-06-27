import gspread
import httpx
import requests
import os
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from .chat_auth import get_chat_access_token
from .cards import build_leave_approval_card

load_dotenv()

SPACE_ID = os.getenv("MANAGER_SPACE_ID")  

def get_sheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("config/creds.json", scope)
    return gspread.authorize(creds)

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
