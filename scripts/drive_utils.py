from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SERVICE_ACCOUNT_FILE = "config/creds.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

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

def search_drive_folder(query):
    folder_id = "11ZIkUQyWSH3RcvWfOHpE_ZBpTsP0me5q" 
    all_files = list_files_in_folder(folder_id)

    if not all_files:
        return "No documents found in the folder."

    file_names = [file['name'] for file in all_files]
    matches = get_close_matches(query, file_names, n=3, cutoff=0.4)

    if not matches:
        return f"No matching documents found for: '{query}'."

    # Return top matching files with links
    response = []
    for m in matches:
        for f in all_files:
            if f["name"] == m:
                response.append(f"📄 *{f['name']}*\n🔗 {f['webViewLink']}")
                break

    return "\n\n".join(response)


def search_drive_folder(query):
    service = get_drive_service()
    folder_id = "11ZIkUQyWSH3RcvWfOHpE_ZBpTsP0me5q" 
    q = f"'{folder_id}' in parents and trashed = false and name contains '{query}'"

    results = service.files().list(
        q=q,
        spaces="drive",
        fields="files(id, name, webViewLink)",
        pageSize=5
    ).execute()

    files = results.get("files", [])
    print(files)

    if not files:
        return f"No documents found matching '{query}'."
    
    # Return the top match (you can customize scoring later)
    top = files[0]
    return f"📄 *{top['name']}*\n🔗 {top['webViewLink']}"
