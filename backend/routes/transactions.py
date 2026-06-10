# routes/transactions.py
import token
import jwt
import requests
import time
import uuid
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from db import engine, Account, Transaction
from sqlmodel import Session, select
import traceback
import json

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()
APP_ID = os.getenv("APP_ID")
KEY_PATH = BASE_DIR / "private_key.pem"

def get_enable_banking_acces_token():
    print("Citit fisierul de cheie privata")
    with open(KEY_PATH, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    time_now = int(time.time())
    payload = {
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": time_now,
        "exp": time_now + 3600,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256',
                       headers={"kid": APP_ID, "typ": "JWT"})
    return token

# Helper nou: Descarcă soldul real pentru fiecare cont de la Enable Banking API
def get_account_balance_api(account_uid: str) -> float:
    try:
        token = get_enable_banking_acces_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"https://api.enablebanking.com/accounts/{account_uid}/balances"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            balances = data.get("balances", [])
            if balances:
                # Extragem primul sold din listă (suportă ambele casing-uri)
                bal_amt = balances[0].get("balance_amount") or balances[0].get("balanceAmount") or {}
                return float(bal_amt.get("amount") or 0.0)
    except Exception as e:
        print(f"[transactions.py] Nu s-a putut descărca balanța pentru contul {account_uid}: {e}")
    return 0.0

def get_transactions():
    print("Intra in get transactions")
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    account_url = "https://api.enablebanking.com/accounts"
    response = requests.get(account_url, headers=headers)
    accounts = response.json().get("accounts", [])
    
    if not accounts:
        return {"error": "No accounts found"}
    
    # Suportă uid sau id
    account_id = accounts[0].get("uid") or accounts[0].get("id")
    print(f"Am luat account id: {account_id}")
    transactions_url = f"https://api.enablebanking.com/accounts/{account_id}/transactions"
    res = requests.get(transactions_url, headers=headers)
    
    return res.json()


def start_revolut_session():
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    now = datetime.now(timezone.utc)
    valid_until = now + timedelta(days=90)
    valid_until_str = valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

    session_data = {
        "access": {
            "valid_until": valid_until_str
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

# 2. Salvare conturi în DB (Actualizat pentru a adăuga balanța reală)
def save_accounts_to_db(accounts_data: list):
    print(f"\n[transactions.py] save_accounts_to_db apelat cu {len(accounts_data)} conturi.")
    try:
        with Session(engine) as session:
            for acc in accounts_data:
                # Extragem ID-ul unic al contului (suportă ambele casing-uri)
                acc_id = acc.get("uid") or acc.get("account_id") or acc.get("id")
                
                if not acc_id:
                    print("[transactions.py] Eroare: Am primit un cont fără ID/uid.")
                    continue

                # Extragem soldul real direct prin API-ul suplimentar de balanță
                balance_value = get_account_balance_api(acc_id)

                # Inserare sau actualizare securizată (Compatibil cu toate versiunile de SQLAlchemy)
                db_account = session.exec(select(Account).where(Account.id == acc_id)).first()
                if not db_account:
                    db_account = Account(
                        id=acc_id,
                        name=acc.get("name") or acc.get("holderName") or "Cont Revolut",
                        currency=acc.get("currency", "RON"),
                        balance=balance_value
                    )
                    session.add(db_account)
                    print(f"[transactions.py] Am salvat contul nou: {acc_id} cu soldul {balance_value} {db_account.currency}")
                else:
                    db_account.name = acc.get("name") or acc.get("holderName") or db_account.name
                    db_account.currency = acc.get("currency", db_account.currency)
                    db_account.balance = balance_value
                    session.add(db_account)
                    print(f"[transactions.py] Am actualizat contul existent: {acc_id} cu soldul {balance_value} {db_account.currency}")

            session.commit()
            print("[transactions.py] Toate conturile au fost salvate cu succes!")
    except Exception as e:
        print("[transactions.py] Eroare critică în save_accounts_to_db:")
        traceback.print_exc()
        raise e

# 3. Salvare tranzacții în DB (Suportă ambele stiluri de naming și previne coliziunile)
def save_transactions_to_db(account_id: str, transactions_data: list):
    print(f"\n[transactions.py] save_transactions_to_db apelat pentru contul {account_id} cu {len(transactions_data)} tranzacții.")
    try:
        with Session(engine) as session:
            saved_count = 0
            for tx in transactions_data:
                # Verifică ID-ul nativ sub ambele tipuri de casing-uri (snake_case sau camelCase)
                tx_id = tx.get("transaction_id") or tx.get("transactionId") or tx.get("entry_reference") or tx.get("entryReference")
                
                # Colectăm date pentru un ID fallback stabil în caz de ID nativ absent
                raw_date = tx.get("booking_date_time") or tx.get("bookingDateTime") or tx.get("booking_date") or tx.get("bookingDate") or tx.get("value_date_time") or tx.get("valueDateTime") or ""
                amount_obj = tx.get("transaction_amount") or tx.get("transactionAmount") or tx.get("instructed_amount") or tx.get("instructedAmount") or {}
                amount_str = amount_obj.get("amount") or tx.get("amount") or "0"
                
                # Extragem comerciantul corect sub ambele casing-uri
                merchant_name = tx.get("creditor_name") or tx.get("creditorName") or (tx.get("creditor") or {}).get("name")
                if not merchant_name:
                    rem_info = tx.get("remittance_information") or tx.get("remittanceInformation")
                    if rem_info and isinstance(rem_info, list) and len(rem_info) > 0:
                        merchant_name = rem_info[0]
                if not merchant_name:
                    merchant_name = tx.get("remittance_information_unstructured") or tx.get("remittanceInformationUnstructured") or "Necunoscut"
                
                # Generăm o cheie unică stabilă pentru a împiedica coliziunile și a salva toate tranzacțiile
                if not tx_id:
                    tx_id = f"{account_id}-{raw_date}-{amount_str}-{merchant_name}".replace(" ", "_")
                
                # Verificăm dacă există deja tranzacția
                statement = select(Transaction).where(Transaction.transaction_id == tx_id)
                existing = session.exec(statement).first()
                if existing:
                    continue # Sărim peste dubluri
                
                # Extragem valoarea numerică a sumei
                amount_val = 0.0
                try:
                    amount_val = float(amount_str)
                except Exception:
                    pass
                
                currency_val = amount_obj.get("currency") or tx.get("currency") or "RON"
                
                # Aplicăm creditDebitIndicator sub ambele casing-uri
                # DBIT = Debit (Minus) | CRDT = Credit (Plus)
                credit_debit = tx.get("credit_debit_indicator") or tx.get("creditDebitIndicator")
                if credit_debit == "DBIT" or credit_debit == "Debit":
                    amount_val = -abs(amount_val)
                elif credit_debit == "CRDT" or credit_debit == "Credit":
                    amount_val = abs(amount_val)
                
                try:
                    booking_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else datetime.now()
                except Exception:
                    booking_date = datetime.now()
                
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
                saved_count += 1
                
            session.commit()
            print(f"[transactions.py] S-au salvat {saved_count} tranzacții noi în baza de date locală SQLite.")
    except Exception as e:
        print(f"[transactions.py] Eroare critică în save_transactions_to_db pentru contul {account_id}:")
        traceback.print_exc()
        raise e

def get_all_accounts():
    token = get_enable_banking_acces_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get("https://api.enablebanking.com/accounts", headers=headers)
    return response.json()