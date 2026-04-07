"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # --- Enum types ---
    source_type = postgresql.ENUM(
        "BIZINFO", "KSTARTUP", "SUBSIDY24", "NTIS", "THINKCONTEST", "WEVITY", "MANUAL",
        name="source_type",
        create_type=True,
    )
    program_status = postgresql.ENUM(
        "UPCOMING", "OPEN", "CLOSED",
        name="program_status",
        create_type=True,
    )
    provider_type = postgresql.ENUM(
        "EMAIL", "KAKAO",
        name="provider_type",
        create_type=True,
    )
    alert_type = postgresql.ENUM(
        "KEYWORD", "CATEGORY", "DEADLINE",
        name="alert_type",
        create_type=True,
    )
    channel_type = postgresql.ENUM(
        "EMAIL", "PUSH",
        name="channel_type",
        create_type=True,
    )
    crawl_status = postgresql.ENUM(
        "RUNNING", "SUCCESS", "FAILED",
        name="crawl_status",
        create_type=True,
    )

    source_type.create(op.get_bind(), checkfirst=True)
    program_status.create(op.get_bind(), checkfirst=True)
    provider_type.create(op.get_bind(), checkfirst=True)
    alert_type.create(op.get_bind(), checkfirst=True)
    channel_type.create(op.get_bind(), checkfirst=True)
    crawl_status.create(op.get_bind(), checkfirst=True)

    # --- programs ---
    op.create_table(
        "programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source", source_type, nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("organization", sa.String(200)),
        sa.Column("category", sa.String(100)),
        sa.Column("sub_category", sa.String(100)),
        sa.Column("region", sa.String(50)),
        sa.Column("target_type", sa.String(100)),
        sa.Column("support_amount", sa.String(200)),
        sa.Column("support_amount_max", sa.Integer()),
        sa.Column("application_start", sa.DateTime()),
        sa.Column("application_end", sa.DateTime()),
        sa.Column("status", program_status, nullable=False, server_default="UPCOMING"),
        sa.Column("description", sa.Text()),
        sa.Column("eligibility", sa.Text()),
        sa.Column("detail_url", sa.String(1000)),
        sa.Column("raw_data", postgresql.JSONB()),
        sa.Column("summary", sa.Text()),
        sa.Column("tags", postgresql.ARRAY(sa.String())),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_unique_constraint("uq_program_source", "programs", ["source", "source_id"])
    op.create_index("ix_programs_application_end", "programs", ["application_end"])
    op.create_index("ix_programs_status", "programs", ["status"])
    op.create_index("ix_programs_category", "programs", ["category"])
    op.create_index("ix_programs_region", "programs", ["region"])
    op.create_index("ix_programs_tags", "programs", ["tags"], postgresql_using="gin")

    # GIN trigram index on title and description for similarity search
    op.execute(
        "CREATE INDEX ix_programs_title_trgm ON programs USING gin (title gin_trgm_ops);"
    )
    op.execute(
        "CREATE INDEX ix_programs_description_trgm ON programs USING gin (description gin_trgm_ops);"
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("password_hash", sa.String()),
        sa.Column("name", sa.String(100)),
        sa.Column("provider", provider_type, nullable=False, server_default="EMAIL"),
        sa.Column("provider_id", sa.String()),
        sa.Column("profile", postgresql.JSONB()),
        sa.Column("is_premium", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- bookmarks ---
    op.create_table(
        "bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("memo", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_bookmark_user_program", "bookmarks", ["user_id", "program_id"])

    # --- alerts ---
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", alert_type, nullable=False),
        sa.Column("condition", postgresql.JSONB(), nullable=False),
        sa.Column("channel", channel_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- crawl_logs ---
    op.create_table(
        "crawl_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("total_fetched", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_detail", sa.Text()),
        sa.Column("status", crawl_status, nullable=False, server_default="RUNNING"),
    )


def downgrade() -> None:
    op.drop_table("crawl_logs")
    op.drop_table("alerts")
    op.drop_table("bookmarks")
    op.drop_table("users")

    op.execute("DROP INDEX IF EXISTS ix_programs_description_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_programs_title_trgm;")
    op.drop_table("programs")

    op.execute("DROP TYPE IF EXISTS crawl_status;")
    op.execute("DROP TYPE IF EXISTS channel_type;")
    op.execute("DROP TYPE IF EXISTS alert_type;")
    op.execute("DROP TYPE IF EXISTS provider_type;")
    op.execute("DROP TYPE IF EXISTS program_status;")
    op.execute("DROP TYPE IF EXISTS source_type;")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
