import os
from sqlmodel import create_engine, Session

# Default: SQLite in the working directory
# Override with DATABASE_URL env var for PostgreSQL multi-terminal setups
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./opentill.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session
