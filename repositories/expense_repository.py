from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.models import Expense, User, UserBolge
from repositories._dates import format_tarih_for_json, parse_date

_EXPENSE_MUTABLE = frozenset(
    {
        "tarih",
        "bolge_kodu",
        "kaynak_tipi",
        "stage",
        "stage_operasyon",
        "no_su",
        "kimden_alindigi",
        "aciklama",
        "tutar",
    }
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


class ExpenseRepository:
    def __init__(self, session: Session):
        self._s = session

    def save(
        self,
        user_id: int,
        tarih: str,
        bolge_kodu: Optional[str],
        kaynak_tipi: Optional[str],
        stage: Optional[str],
        stage_operasyon: Optional[str],
        no_su: Optional[str],
        kimden_alindigi: Optional[str],
        aciklama: Optional[str],
        tutar: float,
    ) -> int:
        e = Expense(
            user_id=user_id,
            tarih=parse_date(tarih),
            bolge_kodu=bolge_kodu,
            kaynak_tipi=kaynak_tipi,
            stage=stage,
            stage_operasyon=stage_operasyon,
            no_su=no_su,
            kimden_alindigi=kimden_alindigi,
            aciklama=aciklama,
            tutar=tutar,
        )
        self._s.add(e)
        self._s.flush()
        return e.id

    def list_filtered(
        self,
        user_id: Optional[int],
        bolge_kodu: Optional[str],
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

        stmt = select(Expense)
        conditions = []
        if role == "normal" and user_bolgeler:
            variants = _normalized_bolge_variants(user_bolgeler)
            conditions.append(Expense.bolge_kodu.in_(variants))
        if bolge_kodu:
            bn = _normalize_bolge(bolge_kodu)
            conditions.append(
                (Expense.bolge_kodu == bn) | (Expense.bolge_kodu == bn + ".")
            )
        if stage_kodu:
            conditions.append(Expense.stage == stage_kodu)
        for c in conditions:
            stmt = stmt.where(c)
        stmt = stmt.order_by(Expense.tarih.desc())
        rows = self._s.scalars(stmt).all()

        expenses: List[Dict[str, Any]] = []
        for row in rows:
            tarih_value = row.tarih
            if tarih_value:
                tarih = format_tarih_for_json(tarih_value)
            else:
                tarih = None
            expenses.append(
                {
                    "id": row.id,
                    "tarih": tarih,
                    "bolge_kodu": row.bolge_kodu,
                    "kaynak_tipi": row.kaynak_tipi,
                    "stage": row.stage,
                    "stage_operasyon": row.stage_operasyon,
                    "no_su": row.no_su,
                    "kimden_alindigi": row.kimden_alindigi,
                    "aciklama": row.aciklama,
                    "tutar": float(row.tutar) if row.tutar is not None else 0.0,
                }
            )
        return expenses

    def clear_for_user(self, user_id: int) -> None:
        self._s.execute(delete(Expense).where(Expense.user_id == user_id))

    def clear_all(self) -> None:
        self._s.execute(delete(Expense))

    def get_by_id(self, expense_id: int) -> Optional[Expense]:
        return self._s.get(Expense, expense_id)

    def update_whitelisted(self, expense_id: int, data: Dict[str, Any]) -> bool:
        e = self.get_by_id(expense_id)
        if not e:
            return False
        changed = False
        for field in _EXPENSE_MUTABLE:
            if field not in data:
                continue
            val = data[field]
            if field == "tutar":
                if isinstance(val, str):
                    val = float(val.replace("₺", "").replace(",", ".").strip())
                else:
                    val = float(val)
                setattr(e, field, val)
            elif field == "tarih":
                setattr(e, field, parse_date(val))
            else:
                setattr(e, field, val)
            changed = True
        if changed:
            e.updated_at = datetime.now()
        return changed

    def delete_by_id(self, expense_id: int) -> bool:
        e = self.get_by_id(expense_id)
        if not e:
            return False
        self._s.delete(e)
        return True
