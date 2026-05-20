from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from db import create_db_and_tables




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
create_db_and_tables()
