from sqlmodel import Field,SQLModel,create_engine

class BankConnection(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    bank_name: str
    access_token: str
class Subscription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    merchant_name: str
    amount: float
    next_billing_date: str
    status: str

postgres_file_name = "database.db"
postgres_url = "postgresql://myuser:mypassword@localhost:5432/mydb"

engine = create_engine(postgres_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()