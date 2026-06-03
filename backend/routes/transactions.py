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
from db import engine, Account, Transaction
from sqlmodel import Session, select
from datetime import datetime


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


def start_revolut_session():
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    #Calculez data de 3 luni
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

    #Endpoint pentru un itiliztor anumit
    transactions_url = f"https://api.enablebanking.com/accounts/{account_uid}/transactions"
    
    response = requests.get(transactions_url, headers=headers)
    
    return response.json()

def categorize_merchant(merchant_name: str) -> str:
    name = merchant_name.lower()
    
    subscriptions = ['netflix', 'spotify', 'youtube', 'google', 'apple', 'amazon', 'adobe', 'microsoft', 'github', 'openai', 'chatgpt', 'patreon', 'hbo', 'disney', 'scribd', 'badoo', 'tinder']
    groceries = ['lidl', 'carrefour', 'kaufland', 'mega image', 'auchan', 'profi', 'penny', 'billa', 'metro', 'selgros']
    dining_delivery = ['glovo', 'bolt food', 'tazz', 'mcdonald', 'kfc', 'starbucks', 'dristor', 'restaurant', 'pub', 'pizza', 'dodo']
    transport = ['bolt', 'uber', 'cfr', 'wizz', 'omv', 'rompetrol', 'lukoil', 'mol', 'taxis', 'metrorex', 'autobuz', 'autonom']
    utilities = ['enel', 'digi', 'orange', 'vodafone', 'e.on', 'apa nova', 'engie', 'hidroelectrica']
    
    if any(kw in name for kw in subscriptions):
        return "Abonament"
    if any(kw in name for kw in groceries):
        return "Groceries"
    if any(kw in name for kw in dining_delivery):
        return "Mâncare & Restaurant"
    if any(kw in name for kw in transport):
        return "Transport & Auto"
    if any(kw in name for kw in utilities):
        return "Utilități"
    
    return "Altele"

# 2. Salvare conturi în DB
def save_accounts_to_db(accounts_data: list):
    with Session(engine) as session:
        for acc in accounts_data:
            acc_id = acc.get("id") or acc.get("accountId")
            if not acc_id:
                continue
                
            balance_val = 0.0
            if acc.get("balances"):
                balance_val = float(acc["balances"][0].get("balanceAmount", {}).get("amount", 0.0))
            
            existing = session.get(Account, acc_id)
            if existing:
                existing.balance = balance_val
                existing.currency = acc.get("currency", "RON")
                existing.name = acc.get("name", "Revolut Account")
            else:
                new_acc = Account(
                    id=acc_id,
                    name=acc.get("name", "Revolut Account"),
                    currency=acc.get("currency", "RON"),
                    balance=balance_val
                )
                session.add(new_acc)
        session.commit()

# 3. Salvare tranzacții în DB (fără a duplica înregistrările existente)
def save_transactions_to_db(account_id: str, transactions_data: list):
    with Session(engine) as session:
        for tx in transactions_data:
            tx_id = tx.get("transactionId") or tx.get("entryReference")
            if not tx_id:
                # Fallback pentru a crea o cheie unică stabilă dacă Revolut nu returnează id direct
                raw_date = tx.get("bookingDateTime") or tx.get("bookingDate") or ""
                amount_fallback = tx.get("transactionAmount", {}).get("amount", "0")
                tx_id = f"{account_id}-{raw_date}-{amount_fallback}"
            
            # Verificăm dacă tranzacția există deja
            statement = select(Transaction).where(Transaction.transaction_id == tx_id)
            existing = session.exec(statement).first()
            if existing:
                continue # Trecem peste ea dacă există deja în baza de date
            
            amount_obj = tx.get("transactionAmount", {})
            amount_val = float(amount_obj.get("amount", 0.0))
            currency_val = amount_obj.get("currency", "RON")
            
            raw_date = tx.get("bookingDateTime") or tx.get("bookingDate")
            try:
                # Convertim stringul ISO format în obiect datetime Python
                booking_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else datetime.now()
            except Exception:
                booking_date = datetime.now()
            
            # Determină numele comerciantului din diverse câmpuri posibile din API
            merchant_name = tx.get("creditorName") or (tx.get("creditor") or {}).get("name")
            if not merchant_name and tx.get("remittanceInformation"):
                merchant_name = tx["remittanceInformation"][0]
            if not merchant_name:
                merchant_name = tx.get("remittanceInformationUnstructured") or "Necunoscut"
            
            category_val = categorize_merchant(merchant_name)
            
            new_tx = Transaction(
                transaction_id=tx_id,
                account_id=account_id,
                booking_date=booking_date,
                merchant=merchant_name,
                amount=amount_val,
                currency=currency_val,
                category=category_val
            )
            session.add(new_tx)
        session.commit()

def get_all_accounts():
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get("https://api.enablebanking.com/accounts", headers=headers)
    return response.json()