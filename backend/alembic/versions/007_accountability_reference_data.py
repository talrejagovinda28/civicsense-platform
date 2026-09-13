"""Add accountability reference data and routing configuration

Revision ID: 007
Revises: 006
Create Date: 2026-09-14

"""

import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VERIFIED_2025 = datetime(2025, 11, 25, tzinfo=timezone.utc)
VERIFIED_2026 = datetime(2026, 1, 15, tzinfo=timezone.utc)
PMC_ENV_SOURCE = "https://www.pmc.gov.in/en/b/environment-status-report"
PMC_CARE_SOURCE = "https://pmccare.in/"
ELECTION_SOURCE = (
    "https://data.opencity.in/dataset/pmc-election-results-2026/resource/"
    "ac74e3a3-0fce-4ce5-bcdf-b3b6271ae722"
)

PUNE_WARD_OFFICES = [
    ("aundh-baner", "Aundh - Baner"),
    ("bhavani-peth", "Bhavani Peth"),
    ("bibwewadi", "Bibwewadi"),
    ("dhankawadi-sahakar-nagar", "Dhankawadi - Sahakar Nagar"),
    ("dhole-patil-road", "Dhole Patil Road"),
    ("hadapsar-mundhwa", "Hadapsar - Mundhwa"),
    ("kasaba-vishrambagwada", "Kasaba Vishrambagwada"),
    ("kondhwa-yewalewadi", "Kondhwa - Yewalewadi"),
    ("kothrud-bavdhan", "Kothrud - Bavdhan"),
    ("nagar-road-vadgaonsheri", "Nagar Road - Vadgaonsheri"),
    ("shivajinagar-ghole-road", "Shivajinagar - Ghole Road"),
    ("sinhgad-road", "Sinhgad Road"),
    ("wanawadi-ramtekdi", "Wanawadi / Wanowrie - Ramtekdi"),
    ("warje-karvenagar", "Warje - Karvenagar"),
    ("yerawada-kalas-dhanori", "Yerawada - Kalas - Dhanori"),
]

PUNE_DEPARTMENTS = [
    ("road", "Road Department"),
    ("solid-waste", "Solid Waste Management"),
    ("electrical", "Electrical Department"),
    ("drainage", "Drainage Department"),
    ("water-supply", "Water Supply Department"),
    ("building-permission", "Building Permission Department"),
]

CATEGORY_DEPARTMENT_SLUGS = {
    "pothole": "road",
    "garbage": "solid-waste",
    "streetlight": "electrical",
    "drainage": "drainage",
    "water_leak": "water-supply",
    "illegal_construction": "building-permission",
    "other": "road",
}


def _load_representative_rows(csv_path: Path) -> list[dict]:
    rows: list[dict] = []
    current_ward_no: int | None = None
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ward_no_raw = (row.get("Ward No.") or "").strip()
            if ward_no_raw:
                current_ward_no = int(float(ward_no_raw))
            if current_ward_no is None:
                continue
            rows.append(
                {
                    "ward_no": current_ward_no,
                    "seat_label": (row.get("Seat") or "").strip(),
                    "reservation": (row.get("Reservation") or "").strip() or None,
                    "full_name": (row.get("Elected Candidate Name") or "").strip(),
                    "party": (row.get("Party") or "").strip() or None,
                }
            )
    return rows


