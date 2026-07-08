"""
Database engine and session management.

Uses SQLite by default (zero-config for local dev/CI). Switch to Postgres
for production by setting DATABASE_URL — no code changes required.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./senus.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """FastAPI dependency: yield a session and always close it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
