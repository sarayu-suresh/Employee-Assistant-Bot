import gspread
import httpx
import re
import requests
import os
import json
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

from .chat_auth import get_chat_access_token
from .cards import build_leave_approval_card
from models.query_llm import query_mistral_dkubex



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

    token = get_chat_access_token("config/creds.json")
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

def get_name_email_map():
    client = get_sheet_client()
    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1XbVka8zPAQaBmirGYCUocPeRnD5I7FLf3JCA09HFP20/edit#gid=0"
    ).sheet1  

    data = sheet.get_all_records()

    email = {row["Name"].strip().lower(): row["Email"].strip() for row in data if row.get("Name") and row.get("Email")}
    print(email)

    return email

def resolve_closest_name_with_llm(input_name: str, data: list[dict]) -> str:
    """
    Uses LLM to find the closest matching name from the data list for a possibly misspelled input.
    Returns the best matching name exactly as in data, or "Unknown".
    """

    valid_names = [row["Name"] for row in data if row.get("Name")]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that resolves misspelled names by matching them "
                "to the most likely correct name from a known directory.\n"
                "Always return a strict JSON like this: {\"match\": \"Correct Name\"}.\n"
                "If no match is confident, return: {\"match\": \"Unknown\"}.\n\n"
                f"Directory: {valid_names}"
            )
        },
        {
            "role": "user",
            "content": f"Find closest match for: {input_name}"
        }
    ]

    raw_response = query_mistral_dkubex(messages)
    
    try:
        parsed = json.loads(raw_response)
        match = parsed.get("match", "Unknown")
        return match if match in valid_names else "Unknown"
    except Exception:
        print("❌ Failed to parse LLM response:", raw_response)
        return "Unknown"


def get_email_from_name(name: str) -> str:
    client = get_sheet_client()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1XbVka8zPAQaBmirGYCUocPeRnD5I7FLf3JCA09HFP20/edit?usp=sharing").sheet1
    data = sheet.get_all_records()
    print(data)
    for row in data:
        if row["Name"].strip().lower() == name.strip().lower():
            return row["Email"]

    closest_name_match = resolve_closest_name_with_llm(name, data)
    for row in data:
        if row["Name"].strip().lower() == closest_name_match.strip().lower():
            return row["Email"]
    return None

