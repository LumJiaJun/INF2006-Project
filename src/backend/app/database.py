import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Local dev default: SQLite file. In deployment, set DATABASE_URL to a
# managed Postgres instance (e.g. AWS RDS) — see docs/DEPLOYMENT.md.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./staysphere.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,   # scalability: drop dead connections instead of erroring
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
