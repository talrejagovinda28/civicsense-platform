"""Add complaint jurisdiction FKs, public map coords, external submissions

Revision ID: 008
Revises: 007
Create Date: 2026-09-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "complaints",
        sa.Column("electoral_ward_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "complaints",
        sa.Column("ward_office_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "complaints",
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("complaints", sa.Column("public_latitude", sa.Float(), nullable=True))
    op.add_column("complaints", sa.Column("public_longitude", sa.Float(), nullable=True))

    op.create_foreign_key(
        "fk_complaints_city_id",
        "complaints",
        "cities",
        ["city_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_complaints_electoral_ward_id",
        "complaints",
        "electoral_wards",
        ["electoral_ward_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_complaints_ward_office_id",
        "complaints",
        "ward_offices",
        ["ward_office_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_complaints_department_id",
        "complaints",
        "departments",
        ["department_id"],
        ["id"],
    )

    bind = op.get_bind()
    pune_id = bind.execute(sa.text("SELECT id FROM cities WHERE slug = 'pune'")).scalar_one()
    bind.execute(
        sa.text(
            """
            UPDATE complaints
            SET city_id = :pune_id
            WHERE city ILIKE 'pune' AND city_id IS NULL
            """
        ),
        {"pune_id": pune_id},
    )
    bind.execute(
        sa.text(
            """
            UPDATE complaints
            SET public_latitude = ROUND(latitude::numeric, 3),
                public_longitude = ROUND(longitude::numeric, 3)
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
        )
    )

    op.create_table(
        "external_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("routing_channel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="pmc_care"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("external_token", sa.String(length=120), nullable=True),
        sa.Column("status_url", sa.String(length=500), nullable=True),
        sa.Column("forwarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.ForeignKeyConstraint(["routing_channel_id"], ["routing_channels.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id"),
    )


def downgrade() -> None:
    op.drop_table("external_submissions")
    op.drop_constraint("fk_complaints_department_id", "complaints", type_="foreignkey")
    op.drop_constraint("fk_complaints_ward_office_id", "complaints", type_="foreignkey")
    op.drop_constraint("fk_complaints_electoral_ward_id", "complaints", type_="foreignkey")
    op.drop_constraint("fk_complaints_city_id", "complaints", type_="foreignkey")
    op.drop_column("complaints", "public_longitude")
    op.drop_column("complaints", "public_latitude")
    op.drop_column("complaints", "department_id")
    op.drop_column("complaints", "ward_office_id")
    op.drop_column("complaints", "electoral_ward_id")
    op.drop_column("complaints", "city_id")
