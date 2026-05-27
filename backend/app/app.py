from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
# from db import create_db_and_tables
from routes.transactions import get_transactions
from routes.transactions import start_revolut_session
from routes.transactions import get_enable_banking_acces_token
from routes.transactions import finalize_session
from routes.transactions import get_account_transactions
import requests



app = FastAPI(
    title="CostWatch API",
    description="Peter e cel mai tare OM",
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

# @app.get("/transactions")
# async def transactions(request:Request):
#     return get_transactions()

@app.get("/revolut-session")
async def revolut_session(request:Request):
    return start_revolut_session()

@app.get("/available-banks")
async def get_banks():
    token = get_enable_banking_acces_token() # Your token generator
    headers = {
        "Authorization": f"Bearer {token}",
    }
    # Fetch all banks registered in Romania (RO)
    response = requests.get("https://api.enablebanking.com/aspsps?country=RO", headers=headers)
    return response.json()
@app.get("/finalize")
async def finalize(code: str):
    return finalize_session(code)

@app.get("/transactions/{account_uid}")
async def transactions(account_uid: str):
    return get_account_transactions(account_uid)