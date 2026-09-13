"""Add electoral wards table and seed Pune 41 wards

Revision ID: 006
Revises: 005
Create Date: 2026-09-14

"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOURCE_URL = (
    "https://data.opencity.in/dataset/pune-wards-info/resource/"
    "2badcc86-489c-4b7e-b7dd-a273ef01b798"
)
VERIFIED_AT = datetime(2025, 11, 25, tzinfo=timezone.utc)


def upgrade() -> None:
    op.create_table(
        "electoral_wards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_code", sa.String(length=50), nullable=True),
        sa.Column("ward_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("geometry_feature_id", sa.String(length=100), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("source_license", sa.String(length=100), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "ward_no", name="uq_electoral_wards_city_ward_no"),
    )
    op.create_index("ix_electoral_wards_city_id", "electoral_wards", ["city_id"])

    geojson_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "data"
        / "cities"
        / "pune"
        / "electoral_wards_2025.geojson"
    )
    features = json.loads(geojson_path.read_text(encoding="utf-8")).get("features", [])

    bind = op.get_bind()
    pune_id = bind.execute(sa.text("SELECT id FROM cities WHERE slug = 'pune'")).scalar_one()

    wards_table = sa.table(
        "electoral_wards",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("external_code", sa.String),
        sa.column("ward_no", sa.Integer),
        sa.column("name", sa.String),
        sa.column("geometry_feature_id", sa.String),
        sa.column("valid_from", sa.DateTime(timezone=True)),
        sa.column("valid_to", sa.DateTime(timezone=True)),
        sa.column("source_url", sa.String),
        sa.column("source_license", sa.String),
        sa.column("verified_at", sa.DateTime(timezone=True)),
    )

    rows = []
    for feature in features:
        props = feature.get("properties") or {}
        ward_no = int(props["ward_no"])
        rows.append(
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "external_code": None,
                "ward_no": ward_no,
                "name": str(props.get("name") or f"Ward {ward_no}"),
                "geometry_feature_id": str(
                    props.get("geometry_feature_id") or f"pune-ward-{ward_no}"
                ),
                "valid_from": None,
                "valid_to": None,
                "source_url": SOURCE_URL,
                "source_license": "Public Domain",
                "verified_at": VERIFIED_AT,
            }
        )

    op.bulk_insert(wards_table, rows)


def downgrade() -> None:
    op.drop_index("ix_electoral_wards_city_id", table_name="electoral_wards")
    op.drop_table("electoral_wards")
