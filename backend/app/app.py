from fastapi import FastAPI,Request,Query
from fastapi.middleware.cors import CORSMiddleware
# from db import create_db_and_tables
from routes.transactions import get_transactions,start_revolut_session,get_enable_banking_acces_token,finalize_session,get_account_transactions,save_accounts_to_db,save_transactions_to_db,get_all_accounts
from typing import Optional
from db import create_db_and_tables, Account, Transaction,engine
import requests
from sqlmodel import Session, desc, select, SQLModel, create_engine,col




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


# Creează tabelele automat la pornirea serverului FastAPI
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/revolut-session")
async def revolut_session(request: Request):
    return start_revolut_session()

@app.get("/finalize")
async def finalize(code: str):
    # Finalizează sesiunea cu Revolut
    session_data = finalize_session(code)
    # După ce am finalizat sesiunea cu succes, facem prima sincronizare automată a conturilor
    try:
        remote_accounts = get_all_accounts()
        if "accounts" in remote_accounts:
            save_accounts_to_db(remote_accounts["accounts"])
    except Exception as e:
        print(f"Eroare sincronizare automată inițială: {e}")
    return session_data

# Sincronizare manuală conturi și tranzacții din API în DB
@app.post("/sync")
async def sync_data():
    try:
        # 1. Descarcă conturile
        remote_accounts = get_all_accounts()
        accounts_list = remote_accounts.get("accounts", [])
        save_accounts_to_db(accounts_list)
        
        # 2. Descarcă tranzacțiile pentru fiecare cont identificat
        for acc in accounts_list:
            acc_id = acc.get("id") or acc.get("accountId")
            if acc_id:
                remote_tx = get_account_transactions(acc_id)
                tx_list = remote_tx.get("transactions", [])
                save_transactions_to_db(acc_id, tx_list)
                
        return {"status": "success", "message": f"Datele au fost sincronizate cu succes. Am găsit {len(accounts_list)} conturi."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Listează conturile direct din Baza de Date locală
@app.get("/accounts")
async def get_db_accounts():
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return {"accounts": accounts}

# Obține tranzacțiile direct din baza de date, cu suport pentru căutare și filtrare direct în query-ul SQL
@app.get("/transactions/{account_uid}")
async def get_db_transactions(
    account_uid: str,
    search: Optional[str] = Query(None, description="Căutare după numele comerciantului"),
    category: Optional[str] = Query(None, description="Filtrare după categorie")
):
    with Session(engine) as session:
        statement = select(Transaction).where(Transaction.account_id == account_uid)
        
        # Filtru căutare nume folosind col() ca Pylance să înțeleagă funcția .ilike()
        if search:
            statement = statement.where(col(Transaction.merchant).ilike(f"%{search}%"))
            
        # Filtru categorie
        if category:
            statement = statement.where(Transaction.category == category)
            
        # Sortăm în ordine invers cronologică folosind funcția desc()
        statement = statement.order_by(desc(Transaction.booking_date))
        transactions = session.exec(statement).all()
        
        return {"transactions": transactions}