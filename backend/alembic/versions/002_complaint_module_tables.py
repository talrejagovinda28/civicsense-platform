"""Complaint module tables + Pune category seed

Revision ID: 002
Revises: 001
Create Date: 2026-07-15

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
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

PUNE_CATEGORIES = [
    ("Pothole", "pothole"),
    ("Garbage", "garbage"),
    ("Streetlight", "streetlight"),
    ("Drainage", "drainage"),
    ("Water Leak", "water_leak"),
    ("Illegal Construction", "illegal_construction"),
    ("Other", "other"),
]


def upgrade() -> None:
    complaint_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            complaint_status,
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_suggested_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("google_place_id", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("ward", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False, server_default="Pune"),
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
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["ai_suggested_category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaints_user_id", "complaints", ["user_id"])

    op.create_table(
        "complaint_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cloudinary_url", sa.String(length=500), nullable=False),
        sa.Column("cloudinary_public_id", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
    op.create_index("ix_complaint_images_complaint_id", "complaint_images", ["complaint_id"])

    categories_table = sa.table(
        "categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        categories_table,
        [
            {
                "id": uuid.uuid4(),
                "name": name,
                "slug": slug,
                "is_active": True,
            }
            for name, slug in PUNE_CATEGORIES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_complaint_images_complaint_id", table_name="complaint_images")
    op.drop_table("complaint_images")
    op.drop_index("ix_complaints_user_id", table_name="complaints")
    op.drop_table("complaints")
    op.drop_table("categories")
    complaint_status.drop(op.get_bind(), checkfirst=True)
