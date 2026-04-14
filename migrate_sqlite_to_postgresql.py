"""
SQLite dosyasindaki verileri PostgreSQL'e aktarir.

Oncelikle hedef PostgreSQL icin bos bir veritabani ve .env icinde DATABASE_URL tanimlayin.
Kaynak: DATABASE_PATH / SQLITE_PATH veya --sqlite ile belirtilen .db dosyasi.

Kullanim:
  set DATABASE_URL=postgresql+psycopg2://kullanici:sifre@localhost:5432/veritabani
  python migrate_sqlite_to_postgresql.py

  python migrate_sqlite_to_postgresql.py --database-url postgresql+psycopg2://...
  python migrate_sqlite_to_postgresql.py --sqlite D:\\yol\\harcama_masraf.db
"""

from __future__ import annotations

import argparse
import os
import sys


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SQLite -> PostgreSQL veri aktarimi")
    p.add_argument(
        "--sqlite",
        help="Kaynak SQLite dosyasi (yoksa DATABASE_PATH / SQLITE_PATH / varsayilan kok)",
    )
    p.add_argument(
        "--database-url",
        dest="database_url",
        help="Hedef PostgreSQL SQLAlchemy URLi (os.environ DATABASE_URL uzerine yazar)",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url.strip()

    from sqlalchemy import create_engine, select, text
    from sqlalchemy.orm import class_mapper, sessionmaker

    from config import get_database_path, get_database_url, is_postgresql_database, sanitize_database_url
    from db.init_database import migrate_db
    from db.models import (
        BirimUcret,
        BolgeKod,
        Expense,
        HarcamaTalep,
        HarcamaTalepManuelDegisiklik,
        KaynakTipi,
        Masraf,
        Operasyon,
        Stage,
        StageOperasyon,
        User,
        UserBolge,
    )

    target = get_database_url()
    if not is_postgresql_database():
        print("Hedef DATABASE_URL PostgreSQL olmali (postgresql+psycopg2://...).")
        return 1

    sqlite_path = os.path.abspath(args.sqlite or get_database_path())
    if not os.path.isfile(sqlite_path):
        print(f"Kaynak SQLite dosyasi bulunamadi: {sqlite_path}")
        return 1

    sqlite_url = "sqlite:///" + sqlite_path.replace("\\", "/")
    print(f"Kaynak: {sqlite_path}")
    print(f"Hedef:  {sanitize_database_url(target)}")

    src_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    dst_engine = create_engine(target, pool_pre_ping=True)
    SrcSession = sessionmaker(bind=src_engine, autocommit=False, autoflush=False, future=True)
    DstSession = sessionmaker(bind=dst_engine, autocommit=False, autoflush=False, future=True)

    print("Sema (Alembic, tohum yok) uygulaniyor...")
    migrate_db(run_seeds=False)

    copy_order = [
        BolgeKod,
        KaynakTipi,
        Stage,
        StageOperasyon,
        Operasyon,
        BirimUcret,
        User,
        UserBolge,
        HarcamaTalep,
        HarcamaTalepManuelDegisiklik,
        Masraf,
        Expense,
    ]

    def row_mappings(session, model_cls):
        rows = session.execute(select(model_cls)).scalars().all()
        mapper = class_mapper(model_cls)
        out = []
        for obj in rows:
            d = {prop.key: getattr(obj, prop.key) for prop in mapper.column_attrs}
            out.append(d)
        return out

    src = SrcSession()
    dst = DstSession()
    try:
        for model_cls in copy_order:
            tab = model_cls.__tablename__
            mappings = row_mappings(src, model_cls)
            if not mappings:
                print(f"  — {tab}: bos, atlandi")
                continue
            dst.bulk_insert_mappings(model_cls, mappings)
            dst.commit()
            print(f"  ✓ {tab}: {len(mappings)} satir")
    except Exception as e:
        dst.rollback()
        print(f"Veri aktarim hatasi: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        src.close()
        dst.close()

    # SERIAL sayaclarini MAX(id) ile hizala
    serial_tables = [
        ("users", "id"),
        ("user_bolgeler", "id"),
        ("operasyonlar", "id"),
        ("birim_ucretler", "id"),
        ("harcama_talep", "id"),
        ("harcama_talep_manuel_degisiklikler", "id"),
        ("masraf", "id"),
        ("expenses", "id"),
    ]
    try:
        with dst_engine.begin() as conn:
            for table, col in serial_tables:
                q = (
                    f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
                    f"COALESCE((SELECT MAX({col}) FROM {table}), 1), true)"
                )
                conn.execute(text(q))
        print("PostgreSQL sequence degerleri guncellendi.")
    except Exception as e:
        print(f"UYARI: sequence guncelleme atlandi: {e}")

    print("Tamamlandi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
</think>
migrate_sqlite_to_postgresql.py dosyasındaki sequence sıfırlama bölümünü düzeltiyorum.

<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
StrReplace