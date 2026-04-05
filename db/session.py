"""SQLAlchemy engine ve oturum fabrikasi."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import get_database_path


def _sqlite_url() -> str:
    path = os.path.abspath(get_database_path())
    return "sqlite:///" + path.replace("\\", "/")


engine = create_engine(
    _sqlite_url(),
    connect_args={"check_same_thread": False},
    future=True,
)

SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_flask_session():
    """Flask istegi basina tek Session (g uzerinde)."""
    from flask import g

    if not hasattr(g, "sa_session") or g.sa_session is None:
        g.sa_session = SessionFactory()
    return g.sa_session


def close_flask_session() -> None:
    from flask import g

    s = getattr(g, "sa_session", None)
    if s is not None:
        s.close()
        g.sa_session = None
