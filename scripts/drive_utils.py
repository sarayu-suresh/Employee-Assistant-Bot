from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SERVICE_ACCOUNT_FILE = "config/creds.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER_ID = "11ZIkUQyWSH3RcvWfOHpE_ZBpTsP0me5q"  # your folder ID

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def list_files_in_folder(folder_id):
    service = get_drive_service()
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, webViewLink)",
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            break

    return files
