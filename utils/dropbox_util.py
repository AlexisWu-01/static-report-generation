
# -*- coding: utf-8 -*-
import json
import os
import requests
import sys
import dropbox
import base64
import time

"""
Author: Alexis (Xinyi) Wu
Project: Air Partners
Description: Script for managing credentials and uploading and deleting files from the Air Partners Dropbox account.
"""

class TransferData:
    """
    Class used for transfering data to and from the Air Partners Dropbox account.
    """
    CRED_FILE = 'creds/dropbox_creds.json'
    
    def __init__(self):
        if not os.path.exists(self.CRED_FILE):
            self.setup_dropbox_credentials()
        with open(self.CRED_FILE, 'r') as f:
            data = json.load(f)
        self.dbx = dropbox.Dropbox(
            app_key=data['app_key'],
            app_secret=data['app_secret'],
            oauth2_refresh_token=data['refresh_token']
        )


    def setup_dropbox_credentials(self):
        print("Dropbox credentials not found. Let's set them up.")
        print("Go to https://www.dropbox.com/developers/apps to find the appkey and app secret.")
        app_key = input("Enter the app key: ") 
        app_secret = input("Enter the app secret: ")
        print("\nVisit the following URL to get your AUTHORIZATION_CODE:")
        print(f"https://www.dropbox.com/oauth2/authorize?client_id={app_key}&token_access_type=offline&response_type=code")
        auth_code = input("\nEnter the AUTHORIZATION_CODE here: ")
        token_url = "https://api.dropboxapi.com/oauth2/token"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{app_key}:{app_secret}'.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "code": auth_code,
            "grant_type": "authorization_code"
        }
        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            refresh_token = response.json().get('refresh_token')
            creds = {
                "app_key": app_key,
                "app_secret": app_secret,
                "refresh_token": refresh_token
            }
            with open(self.CRED_FILE, 'w') as f:
                json.dump(creds, f)
            print("Credentials saved successfully!")
            time.sleep(1)
        else:
            print("Failed to fetch refresh token. Please try again.")
            sys.exit(1)


    def upload_file(self, file_from, file_to):
        """
        upload a file to Dropbox using API v2
        """

        with open(file_from, 'rb') as f:
            self.dbx.files_upload(f.read(), file_to)
        
    def delete_file(self, file):
        """
        delete a file from Dropbox using API v2
        """

        self.dbx.files_delete(file)

def upload_zip(year_month):
    """
    Uploads a zip specified by year_month to the Air Partners Dropbox account.
    """
    transferData = TransferData()

    # zip file name
    zip_name = f'{year_month}.zip'

    # create file start and destination locations
    file_from = f'zips/{zip_name}'
    file_to = f'/Report_Zips/{zip_name}'  # The full path to upload the file to, including the file name

    # API v2 --> upload file to Dropbox
    transferData.upload_file(file_from, file_to)
    print('file uploaded')

def delete_zip(year_month_prev):
    """
    If it exists, deletes the zip file of reports from the previous month from
    the Air Partners Dropbox account.
    """
    transferData = TransferData()

    # zip file name
    zip_name = f'{year_month_prev}.zip'

    file_to_delete = f'/Report_Zips/{zip_name}'  # The full path to upload the file to, including the file name

    # API v2 --> upload file to Dropbox
    transferData.delete_file(file_to_delete)


if __name__ == '__main__':
    year_month = sys.argv[1]
    upload_zip(year_month)
