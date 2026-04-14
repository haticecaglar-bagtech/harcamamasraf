"""Referans tablolarina ORM ile idempotent tohum (SQLite / PostgreSQL ON CONFLICT DO NOTHING)."""

from sqlalchemy import insert
from sqlalchemy.orm import Session

from db.models import (
    BirimUcret,
    BolgeKod,
    KaynakTipi,
    Operasyon,
    Stage,
    StageOperasyon,
)
from db.seed_data import (
    BIRIM_UCRETLER,
    BOLGE_KODLARI,
    KAYNAK_TIPLERI,
    OPERASYONLAR,
    STAGE_OPERASYONLAR,
    STAGES,
)


def run_reference_seeds(session: Session) -> None:
    for kod, ad in BOLGE_KODLARI:
        stmt = insert(BolgeKod).values(kod=kod, ad=ad).on_conflict_do_nothing(index_elements=[BolgeKod.kod])
        session.execute(stmt)

    for kod, ad in KAYNAK_TIPLERI:
        stmt = insert(KaynakTipi).values(kod=kod, ad=ad).on_conflict_do_nothing(index_elements=[KaynakTipi.kod])
        session.execute(stmt)

    for kod, ad in STAGES:
        stmt = insert(Stage).values(kod=kod, ad=ad).on_conflict_do_nothing(index_elements=[Stage.kod])
        session.execute(stmt)

    for op_id, stage_kod, operasyon_kod, operasyon_ad in OPERASYONLAR:
        stmt = (
            insert(Operasyon)
            .values(id=op_id, stage_kod=stage_kod, operasyon_kod=operasyon_kod, operasyon_ad=operasyon_ad)
            .on_conflict_do_nothing(index_elements=[Operasyon.id])
        )
        session.execute(stmt)

    for kod, ad in STAGE_OPERASYONLAR:
        stmt = (
            insert(StageOperasyon)
            .values(kod=kod, ad=ad)
            .on_conflict_do_nothing(index_elements=[StageOperasyon.kod])
        )
        session.execute(stmt)

    for birim_id, birim, ucret in BIRIM_UCRETLER:
        stmt = (
            insert(BirimUcret)
            .values(id=birim_id, birim=birim, ucret=ucret)
            .on_conflict_do_nothing(index_elements=[BirimUcret.id])
        )
        session.execute(stmt)
