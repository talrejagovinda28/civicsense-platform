"""Add complaint status history table

Revision ID: 003
Revises: 002
Create Date: 2026-09-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

complaint_status = postgresql.ENUM(
    "submitted",
    "in_progress",
    "resolved",
    "closed",
    name="complaint_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "complaint_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", complaint_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["complaint_id"],
            ["complaints.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_complaint_status_history_complaint_id",
        "complaint_status_history",
        ["complaint_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_complaint_status_history_complaint_id",
        table_name="complaint_status_history",
    )
    op.drop_table("complaint_status_history")
