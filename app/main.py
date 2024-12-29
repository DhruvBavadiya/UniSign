from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.routes import router as registration_router

from app.database import engine, get_db
from app.models import Base, Registration

app = FastAPI()

app.include_router(registration_router)

Base.metadata.create_all(bind=engine)
