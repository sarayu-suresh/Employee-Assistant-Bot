from google.oauth2 import service_account
import google.auth.transport.requests

def get_chat_access_token(service_account_path: str) -> str:
    """
    Generates an OAuth2 Bearer token using a service account for Google Chat API.

    Args:
        service_account_path (str): Path to the service account JSON file.

    Returns:
        str: Bearer token for authorization in API requests.
    """
    SCOPES = ["https://www.googleapis.com/auth/chat.bot"]
    
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=SCOPES
    )

    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    return credentials.token
