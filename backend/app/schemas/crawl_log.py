from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.crawl_log import CrawlStatus


class CrawlLogCreate(BaseModel):
    source: str


class CrawlLogUpdate(BaseModel):
    finished_at: datetime | None = None
    total_fetched: int | None = None
    new_count: int | None = None
    updated_count: int | None = None
    error_count: int | None = None
    error_detail: str | None = None
    status: CrawlStatus | None = None


class CrawlLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    started_at: datetime
    finished_at: datetime | None
    total_fetched: int
    new_count: int
    updated_count: int
    error_count: int
    error_detail: str | None
    status: CrawlStatus
