from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from db.models import User, UserBolge


class UserRepository:
    def __init__(self, session: Session):
        self._s = session

    def get_by_username(self, username: str) -> Optional[User]:
        return self._s.scalar(select(User).where(User.username == username))

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._s.get(User, user_id)

    def get_id_by_username(self, username: str) -> Optional[int]:
        u = self.get_by_username(username)
        return u.id if u else None

    def create(self, username: str, password_hash: str, role: str = "normal") -> User:
        u = User(username=username, password_hash=password_hash, role=role)
        self._s.add(u)
        self._s.flush()
        return u

    def username_exists(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def get_role(self, user_id: int) -> Optional[str]:
        u = self.get_by_id(user_id)
        return (u.role or "normal") if u else None

    def list_bolge_kodlari(self, user_id: int) -> List[str]:
        rows = self._s.scalars(
            select(UserBolge.bolge_kodu).where(UserBolge.user_id == user_id)
        ).all()
        return list(rows)

    def update_role(self, username: str, role: str) -> bool:
        u = self.get_by_username(username)
        if not u:
            return False
        u.role = role
        return True

    def list_users_with_bolgeler(self) -> List[Dict[str, Any]]:
        users = self._s.scalars(select(User).order_by(User.id)).all()
        out: List[Dict[str, Any]] = []
        for u in users:
            bolgeler = self.list_bolge_kodlari(u.id)
            out.append(
                {
                    "username": u.username,
                    "role": u.role or "normal",
                    "default_bolge_kodu": u.default_bolge_kodu,
                    "bolge_kodlari": bolgeler,
                }
            )
        return out

    def add_user_bolge(self, user_id: int, bolge_kodu: str) -> Tuple[bool, bool]:
        """(eklendi_mi, zaten_vardi_mi)."""
        exists = self._s.scalar(
            select(UserBolge.id).where(
                UserBolge.user_id == user_id, UserBolge.bolge_kodu == bolge_kodu
            )
        )
        if exists is not None:
            return False, True
        self._s.add(UserBolge(user_id=user_id, bolge_kodu=bolge_kodu))
        return True, False

    def remove_user_bolge(self, user_id: int, bolge_kodu: str) -> int:
        r = self._s.execute(
            delete(UserBolge).where(
                UserBolge.user_id == user_id, UserBolge.bolge_kodu == bolge_kodu
            )
        )
        return r.rowcount or 0

    def user_info_dict(self, username: str) -> Optional[Dict[str, Any]]:
        u = self.get_by_username(username)
        if not u:
            return None
        return {
            "id": u.id,
            "username": u.username,
            "role": u.role or "normal",
            "default_bolge_kodu": u.default_bolge_kodu,
            "bolge_kodlari": self.list_bolge_kodlari(u.id),
        }
