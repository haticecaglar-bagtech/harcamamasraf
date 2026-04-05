from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from db.models import HarcamaTalep, HarcamaTalepManuelDegisiklik, User, UserBolge
from repositories._dates import format_tarih_for_json, parse_date

_UPDATE_FIELDS = (
    "bolge_kodu",
    "kaynak_tipi_kodu",
    "stage_kodu",
    "stage_operasyon_kodu",
    "safha",
    "harcama_kalemi",
    "birim",
    "miktar",
    "birim_ucret",
    "toplam",
    "aciklama",
)


def _normalize_bolge(bolge: str) -> str:
    bolge_normalized = str(bolge).strip()
    if bolge_normalized.endswith("."):
        bolge_normalized = bolge_normalized[:-1]
    return bolge_normalized


def _normalized_bolge_variants(user_bolgeler: List[str]) -> List[str]:
    out: List[str] = []
    for bolge in user_bolgeler:
        bn = _normalize_bolge(bolge)
        out.append(bn)
        out.append(bn + ".")
    return out


def _maybe_float(x: Any) -> Optional[float]:
    if x is None or x == "":
        return None
    return float(x)


def harcama_to_dict(h: HarcamaTalep) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in (
        "id",
        "no",
        "tarih",
        "bolge_kodu",
        "kaynak_tipi_kodu",
        "stage_kodu",
        "stage_operasyon_kodu",
        "safha",
        "harcama_kalemi",
        "birim",
        "miktar",
        "birim_ucret",
        "toplam",
        "aciklama",
        "is_manuel",
        "user_id",
        "created_at",
        "updated_at",
    ):
        v = getattr(h, key, None)
        if key == "tarih":
            out[key] = format_tarih_for_json(v) if v is not None else None
        elif key in ("created_at", "updated_at") and v is not None:
            out[key] = v.isoformat(sep=" ") if hasattr(v, "isoformat") else str(v)
        else:
            out[key] = v
    return out


class HarcamaRepository:
    def __init__(self, session: Session):
        self._s = session

    def next_no(self) -> int:
        m = self._s.scalar(select(func.max(HarcamaTalep.no)))
        return (m or 0) + 1

    def save_from_payload(self, data: Dict[str, Any]) -> int:
        no = self.next_no()
        h = HarcamaTalep(
            no=no,
            tarih=parse_date(data.get("tarih")),
            bolge_kodu=data.get("bolge_kodu"),
            kaynak_tipi_kodu=data.get("kaynak_tipi_kodu"),
            stage_kodu=data.get("stage_kodu"),
            stage_operasyon_kodu=data.get("stage_operasyon_kodu"),
            safha=data.get("safha"),
            harcama_kalemi=data.get("harcama_kalemi"),
            birim=data.get("birim"),
            miktar=_maybe_float(data.get("miktar")),
            birim_ucret=_maybe_float(data.get("birim_ucret")),
            toplam=_maybe_float(data.get("toplam")),
            aciklama=data.get("aciklama"),
            is_manuel=int(data.get("is_manuel", 0) or 0),
            user_id=data.get("user_id"),
        )
        self._s.add(h)
        self._s.flush()
        return h.id

    def count_all(self) -> int:
        return self._s.scalar(select(func.count()).select_from(HarcamaTalep)) or 0

    def list_filtered(
        self,
        user_id: Optional[int],
        bolge_kodu: Optional[str],
        safha: Optional[str],
        stage_kodu: Optional[str],
    ) -> List[Dict[str, Any]]:
        role = "normal"
        user_bolgeler: List[str] = []
        if user_id is not None:
            u = self._s.get(User, user_id)
            if u:
                role = u.role or "normal"
                if role == "normal":
                    user_bolgeler = [
                        r[0]
                        for r in self._s.execute(
                            select(UserBolge.bolge_kodu).where(UserBolge.user_id == user_id)
                        ).all()
                    ]

        stmt = select(HarcamaTalep)
        if role == "normal" and user_bolgeler:
            stmt = stmt.where(HarcamaTalep.bolge_kodu.in_(_normalized_bolge_variants(user_bolgeler)))
        if bolge_kodu:
            bn = _normalize_bolge(bolge_kodu)
            stmt = stmt.where(
                (HarcamaTalep.bolge_kodu == bn) | (HarcamaTalep.bolge_kodu == bn + ".")
            )
        if safha:
            stmt = stmt.where(HarcamaTalep.safha == safha)
        if stage_kodu:
            stmt = stmt.where(HarcamaTalep.stage_kodu == stage_kodu)
        stmt = stmt.order_by(HarcamaTalep.no, HarcamaTalep.tarih)
        rows = self._s.scalars(stmt).all()
        return [harcama_to_dict(h) for h in rows]

    def get_by_id(self, hid: int) -> Optional[HarcamaTalep]:
        return self._s.get(HarcamaTalep, hid)

    def update_with_audit(self, harcama_talep_id: int, user_id: int, data: Dict[str, Any]) -> bool:
        h = self.get_by_id(harcama_talep_id)
        if not h:
            return False
        old = harcama_to_dict(h)
        changed = False
        for field in _UPDATE_FIELDS:
            if field not in data:
                continue
            new_v = data[field]
            old_v = old.get(field)
            if str(new_v) != str(old_v if old_v is not None else ""):
                changed = True
                if field in ("miktar", "birim_ucret", "toplam"):
                    setattr(h, field, _maybe_float(new_v))
                else:
                    setattr(h, field, new_v)
                self._s.add(
                    HarcamaTalepManuelDegisiklik(
                        harcama_talep_id=harcama_talep_id,
                        user_id=user_id,
                        alan_adi=field,
                        eski_deger=str(old_v if old_v is not None else ""),
                        yeni_deger=str(new_v),
                    )
                )
        if changed:
            h.updated_at = datetime.now()
        return True

    def delete_by_id(self, harcama_talep_id: int) -> None:
        self._s.execute(
            delete(HarcamaTalepManuelDegisiklik).where(
                HarcamaTalepManuelDegisiklik.harcama_talep_id == harcama_talep_id
            )
        )
        self._s.execute(delete(HarcamaTalep).where(HarcamaTalep.id == harcama_talep_id))

    def clear_all(self) -> None:
        self._s.execute(delete(HarcamaTalepManuelDegisiklik))
        self._s.execute(delete(HarcamaTalep))
