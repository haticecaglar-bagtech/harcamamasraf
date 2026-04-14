"""Semayi olusturur ve referans tohumlarini uygular (migrate_db eslenigi)."""

from __future__ import annotations

import os

from db.models import Base
from db.seed import run_reference_seeds
from db.session import engine, session_scope

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def migrate_db(*, run_seeds: bool = True) -> None:
    """SQLite: create_all. PostgreSQL: Alembic upgrade head. Sonra istenirse referans tohumlari."""
    from alembic import command
    from alembic.config import Config

    from config import get_database_url, is_postgresql_database

    try:
        if is_postgresql_database():
            ini_path = os.path.join(_PROJECT_ROOT, "alembic.ini")
            cfg = Config(ini_path)
            cfg.set_main_option("sqlalchemy.url", get_database_url())
            command.upgrade(cfg, "head")
            print("✅ PostgreSQL şema migrasyonu (Alembic) tamamlandı.")
        else:
            Base.metadata.create_all(bind=engine)
            print("✅ SQLite tabloları oluşturuldu (SQLAlchemy).")
    except Exception as e:
        print(f"❌ Migration (şema) hatası: {e}")
        import traceback

        traceback.print_exc()
        return

    if not run_seeds:
        return

    try:
        with session_scope() as session:
            run_reference_seeds(session)
        print("✅ Referans tohumları uygulandı.")
    except Exception as e:
        print(f"❌ Tohum hatası: {e}")
        import traceback

        traceback.print_exc()
