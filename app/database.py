from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.database_operation import create_database
import os
from dotenv import load_dotenv

load_dotenv()

# Fetch values from the environment
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_URL = os.getenv("ADMIN_URL")

# Create the database if it doesn't exist
create_database(ADMIN_URL, DATABASE_NAME)

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
