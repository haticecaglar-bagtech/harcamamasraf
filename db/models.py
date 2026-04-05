"""SQLAlchemy modelleri — mevcut SQLite şeması ile uyumlu."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="normal")
    default_bolge_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=True
    )


class UserBolge(Base):
    __tablename__ = "user_bolgeler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bolge_kodu: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "bolge_kodu", name="uq_user_bolge"),)


class BolgeKod(Base):
    __tablename__ = "bolge_kodlari"

    kod: Mapped[str] = mapped_column(String(64), primary_key=True)
    ad: Mapped[str] = mapped_column(String(512), nullable=False)


class KaynakTipi(Base):
    __tablename__ = "kaynak_tipleri"

    kod: Mapped[str] = mapped_column(String(64), primary_key=True)
    ad: Mapped[str] = mapped_column(String(512), nullable=False)


class Stage(Base):
    __tablename__ = "stages"

    kod: Mapped[str] = mapped_column(String(64), primary_key=True)
    ad: Mapped[str] = mapped_column(String(512), nullable=False)


class Operasyon(Base):
    __tablename__ = "operasyonlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stage_kod: Mapped[str] = mapped_column(String(64), ForeignKey("stages.kod"), nullable=False)
    operasyon_kod: Mapped[str] = mapped_column(String(64), nullable=False)
    operasyon_ad: Mapped[str] = mapped_column(String(512), nullable=False)

    __table_args__ = (UniqueConstraint("stage_kod", "operasyon_kod", name="uq_stage_operasyon"),)


class StageOperasyon(Base):
    __tablename__ = "stage_operasyonlar"

    kod: Mapped[str] = mapped_column(String(64), primary_key=True)
    ad: Mapped[str] = mapped_column(String(512), nullable=False)


class BirimUcret(Base):
    __tablename__ = "birim_ucretler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    birim: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    ucret: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class HarcamaTalep(Base):
    __tablename__ = "harcama_talep"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    no: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tarih: Mapped[date] = mapped_column(Date, nullable=False)
    bolge_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kaynak_tipi_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage_operasyon_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    safha: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    harcama_kalemi: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    birim: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    miktar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birim_ucret: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    toplam: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_manuel: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True
    )


class HarcamaTalepManuelDegisiklik(Base):
    __tablename__ = "harcama_talep_manuel_degisiklikler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    harcama_talep_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("harcama_talep.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    alan_adi: Mapped[str] = mapped_column(String(128), nullable=False)
    eski_deger: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    yeni_deger: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    degisiklik_tarihi: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=True
    )


class Masraf(Base):
    __tablename__ = "masraf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tarih: Mapped[date] = mapped_column(Date, nullable=False)
    bolge_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kaynak_tipi_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage_operasyon_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    no: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kimden_alindi: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tutar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tarih: Mapped[date] = mapped_column(Date, nullable=False)
    bolge_kodu: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kaynak_tipi: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage_operasyon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    no_su: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    kimden_alindigi: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tutar: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True
    )
