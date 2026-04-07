from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.program import SourceType, ProgramStatus


# ---------------------------------------------------------------------------
# Base / Create / Update
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Response — Full (상세)
# ---------------------------------------------------------------------------


class ProgramResponse(ProgramBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    view_count: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Response — List item (목록용, 무거운 필드 제외)
# ---------------------------------------------------------------------------


class ProgramListItem(BaseModel):
    """목록 조회용 경량 응답 (description, raw_data 제외)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source: SourceType
    organization: str | None = None
    category: str | None = None
    region: str | None = None
    target_type: str | None = None
    support_amount: str | None = None
    support_amount_max: int | None = None
    application_start: datetime | None = None
    application_end: datetime | None = None
    status: ProgramStatus
    tags: list[str] | None = None
    view_count: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Facet / Filter counts
# ---------------------------------------------------------------------------


class FacetItem(BaseModel):
    name: str
    count: int


class FilterFacets(BaseModel):
    categories: list[FacetItem] = []
    regions: list[FacetItem] = []
    sources: list[FacetItem] = []


# ---------------------------------------------------------------------------
# Paginated list response
# ---------------------------------------------------------------------------


class ProgramListResponse(BaseModel):
    items: list[ProgramListItem]
    total: int
    page: int
    limit: int
    total_pages: int
    filters: FilterFacets | None = None


# ---------------------------------------------------------------------------
# Related program (상세 페이지용)
# ---------------------------------------------------------------------------


class ProgramRelated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    organization: str | None = None
    application_end: datetime | None = None
    status: ProgramStatus


class ProgramDetailResponse(ProgramResponse):
    related: list[ProgramRelated] = []


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


class CalendarProgramItem(BaseModel):
    id: UUID
    title: str
    organization: str | None = None


class CalendarDayEntry(BaseModel):
    date: date
    count: int
    programs: list[CalendarProgramItem]


# ---------------------------------------------------------------------------
# Stats / Dashboard
# ---------------------------------------------------------------------------


class CategoryStat(BaseModel):
    category: str
    count: int


class SourceStat(BaseModel):
    source: str
    count: int


class ProgramStats(BaseModel):
    total: int
    open_count: int
    closing_this_week: int
    by_category: list[CategoryStat]
    by_source: list[SourceStat]
