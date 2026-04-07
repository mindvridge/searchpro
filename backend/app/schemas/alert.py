from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertType, ChannelType


class AlertCreate(BaseModel):
    type: AlertType
    condition: dict
    channel: ChannelType


class AlertUpdate(BaseModel):
    condition: dict | None = None
    channel: ChannelType | None = None
    is_active: bool | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: AlertType
    condition: dict
    channel: ChannelType
    is_active: bool
    created_at: datetime
