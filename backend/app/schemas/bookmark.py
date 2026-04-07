from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookmarkCreate(BaseModel):
    program_id: UUID
    memo: str | None = None


class BookmarkUpdate(BaseModel):
    memo: str | None = None


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    program_id: UUID
    memo: str | None
    created_at: datetime
