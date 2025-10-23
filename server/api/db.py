# server/api/db.py
import os
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, String, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import OperationalError

Base = declarative_base()
engine = None
SessionLocal = None


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(255), unique=True, nullable=True)  # for future Auth0 / providers
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())

    templates = relationship("Template", back_populates="owner")
    uploads = relationship("UploadedFile", back_populates="owner")


class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # relationship optional
    # user = relationship("User")


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="templates")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False)
    stored_path = Column(String(1024), nullable=False)
    content_type = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="uploads")


def init_db(db_url):
    global engine, SessionLocal
    if not db_url:
        print("[DB] No DATABASE_URL provided, skipping DB init.")
        return
    try:
        # ensure psycopg driver in URL or default to psycopg
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
