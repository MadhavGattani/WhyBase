# server/api/db.py
import os
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

Base = declarative_base()
engine = None
SessionLocal = None


class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())


def init_db(db_url):
    global engine, SessionLocal
    if not db_url:
        print("[DB] No DATABASE_URL provided, skipping DB init.")
        return
    try:
        engine = create_engine(db_url)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("[DB] Connected and initialized successfully.")
    except OperationalError as e:
        print(f"[DB] Could not connect to database: {e}")
        engine = None
        SessionLocal = None


def get_session():
    if not SessionLocal:
        print("[DB] No database session available.")
        return None
    return SessionLocal()
