import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProviderType(str, enum.Enum):
    EMAIL = "EMAIL"
    KAKAO = "KAKAO"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String)
    name: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(
        SAEnum(ProviderType, name="provider_type", create_constraint=True),
        nullable=False,
        default=ProviderType.EMAIL,
    )
    provider_id: Mapped[str | None] = mapped_column(String)
    profile: Mapped[dict | None] = mapped_column(JSONB)
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="user")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")
