import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")
db_name = os.getenv("DB_NAME")

URI = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

engine = create_engine(URI, echo=False, pool_size=5, max_overflow=0)

SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=True)
