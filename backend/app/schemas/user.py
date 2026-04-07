from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import ProviderType


class UserBase(BaseModel):
    email: str
    name: str | None = None
    provider: ProviderType = ProviderType.EMAIL
    provider_id: str | None = None
    profile: dict | None = None


class UserCreate(UserBase):
    password: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    profile: dict | None = None
    is_premium: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None
    provider: ProviderType
    profile: dict | None
    is_premium: bool
    created_at: datetime
    updated_at: datetime
