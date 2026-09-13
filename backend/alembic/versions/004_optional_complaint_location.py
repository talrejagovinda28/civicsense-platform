"""Make complaint location fields optional for manual entry

Revision ID: 004
Revises: 003
Create Date: 2026-09-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("complaints", "latitude", existing_type=sa.Float(), nullable=True)
    op.alter_column("complaints", "longitude", existing_type=sa.Float(), nullable=True)
    op.alter_column(
        "complaints",
        "google_place_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "complaints",
        "google_place_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column("complaints", "longitude", existing_type=sa.Float(), nullable=False)
    op.alter_column("complaints", "latitude", existing_type=sa.Float(), nullable=False)
