import os
import json
import requests
from datetime import datetime, timezone,timedelta
from dateutil import parser

""" 
    Only the credentials.json matters. It is downloaded from client authorization.
    If the auth expires, create new key in service account. 
"""

def checkExpired():
    if not os.path.exists('token.json'):
        return True
    with open('token.json', 'r') as f:
        try:
            creds = json.load(f)
        except json.decoder.JSONDecoderError:
            os.remove('token.json')
            return True
    now = datetime.now(timezone.utc)
    exp_dt = parser.parse(creds['expiry'])
    diff = exp_dt-now
    if diff < timedelta(minutes=10):
        return True
    return False

def refreshToken():
    if not os.path.exists('token.json'):
        return None

    with open('token.json', 'r') as f:
        creds = json.load(f)
        
    params = {
            "grant_type": "refresh_token",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"]
    }
    
    authorization_url = "https://oauth2.googleapis.com/token"
    if checkExpired():
        # expired
        try:
            r = requests.post(authorization_url, data=params)
            r.raise_for_status()
            creds['token'] = r.json()['access_token']
            with open('token.json', 'w') as f:
                json.dump(creds, f)
            return 1
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Error refreshing token: {e}")
            return 0
    else:
        return None

if __name__=="__main__":
    refreshToken()