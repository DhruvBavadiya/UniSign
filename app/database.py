from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.database_operation import create_database

DATABASE_NAME = "user_db"
DATABASE_URL = f"postgresql://postgres:test@localhost:5432/{DATABASE_NAME}"
ADMIN_URL = "postgresql://postgres:test@localhost:5432/postgres"

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
