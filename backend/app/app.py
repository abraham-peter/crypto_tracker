from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
# from db import create_db_and_tables
from routes.transactions import get_transactions,start_revolut_session,get_enable_banking_acces_token,finalize_session,get_all_accounts,get_account_transactions
import requests



app = FastAPI(
    title="CostWatch API",
    description="Merge?Habar nu am",
)
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5173",
    
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)
# create_db_and_tables()


@app.get("/revolut-session")
async def revolut_session(request:Request):
    return start_revolut_session()

@app.get("/available-banks")
async def get_banks():
    token = get_enable_banking_acces_token() # Genratorul meu de tokens
    headers = {
        "Authorization": f"Bearer {token}",
    }
    # Iau Toate Bancile din Romania
    response = requests.get("https://api.enablebanking.com/aspsps?country=RO", headers=headers)
    return response.json()
@app.get("/finalize")
async def finalize(code: str):
    return finalize_session(code)

@app.get("/accounts")
async def accounts():
    return get_all_accounts

@app.get("/transactions/{account_uid}")
async def transactions_account(account_uid: str):
    return get_account_transactions(account_uid)