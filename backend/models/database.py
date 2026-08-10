from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

# PostgreSQL engine — works with Supabase, Neon, Railway Postgres, etc.
# connection_args not needed for PostgreSQL (check_same_thread is SQLite-only)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # reconnects if the connection drops
    pool_size=5,             # keep 5 connections ready
    max_overflow=10,         # allow up to 10 extra under load
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
