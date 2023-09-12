"""
Author: Andrew DeCandia, Alexis Wu
Project: Air Partners

Script for setting/ refreshing google credentials and  pulling form data from google drives.
"""
from __future__ import print_function
import os
import json
import requests
from datetime import datetime, timezone,timedelta
from dateutil import parser


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = 'creds/token.json' # Auto generated
CREDENTIALS_PATH = 'creds/google_credentials.json' # Manually downloaded from google platform
CONFIG_PATH = 'creds/google_config.json'
AUTHORIZATION_URL = "https://oauth2.googleapis.com/token"

def checkExpired():
    """
    Checks if the token has expired. If it has, deletes the token and returns True.
    Please note that this token is different from google credentials and you should never manually change the token.json.
    """
    if not os.path.exists(TOKEN_PATH):
        return True
    with open(TOKEN_PATH, 'r') as f:
        try:
            creds = json.load(f)
        except json.decoder.JSONDecoderError:
            os.remove(TOKEN_PATH)
            return True
    now = datetime.now(timezone.utc)
    exp_dt = parser.parse(creds['expiry'])
    return exp_dt - now < timedelta(minutes=10)

def refreshToken():
    """
    Refreshes the token if it has expired.
    """
    if not os.path.exists(TOKEN_PATH):
        return None
    
    with open(TOKEN_PATH, 'r') as f:
        creds = json.load(f)
    
    params = {
            "grant_type": "refresh_token",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"]
    }

    if checkExpired():
        try:
            r = requests.post(AUTHORIZATION_URL, data=params)
            r.raise_for_status()
            creds['token'] = r.json()['access_token']
            with open(TOKEN_PATH, 'w') as f:
                json.dump(creds, f)
            return 1
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Error refreshing token: {e}")
            return 0
    else:
        return None


def load_credentials():
    """
    Loads credentials from the token.json file. If the credentials are not valid, creates new credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def load_config():
    """
    Load configuration for Google Drive files.
    """
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH,'r') as f:
            config = json.load(f)
            return config['items']
    else:
        return {
            'maillist': '17GP7PlQYxr1A1_1srrSDpLjCplLztdHWG51XY2qZoVo',
            'sensor_install_data': '15DDTqQkXqD16vCnOBBTz9mPUmVWnKywjxdNWF9N6Gcg'
        }

def pull_sensor_install_data():
    """
    Pulls sensor install data from Google Drive.    
    """
    refreshToken()
    creds = load_credentials()
    
    try:
        service = build('drive', 'v3', credentials=creds)
        items = load_config()
        if not os.path.exists('google_drive'):
            os.mkdir('google_drive')
        print('Pulling sensor install data from google drive...')
        for key, item_id in items.items():
            info = service.files().export(fileId=item_id, mimeType='text/csv').execute()
            with open(f'google_drive/{key}.csv', 'wb') as f:
                f.write(info)

    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    pull_sensor_install_data()
