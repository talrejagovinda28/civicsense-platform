"""Protect all CivicSense tables from direct Supabase browser-role access.

Revision ID: 010
Revises: 009

FastAPI connects to PostgreSQL as the table owner. The browser does not use
Supabase Data API for application reads/writes: all authorization is enforced
through the FastAPI endpoints. Supabase anon/authenticated must not be able to
access raw complaint, user, chat or moderation tables.
"""

from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Lock down both existing and newly created tables. Owner postgres bypasses
    # RLS by default; DO NOT set FORCE ROW LEVEL SECURITY here.
    op.execute(
        """
        DO $$
        DECLARE table_row record;
        BEGIN
            FOR table_row IN
                SELECT c.relname AS table_name
                FROM pg_class AS c
                JOIN pg_namespace AS n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
            LOOP
                EXECUTE format(
                    'ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',
                    table_row.table_name
                );
            END LOOP;
        END;
        $$;
        """
    )
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM anon, authenticated")
    op.execute("REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated")
    op.execute("ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated")
    op.execute("ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated")


def downgrade() -> None:
    # Intentionally retain access controls on downgrade; rolling back an app
    # revision must not silently expose complaint/user data through PostgREST.
    pass
