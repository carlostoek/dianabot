from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
from .settings import settings
import os

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    try:
        engine = create_engine(os.getenv("DATABASE_URL"))
        global Session
        Session = scoped_session(sessionmaker(bind=engine))
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
   