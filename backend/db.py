# db.py
from sqlmodel import Field, SQLModel, create_engine
from typing import Optional
from datetime import datetime

class BankConnection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(default=1)  # Default pentru moment
    bank_name: str
    access_token: str

class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(default=1)
    merchant_name: str
    amount: float
    next_billing_date: str
    status: str

class Account(SQLModel, table=True):
    id: str = Field(primary_key=True) 
    name: str
    currency: str
    balance: float


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(index=True, unique=True)  # Pentru a evita duplicatele
    account_id: str = Field(foreign_key="account.id")
    booking_date: datetime
    merchant: str
    amount: float
    currency: str
    category: str  # "Abonament", "Groceries", "Mâncare", "Transport", "Altele"

postgres_url = "sqlite:///database.db"

engine = create_engine(postgres_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()