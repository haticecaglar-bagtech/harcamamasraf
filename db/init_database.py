"""Semayi olusturur ve referans tohumlarini uygular (migrate_db eslenigi)."""

from db.models import Base
from db.seed import run_reference_seeds
from db.session import engine, session_scope


def migrate_db() -> None:
    """Tablolari yoksa olusturur; bolge/kaynak/stage/operasyon tohumlarini ekler."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"❌ Migration (engine) hatası: {e}")
        import traceback

        traceback.print_exc()
        return

    try:
        with session_scope() as session:
            run_reference_seeds(session)
        print("✅ SQLite Migration başarıyla tamamlandı! (SQLAlchemy)")
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        import traceback

        traceback.print_exc()
