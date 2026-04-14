"""SQLAlchemy engine ve oturum fabrikasi; transaction / rollback yardimcilari."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import get_database_url


def _engine_kwargs(url: str) -> dict:
    if url.lower().startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # PostgreSQL ve diger sunucular
    return {"pool_pre_ping": True}


_url = get_database_url()
engine = create_engine(_url, **_engine_kwargs(_url), future=True)

SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_flask_session() -> Session:
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


def rollback_flask_session() -> None:
    """Istek oturumunu acikca geri al (DB yazimi basladiktan sonra erken HTTP cevabi verirken)."""
    from flask import g

    s = getattr(g, "sa_session", None)
    if s is not None:
        s.rollback()


@contextmanager
def flask_transaction():
    """Flask istegi oturumu ile tek transaction blogu.

    - Basarili cikista: commit
    - Istisnada: rollback, istisna yeniden firlatilir

    Erken ``return`` ile cikista da commit calisir; yazma yapildiysa ve
    islemi iptal etmek istiyorsaniz once :func:`rollback_flask_session` cagirin.
    """
    session = get_flask_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise


@contextmanager
def session_scope():
    """Script / CLI / migrate: yeni oturum; basarida commit, hatada rollback, her zaman kapat."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
