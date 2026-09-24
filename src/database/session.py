"""Engine and session configuration selected by DATABASE_URL."""

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'results' / 'trustguard.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine: Engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def database_is_healthy() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def session_scope() -> Session:
    return SessionLocal()