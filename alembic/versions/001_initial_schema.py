"""Ilk sema — db.models ile uyumlu (PostgreSQL).

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-04-05

"""

from __future__ import annotations

from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from db.models import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from db.models import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
