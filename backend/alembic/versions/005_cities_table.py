"""Add cities table and seed Pune + preview cities

Revision ID: 005
Revises: 004
Create Date: 2026-09-14

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CITIES = [
    {
        "slug": "pune",
        "name": "Pune",
        "state_name": "Maharashtra",
        "state_code": "MH",
        "status": "active",
        "municipality_name": "Pune Municipal Corporation",
        "center_lat": 18.5204,
        "center_lng": 73.8567,
        "default_zoom": 12,
        "supports_reporting": True,
        "supports_ward_map": True,
        "supports_accountability": True,
        "map_data_version": "2025-electoral",
    },
    {
        "slug": "mumbai",
        "name": "Mumbai",
        "state_name": "Maharashtra",
        "state_code": "MH",
        "status": "preview",
        "municipality_name": "Brihanmumbai Municipal Corporation",
        "center_lat": 19.0760,
        "center_lng": 72.8777,
        "default_zoom": 11,
        "supports_reporting": False,
        "supports_ward_map": False,
        "supports_accountability": False,
        "map_data_version": None,
    },
    {
        "slug": "bengaluru",
        "name": "Bengaluru",
        "state_name": "Karnataka",
        "state_code": "KA",
        "status": "preview",
        "municipality_name": "Bruhat Bengaluru Mahanagara Palike",
        "center_lat": 12.9716,
        "center_lng": 77.5946,
        "default_zoom": 11,
        "supports_reporting": False,
        "supports_ward_map": False,
        "supports_accountability": False,
        "map_data_version": None,
    },
    {
        "slug": "hyderabad",
        "name": "Hyderabad",
        "state_name": "Telangana",
        "state_code": "TG",
        "status": "preview",
        "municipality_name": "Greater Hyderabad Municipal Corporation",
        "center_lat": 17.3850,
        "center_lng": 78.4867,
        "default_zoom": 11,
        "supports_reporting": False,
        "supports_ward_map": False,
        "supports_accountability": False,
        "map_data_version": None,
    },
    {
        "slug": "delhi",
        "name": "Delhi",
        "state_name": "Delhi",
        "state_code": "DL",
        "status": "preview",
        "municipality_name": "Municipal Corporation of Delhi",
        "center_lat": 28.6139,
        "center_lng": 77.2090,
        "default_zoom": 11,
        "supports_reporting": False,
        "supports_ward_map": False,
        "supports_accountability": False,
        "map_data_version": None,
    },
    {
        "slug": "chennai",
        "name": "Chennai",
        "state_name": "Tamil Nadu",
        "state_code": "TN",
        "status": "preview",
        "municipality_name": "Greater Chennai Corporation",
        "center_lat": 13.0827,
        "center_lng": 80.2707,
        "default_zoom": 11,
        "supports_reporting": False,
        "supports_ward_map": False,
        "supports_accountability": False,
        "map_data_version": None,
    },
]


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("state_name", sa.String(length=100), nullable=False),
        sa.Column("state_code", sa.String(length=10), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False, server_default="IN"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="preview"),
        sa.Column("municipality_name", sa.String(length=200), nullable=True),
        sa.Column("center_lat", sa.Float(), nullable=False),
        sa.Column("center_lng", sa.Float(), nullable=False),
        sa.Column("default_zoom", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("supports_reporting", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_ward_map", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "supports_accountability",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("map_data_version", sa.String(length=50), nullable=True),
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
    op.create_index("ix_cities_slug", "cities", ["slug"], unique=True)

    cities_table = sa.table(
        "cities",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("state_name", sa.String),
        sa.column("state_code", sa.String),
        sa.column("country_code", sa.String),
        sa.column("status", sa.String),
        sa.column("municipality_name", sa.String),
        sa.column("center_lat", sa.Float),
        sa.column("center_lng", sa.Float),
        sa.column("default_zoom", sa.Integer),
        sa.column("supports_reporting", sa.Boolean),
        sa.column("supports_ward_map", sa.Boolean),
        sa.column("supports_accountability", sa.Boolean),
        sa.column("map_data_version", sa.String),
    )

    op.bulk_insert(
        cities_table,
        [
            {
                "id": uuid.uuid4(),
                "country_code": "IN",
                **city,
            }
            for city in CITIES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_cities_slug", table_name="cities")
    op.drop_table("cities")
