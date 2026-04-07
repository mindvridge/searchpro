import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Index,
    UniqueConstraint,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------- Enums ----------

import enum


class SourceType(str, enum.Enum):
    BIZINFO = "BIZINFO"
    KSTARTUP = "KSTARTUP"
    SUBSIDY24 = "SUBSIDY24"
    NTIS = "NTIS"
    THINKCONTEST = "THINKCONTEST"
    WEVITY = "WEVITY"
    MANUAL = "MANUAL"


class ProgramStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(
        SAEnum(SourceType, name="source_type", create_constraint=True), nullable=False
    )
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    sub_category: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(50))
    target_type: Mapped[str | None] = mapped_column(String(100))
    support_amount: Mapped[str | None] = mapped_column(String(200))
    support_amount_max: Mapped[int | None] = mapped_column(Integer)
    application_start: Mapped[datetime | None] = mapped_column(DateTime)
    application_end: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        SAEnum(ProgramStatus, name="program_status", create_constraint=True),
        nullable=False,
        default=ProgramStatus.UPCOMING,
    )
    description: Mapped[str | None] = mapped_column(Text)
    eligibility: Mapped[str | None] = mapped_column(Text)
    detail_url: Mapped[str | None] = mapped_column(String(1000))
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    summary: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="program")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_program_source"),
        Index("ix_programs_application_end", "application_end"),
        Index("ix_programs_status", "status"),
        Index("ix_programs_category", "category"),
        Index("ix_programs_region", "region"),
        Index("ix_programs_tags", "tags", postgresql_using="gin"),
    )
