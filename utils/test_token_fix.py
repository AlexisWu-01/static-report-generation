from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "token.json"

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,)
print(credentials)
# admin_service = build("admin", "directory_v1", credentials=credentials)
# group = admin_service.groups().list(domain="example.com").execute()
# print("groups list: ", group)