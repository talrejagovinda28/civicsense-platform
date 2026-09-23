"""India social and accountability pack

Revision ID: 009
Revises: 008
Create Date: 2026-09-22

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PMC_ONLINE_COMPLAINT_URL = "https://www.pmc.gov.in/en/online-complaint"


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clerk_user_id", sa.String(length=255), nullable=False),
        sa.Column("handle", sa.String(length=50), nullable=True),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "dm_policy",
            sa.String(length=30),
            nullable=False,
            server_default="mutual_or_request",
        ),
        sa.Column(
            "official_dm_opt_in",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("home_locality_label", sa.String(length=200), nullable=True),
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
        sa.UniqueConstraint("clerk_user_id"),
        sa.UniqueConstraint("handle"),
    )
    op.create_index("ix_user_profiles_clerk_user_id", "user_profiles", ["clerk_user_id"])

    op.add_column(
        "complaints",
        sa.Column(
            "anonymous_to_public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "complaints",
        sa.Column(
            "is_sensitive",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("complaints", sa.Column("public_caption", sa.Text(), nullable=True))
    op.add_column(
        "complaints",
        sa.Column(
            "verification_state",
            sa.String(length=30),
            nullable=False,
            server_default="none",
        ),
    )
    op.add_column(
        "complaints",
        sa.Column(
            "submission_state",
            sa.String(length=30),
            nullable=False,
            server_default="internal_created",
        ),
    )
    op.add_column(
        "complaints",
        sa.Column("route_confidence", sa.String(length=20), nullable=True),
    )

    op.add_column(
        "complaint_images",
        sa.Column(
            "resource_type",
            sa.String(length=20),
            nullable=False,
            server_default="image",
        ),
    )
    op.add_column("complaint_images", sa.Column("duration_seconds", sa.Float(), nullable=True))
    op.add_column(
        "complaint_images",
        sa.Column(
            "evidence_kind",
            sa.String(length=20),
            nullable=False,
            server_default="report",
        ),
    )
    op.add_column(
        "complaint_images",
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="public",
        ),
    )

    op.create_table(
        "authority_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("origin_url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("publisher", sa.String(length=200), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("validation_note", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="research_only",
        ),
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
    )

    op.create_table(
        "external_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("routing_channel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel_type", sa.String(length=50), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column(
            "activation",
            sa.String(length=30),
            nullable=False,
            server_default="DISABLED",
        ),
        sa.Column("destination", sa.String(length=500), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "can_auto_submit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "supports_tracking",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("on_behalf_policy", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("disable_reason", sa.String(length=500), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["routing_channel_id"], ["routing_channels.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["authority_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_channels_city_id", "external_channels", ["city_id"])

    op.create_table(
        "submission_consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("disclosure_json", sa.Text(), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.String(length=50), nullable=False),
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
        sa.ForeignKeyConstraint(["channel_id"], ["external_channels.id"]),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submission_consents_complaint_id", "submission_consents", ["complaint_id"])
    op.create_index("ix_submission_consents_user_id", "submission_consents", ["user_id"])

    op.create_table(
        "submission_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_snapshot", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("test_scenario", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["channel_id"], ["external_channels.id"]),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["consent_id"], ["submission_consents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_submission_intents_complaint_id", "submission_intents", ["complaint_id"])

    op.create_table(
        "submission_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("transport_state", sa.String(length=30), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column(
            "unknown_outcome",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("response_metadata_redacted", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["intent_id"], ["submission_intents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("intent_id", "attempt_no", name="uq_submission_attempts_intent_no"),
    )
    op.create_index("ix_submission_attempts_intent_id", "submission_attempts", ["intent_id"])

    op.create_table(
        "complaint_timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("actor_kind", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("authenticity_level", sa.String(length=30), nullable=False),
        sa.Column("public_payload_redacted", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        "ix_complaint_timeline_events_complaint_id",
        "complaint_timeline_events",
        ["complaint_id"],
    )
    op.create_index(
        "ix_complaint_timeline_events_complaint_created",
        "complaint_timeline_events",
        ["complaint_id", "created_at"],
    )

    op.create_table(
        "external_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_value", sa.String(length=255), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tracking_url", sa.String(length=500), nullable=True),
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="owner",
        ),
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
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["intent_id"], ["submission_intents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_references_complaint_id", "external_references", ["complaint_id"])

    op.create_table(
        "resolution_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitter_id", sa.String(length=255), nullable=False),
        sa.Column("submitter_role", sa.String(length=30), nullable=False),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("assertion", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
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
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resolution_evidence_complaint_id", "resolution_evidence", ["complaint_id"])

    op.create_table(
        "resolution_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reviewer_id", sa.String(length=255), nullable=False),
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
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["resolution_evidence.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resolution_reviews_complaint_id", "resolution_reviews", ["complaint_id"])

    op.create_table(
        "feed_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("timeline_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="public",
        ),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_event_id"], ["complaint_timeline_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feed_events_complaint_id", "feed_events", ["complaint_id"])
    op.create_index("ix_feed_events_published_at", "feed_events", ["published_at"])
    op.create_index(
        "uq_feed_events_complaint_kind_original",
        "feed_events",
        ["complaint_id", "kind"],
        unique=True,
        postgresql_where=sa.text("kind = 'original'"),
    )
    op.create_index(
        "uq_feed_events_complaint_timeline_event",
        "feed_events",
        ["complaint_id", "timeline_event_id"],
        unique=True,
        postgresql_where=sa.text("timeline_event_id IS NOT NULL"),
    )

    op.create_table(
        "likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "complaint_id", name="uq_likes_user_complaint"),
    )
    op.create_index("ix_likes_user_id", "likes", ["user_id"])
    op.create_index("ix_likes_complaint_id", "likes", ["complaint_id"])

    op.create_table(
        "affected",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "complaint_id", name="uq_affected_user_complaint"),
    )
    op.create_index("ix_affected_user_id", "affected", ["user_id"])
    op.create_index("ix_affected_complaint_id", "affected", ["complaint_id"])

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "moderation_status",
            sa.String(length=20),
            nullable=False,
            server_default="visible",
        ),
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
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_complaint_id", "comments", ["complaint_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index("ix_comments_complaint_created", "comments", ["complaint_id", "created_at"])

    op.create_table(
        "follows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("follower_id", sa.String(length=255), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("follower_id", "target_id", name="uq_follows_follower_target"),
    )
    op.create_index("ix_follows_follower_id", "follows", ["follower_id"])
    op.create_index("ix_follows_target_id", "follows", ["target_id"])

    op.create_table(
        "user_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("blocker_id", sa.String(length=255), nullable=False),
        sa.Column("blocked_id", sa.String(length=255), nullable=False),
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
        sa.UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_blocker_blocked"),
    )
    op.create_index("ix_user_blocks_blocker_id", "user_blocks", ["blocker_id"])
    op.create_index("ix_user_blocks_blocked_id", "user_blocks", ["blocked_id"])

    op.create_table(
        "reputation_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("event_key", sa.String(length=128), nullable=False),
        sa.Column("source_entity_id", sa.String(length=255), nullable=True),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="granted",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key"),
    )
    op.create_index("ix_reputation_ledger_user_id", "reputation_ledger", ["user_id"])

    op.create_table(
        "badge_awards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("badge_code", sa.String(length=50), nullable=False),
        sa.Column("source_event_key", sa.String(length=128), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_event_key"),
    )
    op.create_index("ix_badge_awards_user_id", "badge_awards", ["user_id"])

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("issue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(["issue_id"], ["complaints.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conversation_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_members_conversation_user",
        ),
    )
    op.create_index(
        "ix_conversation_members_conversation_id",
        "conversation_members",
        ["conversation_id"],
    )
    op.create_index("ix_conversation_members_user_id", "conversation_members", ["user_id"])

    op.create_table(
        "message_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", sa.String(length=255), nullable=False),
        sa.Column("recipient_id", sa.String(length=255), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sender_id", "recipient_id", name="uq_message_requests_sender_recipient"),
    )
    op.create_index("ix_message_requests_sender_id", "message_requests", ["sender_id"])
    op.create_index("ix_message_requests_recipient_id", "message_requests", ["recipient_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "moderation_status",
            sa.String(length=20),
            nullable=False,
            server_default="visible",
        ),
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
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])

    op.create_table(
        "message_reads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_message_reads_conversation_user",
        ),
    )
    op.create_index("ix_message_reads_conversation_id", "message_reads", ["conversation_id"])
    op.create_index("ix_message_reads_user_id", "message_reads", ["user_id"])

    op.create_table(
        "moderation_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_id", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="open",
        ),
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
    )
    op.create_index("ix_moderation_reports_reporter_id", "moderation_reports", ["reporter_id"])
    op.create_index("ix_moderation_reports_target_id", "moderation_reports", ["target_id"])

    op.create_table(
        "moderation_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("moderator_id", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
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
    )
    op.create_index("ix_moderation_actions_moderator_id", "moderation_actions", ["moderator_id"])
    op.create_index("ix_moderation_actions_target_id", "moderation_actions", ["target_id"])

    op.create_table(
        "complaint_related",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id_a", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id_b", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(["complaint_id_a"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["complaint_id_b"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "complaint_id_a",
            "complaint_id_b",
            name="uq_complaint_related_pair",
        ),
    )

    op.create_index(
        "ix_complaints_city_id_created_at",
        "complaints",
        ["city_id", "created_at"],
        postgresql_where=sa.text("city_id IS NOT NULL"),
    )

    bind = op.get_bind()
    pune_id = bind.execute(sa.text("SELECT id FROM cities WHERE slug = 'pune'")).scalar_one()
    source_id = uuid.uuid4()
    channel_id = uuid.uuid4()

    authority_sources_table = sa.table(
        "authority_sources",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("origin_url", sa.String),
        sa.column("title", sa.String),
        sa.column("publisher", sa.String),
        sa.column("evidence_type", sa.String),
        sa.column("validation_note", sa.String),
        sa.column("status", sa.String),
    )
    op.bulk_insert(
        authority_sources_table,
        [
            {
                "id": source_id,
                "origin_url": PMC_ONLINE_COMPLAINT_URL,
                "title": "PMC Online Complaint Portal",
                "publisher": "Pune Municipal Corporation",
                "evidence_type": "web_portal",
                "validation_note": "Research-only seed; channel disabled pending verification.",
                "status": "research_only",
            }
        ],
    )

    external_channels_table = sa.table(
        "external_channels",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("city_id", postgresql.UUID(as_uuid=True)),
        sa.column("routing_channel_id", postgresql.UUID(as_uuid=True)),
        sa.column("channel_type", sa.String),
        sa.column("mode", sa.String),
        sa.column("activation", sa.String),
        sa.column("destination", sa.String),
        sa.column("source_id", postgresql.UUID(as_uuid=True)),
        sa.column("can_auto_submit", sa.Boolean),
        sa.column("supports_tracking", sa.Boolean),
        sa.column("on_behalf_policy", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("disable_reason", sa.String),
    )
    op.bulk_insert(
        external_channels_table,
        [
            {
                "id": channel_id,
                "city_id": pune_id,
                "routing_channel_id": None,
                "channel_type": "web_portal",
                "mode": "GUIDED_PORTAL",
                "activation": "DISABLED",
                "destination": PMC_ONLINE_COMPLAINT_URL,
                "source_id": source_id,
                "can_auto_submit": False,
                "supports_tracking": False,
                "on_behalf_policy": "citizen_self",
                "enabled": False,
                "disable_reason": "Research-only channel; not enabled for automated submission.",
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_complaints_city_id_created_at", table_name="complaints")

    op.drop_table("complaint_related")
    op.drop_index("ix_moderation_actions_target_id", table_name="moderation_actions")
    op.drop_index("ix_moderation_actions_moderator_id", table_name="moderation_actions")
    op.drop_table("moderation_actions")
    op.drop_index("ix_moderation_reports_target_id", table_name="moderation_reports")
    op.drop_index("ix_moderation_reports_reporter_id", table_name="moderation_reports")
    op.drop_table("moderation_reports")
    op.drop_index("ix_message_reads_user_id", table_name="message_reads")
    op.drop_index("ix_message_reads_conversation_id", table_name="message_reads")
    op.drop_table("message_reads")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_message_requests_recipient_id", table_name="message_requests")
    op.drop_index("ix_message_requests_sender_id", table_name="message_requests")
    op.drop_table("message_requests")
    op.drop_index("ix_conversation_members_user_id", table_name="conversation_members")
    op.drop_index("ix_conversation_members_conversation_id", table_name="conversation_members")
    op.drop_table("conversation_members")
    op.drop_table("conversations")
    op.drop_index("ix_badge_awards_user_id", table_name="badge_awards")
    op.drop_table("badge_awards")
    op.drop_index("ix_reputation_ledger_user_id", table_name="reputation_ledger")
    op.drop_table("reputation_ledger")
    op.drop_index("ix_user_blocks_blocked_id", table_name="user_blocks")
    op.drop_index("ix_user_blocks_blocker_id", table_name="user_blocks")
    op.drop_table("user_blocks")
    op.drop_index("ix_follows_target_id", table_name="follows")
    op.drop_index("ix_follows_follower_id", table_name="follows")
    op.drop_table("follows")
    op.drop_index("ix_comments_complaint_created", table_name="comments")
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_complaint_id", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_affected_complaint_id", table_name="affected")
    op.drop_index("ix_affected_user_id", table_name="affected")
    op.drop_table("affected")
    op.drop_index("ix_likes_complaint_id", table_name="likes")
    op.drop_index("ix_likes_user_id", table_name="likes")
    op.drop_table("likes")
    op.drop_index("uq_feed_events_complaint_timeline_event", table_name="feed_events")
    op.drop_index("uq_feed_events_complaint_kind_original", table_name="feed_events")
    op.drop_index("ix_feed_events_published_at", table_name="feed_events")
    op.drop_index("ix_feed_events_complaint_id", table_name="feed_events")
    op.drop_table("feed_events")
    op.drop_index("ix_resolution_reviews_complaint_id", table_name="resolution_reviews")
    op.drop_table("resolution_reviews")
    op.drop_index("ix_resolution_evidence_complaint_id", table_name="resolution_evidence")
    op.drop_table("resolution_evidence")
    op.drop_index("ix_external_references_complaint_id", table_name="external_references")
    op.drop_table("external_references")
    op.drop_index("ix_complaint_timeline_events_complaint_created", table_name="complaint_timeline_events")
    op.drop_index("ix_complaint_timeline_events_complaint_id", table_name="complaint_timeline_events")
    op.drop_table("complaint_timeline_events")
    op.drop_index("ix_submission_attempts_intent_id", table_name="submission_attempts")
    op.drop_table("submission_attempts")
    op.drop_index("ix_submission_intents_complaint_id", table_name="submission_intents")
    op.drop_table("submission_intents")
    op.drop_index("ix_submission_consents_user_id", table_name="submission_consents")
    op.drop_index("ix_submission_consents_complaint_id", table_name="submission_consents")
    op.drop_table("submission_consents")
    op.drop_index("ix_external_channels_city_id", table_name="external_channels")
    op.drop_table("external_channels")
    op.drop_table("authority_sources")

    op.drop_column("complaint_images", "visibility")
    op.drop_column("complaint_images", "evidence_kind")
    op.drop_column("complaint_images", "duration_seconds")
    op.drop_column("complaint_images", "resource_type")

    op.drop_column("complaints", "route_confidence")
    op.drop_column("complaints", "submission_state")
    op.drop_column("complaints", "verification_state")
    op.drop_column("complaints", "public_caption")
    op.drop_column("complaints", "is_sensitive")
    op.drop_column("complaints", "anonymous_to_public")

    op.drop_index("ix_user_profiles_clerk_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")
