"""Database setup — SQLModel + SQLite."""

from contextlib import contextmanager
from typing import Generator

from sqlmodel import SQLModel, create_engine, Session
from probe.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager returning a database session that auto-commits and closes."""
    with Session(engine) as session:
        yield session
