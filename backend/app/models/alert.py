import uuid
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlertType(str, enum.Enum):
    KEYWORD = "KEYWORD"
    CATEGORY = "CATEGORY"
    DEADLINE = "DEADLINE"


class ChannelType(str, enum.Enum):
    EMAIL = "EMAIL"
    PUSH = "PUSH"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        SAEnum(AlertType, name="alert_type", create_constraint=True), nullable=False
    )
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    channel: Mapped[str] = mapped_column(
        SAEnum(ChannelType, name="channel_type", create_constraint=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="alerts")
