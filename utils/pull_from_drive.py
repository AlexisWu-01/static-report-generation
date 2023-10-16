"""
Author: Andrew DeCandia, Alexis Wu
Project: Air Partners

Script for setting/ refreshing google credentials and  pulling form data from google drives.
"""
from __future__ import print_function
import os
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account



SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_PATH = 'creds/google_credentials.json' # Manually downloaded from google platform
CONFIG_PATH = 'creds/google_config.json'
AUTHORIZATION_URL = "https://oauth2.googleapis.com/token"

def load_credentials():
    """
    Loads credentials from the google_credentials.json file. If the credentials are not valid, creates new credentials.
    """
    creds = None
    if os.path.exists(CREDENTIALS_PATH):
        creds =  service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
        print(f"credentials loaded: {creds}")
    else:
        # we do not have the google_credentials.json file
        print("No credentials file found. Please download the credentials file from the google platform.")
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
