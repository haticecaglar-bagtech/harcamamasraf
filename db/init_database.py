"""Semayi olusturur ve referans tohumlarini uygular (migrate_db eslenigi)."""

from db.models import Base
from db.seed import run_reference_seeds
from db.session import SessionFactory, engine


def migrate_db() -> None:
    """Tablolari yoksa olusturur; bolge/kaynak/stage/operasyon tohumlarini ekler."""
    try:
        Base.metadata.create_all(bind=engine)
        session = SessionFactory()
        try:
            run_reference_seeds(session)
            session.commit()
            print("✅ SQLite Migration başarıyla tamamlandı! (SQLAlchemy)")
        except Exception as e:
            session.rollback()
            print(f"❌ Migration hatası: {e}")
            import traceback

            traceback.print_exc()
        finally:
            session.close()
    except Exception as e:
        print(f"❌ Migration (engine) hatası: {e}")
        import traceback

        traceback.print_exc()