def upgrade() -> None:
    op.create_table(
        "ward_offices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("source_name", sa.String(length=200), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "slug", name="uq_ward_offices_city_slug"),
    )
    op.create_table(
        "public_officials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("party", sa.String(length=100), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("source_license", sa.String(length=100), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "official_jurisdictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public_official_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("electoral_ward_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seat_label", sa.String(length=20), nullable=False),
        sa.Column("reservation", sa.String(length=100), nullable=True),
        sa.Column("term_label", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["public_official_id"], ["public_officials.id"]),
        sa.ForeignKeyConstraint(["electoral_ward_id"], ["electoral_wards.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("electoral_ward_id", "seat_label", name="uq_official_jurisdictions_ward_seat"),
    )
    op.create_table(
        "ward_jurisdiction_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("electoral_ward_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ward_office_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["electoral_ward_id"], ["electoral_wards.id"]),
        sa.ForeignKeyConstraint(["ward_office_id"], ["ward_offices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("electoral_ward_id", name="uq_ward_jurisdiction_mappings_electoral_ward"),
    )
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "slug", name="uq_departments_city_slug"),
    )
    op.create_table(
        "category_routing_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "category_id", name="uq_category_routing_city_category"),
    )
    op.create_table(
        "routing_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    bind = op.get_bind()
    pune_id = bind.execute(sa.text("SELECT id FROM cities WHERE slug = 'pune'")).scalar_one()

    ward_offices_table = sa.table(
        "ward_offices",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("source_url", sa.String),
        sa.column("source_name", sa.String),
        sa.column("verified_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        ward_offices_table,
        [
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "name": name,
                "slug": slug,
                "source_url": PMC_ENV_SOURCE,
                "source_name": "PMC Environmental Status Report",
                "verified_at": VERIFIED_2025,
            }
            for slug, name in PUNE_WARD_OFFICES
        ],
    )

    departments_table = sa.table(
        "departments",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("source_url", sa.String),
        sa.column("verified_at", sa.DateTime(timezone=True)),
    )
    department_ids: dict[str, uuid.UUID] = {}
    department_rows = []
    for slug, name in PUNE_DEPARTMENTS:
        dept_id = uuid.uuid4()
        department_ids[slug] = dept_id
        department_rows.append(
            {
                "id": dept_id,
                "city_id": pune_id,
                "name": name,
                "slug": slug,
                "source_url": PMC_ENV_SOURCE,
                "verified_at": VERIFIED_2025,
            }
        )
    op.bulk_insert(departments_table, department_rows)

    category_rows = bind.execute(sa.text("SELECT id, slug FROM categories")).all()
    category_id_by_slug = {row.slug: row.id for row in category_rows}
    routing_rules_table = sa.table(
        "category_routing_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("category_id", postgresql.UUID(as_uuid=True)),
        sa.column("department_id", postgresql.UUID(as_uuid=True)),
        sa.column("notes", sa.String),
    )
    op.bulk_insert(
        routing_rules_table,
        [
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "category_id": category_id_by_slug[category_slug],
                "department_id": department_ids[department_slug],
                "notes": "Mapped from CivicSense category to PMC department naming.",
            }
            for category_slug, department_slug in CATEGORY_DEPARTMENT_SLUGS.items()
            if category_slug in category_id_by_slug
        ],
    )

    routing_channels_table = sa.table(
        "routing_channels",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("channel_type", sa.String),
        sa.column("label", sa.String),
        sa.column("value", sa.String),
        sa.column("url", sa.String),
        sa.column("is_official", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("source_url", sa.String),
        sa.column("verified_at", sa.DateTime(timezone=True)),
        sa.column("notes", sa.String),
    )
    op.bulk_insert(
        routing_channels_table,
        [
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "channel_type": "web_portal",
                "label": "PMC CARE",
                "value": "Official grievance portal",
                "url": "https://pmccare.in/",
                "is_official": True,
                "is_active": True,
                "source_url": PMC_CARE_SOURCE,
                "verified_at": VERIFIED_2025,
                "notes": "Primary official citizen grievance channel.",
            },
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "channel_type": "phone",
                "label": "PMC Helpline",
                "value": "1800-103-0222",
                "url": None,
                "is_official": True,
                "is_active": True,
                "source_url": PMC_CARE_SOURCE,
                "verified_at": VERIFIED_2025,
                "notes": None,
            },
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "channel_type": "phone",
                "label": "PMC Main Contact",
                "value": "020-25501000",
                "url": None,
                "is_official": True,
                "is_active": True,
                "source_url": PMC_CARE_SOURCE,
                "verified_at": VERIFIED_2025,
                "notes": None,
            },
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "channel_type": "whatsapp",
                "label": "PMC CARE WhatsApp/SMS",
                "value": "9689900002",
                "url": "https://wa.me/919689900002",
                "is_official": True,
                "is_active": True,
                "source_url": PMC_CARE_SOURCE,
                "verified_at": VERIFIED_2025,
                "notes": "Documented in PMC CARE booklet; verify before campaigns.",
            },
            {
                "id": uuid.uuid4(),
                "city_id": pune_id,
                "channel_type": "email",
                "label": "PMC General Contact",
                "value": "info@punecorporation.org",
                "url": "mailto:info@punecorporation.org",
                "is_official": True,
                "is_active": True,
                "source_url": PMC_CARE_SOURCE,
                "verified_at": VERIFIED_2025,
                "notes": "General contact email; not guaranteed grievance intake.",
            },
        ],
    )

    ward_rows = bind.execute(
        sa.text("SELECT id, ward_no FROM electoral_wards WHERE city_id = :city_id"),
        {"city_id": pune_id},
    ).all()
    ward_id_by_number = {row.ward_no: row.id for row in ward_rows}

    csv_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "data"
        / "cities"
        / "pune"
        / "source"
        / "pmc_election_results_2026.csv"
    )
    officials_table = sa.table(
        "public_officials",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("full_name", sa.String),
        sa.column("party", sa.String),
        sa.column("source_url", sa.String),
        sa.column("source_license", sa.String),
        sa.column("verified_at", sa.DateTime(timezone=True)),
    )
    jurisdictions_table = sa.table(
        "official_jurisdictions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("public_official_id", postgresql.UUID(as_uuid=True)),
        sa.column("electoral_ward_id", postgresql.UUID(as_uuid=True)),
        sa.column("seat_label", sa.String),
        sa.column("reservation", sa.String),
        sa.column("term_label", sa.String),
    )
    official_rows = []
    jurisdiction_rows = []
    for row in _load_representative_rows(csv_path):
        official_id = uuid.uuid4()
        official_rows.append(
            {
                "id": official_id,
                "city_id": pune_id,
                "full_name": row["full_name"],
                "party": row["party"],
                "source_url": ELECTION_SOURCE,
                "source_license": "Public Domain",
                "verified_at": VERIFIED_2026,
            }
        )
        jurisdiction_rows.append(
            {
                "id": uuid.uuid4(),
                "public_official_id": official_id,
                "electoral_ward_id": ward_id_by_number[row["ward_no"]],
                "seat_label": row["seat_label"],
                "reservation": row["reservation"],
                "term_label": "2026-2031",
            }
        )
    op.bulk_insert(officials_table, official_rows)
    op.bulk_insert(jurisdictions_table, jurisdiction_rows)


def downgrade() -> None:
    op.drop_table("routing_channels")
    op.drop_table("category_routing_rules")
    op.drop_table("departments")
    op.drop_table("ward_jurisdiction_mappings")
    op.drop_table("official_jurisdictions")
    op.drop_table("public_officials")
    op.drop_table("ward_offices")
