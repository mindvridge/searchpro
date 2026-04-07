from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.program import SourceType, ProgramStatus


class ProgramBase(BaseModel):
    title: str
    source: SourceType
    source_id: str
    organization: str | None = None
    category: str | None = None
    sub_category: str | None = None
    region: str | None = None
    target_type: str | None = None
    support_amount: str | None = None
    support_amount_max: int | None = None
    application_start: datetime | None = None
    application_end: datetime | None = None
    status: ProgramStatus = ProgramStatus.UPCOMING
    description: str | None = None
    eligibility: str | None = None
    detail_url: str | None = None
    raw_data: dict | None = None
    summary: str | None = None
    tags: list[str] | None = None


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    title: str | None = None
    organization: str | None = None
    category: str | None = None
    sub_category: str | None = None
    region: str | None = None
    target_type: str | None = None
    support_amount: str | None = None
    support_amount_max: int | None = None
    application_start: datetime | None = None
    application_end: datetime | None = None
    status: ProgramStatus | None = None
    description: str | None = None
    eligibility: str | None = None
    detail_url: str | None = None
    summary: str | None = None
    tags: list[str] | None = None


class ProgramResponse(ProgramBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    view_count: int
    created_at: datetime
    updated_at: datetime


class ProgramListResponse(BaseModel):
    items: list[ProgramResponse]
    total: int
    page: int
    limit: int
    total_pages: int
