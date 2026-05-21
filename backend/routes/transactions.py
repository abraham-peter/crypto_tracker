import token

import jwt
import requests
import time
import uuid
from datetime import datetime,timedelta,timezone
import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()
APP_ID=os.getenv("APP_ID")
KEY_PATH=BASE_DIR / "private_key.pem"
# KEY_PATH=os.getenv("KEY_PATH")

def get_enable_banking_acces_token():
    print("Citit fisierul de cheie privata")
    with open(KEY_PATH,'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    time_now = int(time.time())
    payload={
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": time_now,
        "exp": time_now + 3600,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256',
                       headers={"kid": APP_ID,"typ": "JWT"})
    return token
def get_transactions():
    print("Intra in get transactions")
    token = get_enable_banking_acces_token()
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    #Iau lista de account-uri(De exemplu Revolut(Ron/Euro),BT,)
    account_url="https://api.enablebanking.com/accounts"
    response = requests.get(account_url, headers=headers)
    accounts = response.json().get("accounts", [])
    
    if not accounts:
        return {"error": "No accounts found"}
    
    #incerc sa iau tranzactiile de la primul account din lista
    account_id = accounts[0].get("id")
    print(f"Am luat account id: {account_id}")
    transactions_url = f"https://api.enablebanking.com/accounts/{account_id}/transactions"
    res=requests.get(transactions_url, headers=headers)
    
    return res.json()
from datetime import datetime, timedelta, timezone

def start_revolut_session():
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # FIX: Dynamically calculate 90 days from today
    now = datetime.now(timezone.utc)
    valid_until = now + timedelta(days=90)
    # Formats it exactly as 'YYYY-MM-DDTHH:MM:SSZ'
    valid_until_str = valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

    session_data = {
        "access": {
            "valid_until": valid_until_str # Safely under the 180-day limit!
        },
        "aspsp": {
            "name": "Revolut", 
            "country": "RO"
        },
        "redirect_url": "https://localhost:5173/", 
        "state": str(uuid.uuid4()),
        "psu_type": "personal"
    }

    response = requests.post(
        "https://api.enablebanking.com/auth", 
        headers=headers, 
        json=session_data
    )
    
    return response.json()

def finalize_session(auth_code: str):
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Send the authorization code to /sessions
    payload = {
        "code": auth_code
    }

    response = requests.post(
        "https://api.enablebanking.com/sessions",
        headers=headers,
        json=payload
    )
    
    return response.json()

def get_account_transactions(account_uid: str):
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Endpoint to fetch transactions for a specific account UID
    transactions_url = f"https://api.enablebanking.com/accounts/{account_uid}/transactions"
    
    # You can optionaly filter by date, e.g. f"{transactions_url}?date_from=2024-01-01"
    response = requests.get(transactions_url, headers=headers)
    
    return response.json()