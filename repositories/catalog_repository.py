from typing import Dict, List, Optional, Tuple

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from db.models import (
    BirimUcret,
    BolgeKod,
    KaynakTipi,
    Operasyon,
    Stage,
    StageOperasyon,
    UserBolge,
)


class CatalogRepository:
    def __init__(self, session: Session):
        self._s = session

    def bolge_dict_all(self) -> Dict[str, str]:
        rows = self._s.execute(select(BolgeKod.kod, BolgeKod.ad)).all()
        return {r[0]: r[1] for r in rows}

    def bolge_dict_for_user_regions(self, user_id: int) -> Dict[str, str]:
        stmt = (
            select(BolgeKod.kod, BolgeKod.ad)
            .join(UserBolge, UserBolge.bolge_kodu == BolgeKod.kod)
            .where(UserBolge.user_id == user_id)
        )
        rows = self._s.execute(stmt).all()
        return {r[0]: r[1] for r in rows}

    def kaynak_tipleri_dict(self) -> Dict[str, str]:
        rows = self._s.execute(select(KaynakTipi.kod, KaynakTipi.ad)).all()
        return {r[0]: r[1] for r in rows}

    def stages_dict(self) -> Dict[str, str]:
        rows = self._s.execute(select(Stage.kod, Stage.ad)).all()
        return {r[0]: r[1] for r in rows}

    def operasyonlar_nested(self) -> Dict[str, Dict[str, str]]:
        rows = self._s.execute(
            select(Operasyon.stage_kod, Operasyon.operasyon_kod, Operasyon.operasyon_ad)
        ).all()
        result: Dict[str, Dict[str, str]] = {}
        for sk, ok, oa in rows:
            result.setdefault(sk, {})[ok] = oa
        return result

    def stage_operasyonlar_dict(self) -> Dict[str, str]:
        rows = self._s.execute(select(StageOperasyon.kod, StageOperasyon.ad)).all()
        return {r[0]: r[1] for r in rows}

    def birim_ucretler_list(self) -> List[Dict]:
        rows = self._s.execute(select(BirimUcret.birim, BirimUcret.ucret)).all()
        return [{"birim": r[0], "ucret": r[1]} for r in rows]

    def all_reference_payload(self) -> Dict:
        return {
            "bolge_kodlari": self.bolge_dict_all(),
            "kaynak_tipleri": self.kaynak_tipleri_dict(),
            "stages": self.stages_dict(),
            "operasyonlar": self.operasyonlar_nested(),
            "stage_operasyonlar": self.stage_operasyonlar_dict(),
        }

    def add_kaynak_tipi(self, kod: str, ad: str) -> None:
        self._s.add(KaynakTipi(kod=kod, ad=ad))

    def add_stage(self, kod: str, ad: str) -> None:
        self._s.add(Stage(kod=kod, ad=ad))

    def get_stage_ad(self, stage_kod: str) -> Optional[str]:
        return self._s.scalar(select(Stage.ad).where(Stage.kod == stage_kod))

    def find_operasyon(self, stage_kod: str, operasyon_kod: str) -> Optional[str]:
        return self._s.scalar(
            select(Operasyon.operasyon_ad).where(
                Operasyon.stage_kod == stage_kod, Operasyon.operasyon_kod == operasyon_kod
            )
        )

    def get_stage_operasyon_ad(self, kod: str) -> Optional[str]:
        return self._s.scalar(select(StageOperasyon.ad).where(StageOperasyon.kod == kod))

    def add_operasyon_pair(
        self, stage_kod: str, operasyon_kod: str, operasyon_ad: str, kombine_kod: str, kombine_ad: str
    ) -> None:
        self._s.add(
            Operasyon(stage_kod=stage_kod, operasyon_kod=operasyon_kod, operasyon_ad=operasyon_ad)
        )
        so = self._s.get(StageOperasyon, kombine_kod)
        if so is None:
            self._s.add(StageOperasyon(kod=kombine_kod, ad=kombine_ad))
        else:
            so.ad = kombine_ad

    def add_stage_operasyon_row(self, kod: str, ad: str) -> None:
        self._s.add(StageOperasyon(kod=kod, ad=ad))

    def add_birim(self, birim: str, ucret: float) -> None:
        self._s.add(BirimUcret(birim=birim, ucret=ucret))

    def delete_bolge(self, kod: str) -> None:
        self._s.execute(delete(BolgeKod).where(BolgeKod.kod == kod))

    def update_bolge_kod(self, eski_kod: str, yeni_kod: str, ad: str) -> None:
        self._s.execute(
            update(BolgeKod).where(BolgeKod.kod == eski_kod).values(kod=yeni_kod, ad=ad)
        )

    def delete_kaynak_tipi(self, kod: str) -> None:
        self._s.execute(delete(KaynakTipi).where(KaynakTipi.kod == kod))

    def update_kaynak_tipi_kod(self, eski: str, yeni: str, ad: str) -> None:
        self._s.execute(
            update(KaynakTipi).where(KaynakTipi.kod == eski).values(kod=yeni, ad=ad)
        )

    def delete_stage(self, kod: str) -> None:
        self._s.execute(delete(Stage).where(Stage.kod == kod))

    def update_stage_kod(self, eski: str, yeni: str, ad: str) -> None:
        self._s.execute(update(Stage).where(Stage.kod == eski).values(kod=yeni, ad=ad))

    def delete_operasyon(self, stage_kod: str, op_kod: str) -> None:
        self._s.execute(
            delete(Operasyon).where(
                Operasyon.stage_kod == stage_kod, Operasyon.operasyon_kod == op_kod
            )
        )

    def update_operasyon_ad(self, stage_kod: str, op_kod: str, operasyon_ad: str) -> None:
        self._s.execute(
            update(Operasyon)
            .where(Operasyon.stage_kod == stage_kod, Operasyon.operasyon_kod == op_kod)
            .values(operasyon_ad=operasyon_ad)
        )

    def delete_birim_by_name(self, birim: str) -> None:
        self._s.execute(delete(BirimUcret).where(BirimUcret.birim == birim))

    def update_birim_ucret(self, birim: str, ucret: float) -> None:
        self._s.execute(update(BirimUcret).where(BirimUcret.birim == birim).values(ucret=ucret))

    def bolge_exists(self, kod: str) -> bool:
        return self._s.get(BolgeKod, kod) is not None

    def add_bolge(self, kod: str, ad: str) -> None:
        self._s.add(BolgeKod(kod=kod, ad=ad))

    def operasyonlar_for_stage(self, stage_kod: str) -> Dict[str, str]:
        rows = self._s.execute(
            select(Operasyon.operasyon_kod, Operasyon.operasyon_ad).where(
                Operasyon.stage_kod == stage_kod
            )
        ).all()
        return {r[0]: r[1] for r in rows}
