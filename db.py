# db.py
"""Database setup for the MCP server."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base


# Allow the database URL to be configured via an environment variable.  If none
# is provided, fall back to a local SQLite database for easier testing.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")

# Create the SQLAlchemy engine and session factory.  autocommit/autoflush are
# disabled to mirror typical FastAPI style usage.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they do not already exist."""
    Base.metadata.create_all(engine)
