"""지원사업 조회 API — 목록, 상세, 캘린더, 통계"""

from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import Select, and_, case, desc, func, or_, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from cachetools import TTLCache

from app.database import get_db
from app.models.program import Program, ProgramStatus, SourceType
from app.schemas.program import (
    CalendarDayEntry,
    CalendarProgramItem,
    CategoryStat,
    FacetItem,
    FilterFacets,
    ProgramDetailResponse,
    ProgramListItem,
    ProgramListResponse,
    ProgramRelated,
    ProgramResponse,
    ProgramStats,
    SourceStat,
)

router = APIRouter(prefix="/programs", tags=["programs"])

# ---------------------------------------------------------------------------
# In-memory cache (TTL 5 min)
# ---------------------------------------------------------------------------

_facet_cache: TTLCache[str, FilterFacets] = TTLCache(maxsize=64, ttl=300)
_stats_cache: TTLCache[str, ProgramStats] = TTLCache(maxsize=8, ttl=300)

# ---------------------------------------------------------------------------
# Column set for list queries (heavy fields excluded)
# ---------------------------------------------------------------------------

_LIST_COLUMNS = [
    Program.id,
    Program.title,
    Program.source,
    Program.organization,
    Program.category,
    Program.region,
    Program.target_type,
    Program.support_amount,
    Program.support_amount_max,
    Program.application_start,
    Program.application_end,
    Program.status,
    Program.tags,
    Program.view_count,
    Program.created_at,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_filters(
    stmt: Select,
    *,
    q: str | None,
    categories: list[str] | None,
    regions: list[str] | None,
    status: ProgramStatus | None,
    target_type: str | None,
    amount_min: int | None,
    amount_max: int | None,
    sources: list[str] | None,
    deadline_from: date | None,
    deadline_to: date | None,
) -> Select:
    """공통 필터 조건을 SELECT 문에 적용한다."""

    if status is not None:
        stmt = stmt.where(Program.status == status)

    if categories:
        stmt = stmt.where(Program.category.in_(categories))

    if regions:
        stmt = stmt.where(Program.region.in_(regions))

    if target_type:
        stmt = stmt.where(Program.target_type.ilike(f"%{target_type}%"))

    if amount_min is not None:
        stmt = stmt.where(Program.support_amount_max >= amount_min)

    if amount_max is not None:
        stmt = stmt.where(Program.support_amount_max <= amount_max)

    if sources:
        stmt = stmt.where(Program.source.in_(sources))

    if deadline_from:
        stmt = stmt.where(Program.application_end >= datetime.combine(deadline_from, datetime.min.time()))

    if deadline_to:
        stmt = stmt.where(Program.application_end <= datetime.combine(deadline_to, datetime.max.time()))

    # Full-text / trigram search
    if q and len(q) >= 2:
        stmt = stmt.where(
            or_(
                func.similarity(Program.title, q) > 0.15,
                func.word_similarity(q, Program.title) > 0.3,
                func.similarity(Program.description, q) > 0.1,
                Program.title.ilike(f"%{q}%"),
            )
        )

    return stmt


def _apply_sort(stmt: Select, sort: str, q: str | None) -> Select:
    """정렬 적용."""
    if q and len(q) >= 2:
        # 검색어가 있으면 기본 정렬은 유사도순
        relevance = (
            func.similarity(Program.title, q) * 2
            + func.word_similarity(q, Program.title)
        )
        if sort == "deadline_asc":
            stmt = stmt.order_by(Program.application_end.asc().nullslast())
        elif sort == "deadline_desc":
            stmt = stmt.order_by(Program.application_end.desc().nullslast())
        elif sort == "amount_desc":
            stmt = stmt.order_by(Program.support_amount_max.desc().nullslast())
        elif sort == "popular":
            stmt = stmt.order_by(desc(Program.view_count))
        else:
            # default for search: relevance
            stmt = stmt.order_by(desc(relevance), Program.created_at.desc())
    else:
        if sort == "deadline_asc":
            stmt = stmt.order_by(Program.application_end.asc().nullslast())
        elif sort == "deadline_desc":
            stmt = stmt.order_by(Program.application_end.desc().nullslast())
        elif sort == "amount_desc":
            stmt = stmt.order_by(Program.support_amount_max.desc().nullslast())
        elif sort == "popular":
            stmt = stmt.order_by(desc(Program.view_count))
        else:
            # default: created_desc
            stmt = stmt.order_by(Program.created_at.desc())

    return stmt


async def _get_facets(db: AsyncSession, cache_key: str) -> FilterFacets:
    """필터 facet 카운트를 반환한다 (캐시 5분)."""
    cached = _facet_cache.get(cache_key)
    if cached is not None:
        return cached

    # 카테고리별
    cat_q = await db.execute(
        select(Program.category, func.count())
        .where(Program.category.is_not(None))
        .group_by(Program.category)
        .order_by(func.count().desc())
    )
    categories = [FacetItem(name=r[0], count=r[1]) for r in cat_q.all()]

    # 지역별
    reg_q = await db.execute(
        select(Program.region, func.count())
        .where(Program.region.is_not(None))
        .group_by(Program.region)
        .order_by(func.count().desc())
    )
    regions = [FacetItem(name=r[0], count=r[1]) for r in reg_q.all()]

    # 소스별
    src_q = await db.execute(
        select(Program.source, func.count())
        .group_by(Program.source)
        .order_by(func.count().desc())
    )
    sources = [FacetItem(name=r[0], count=r[1]) for r in src_q.all()]

    facets = FilterFacets(categories=categories, regions=regions, sources=sources)
    _facet_cache[cache_key] = facets
    return facets


async def _increment_view_count(program_id: UUID, db: AsyncSession) -> None:
    """조회수 비동기 증가."""
    await db.execute(
        update(Program)
        .where(Program.id == program_id)
        .values(view_count=Program.view_count + 1)
    )
    await db.commit()


# ---------------------------------------------------------------------------
# GET /programs — 목록
# ---------------------------------------------------------------------------


@router.get("", response_model=ProgramListResponse)
async def list_programs(
    q: str | None = Query(None, min_length=2, description="키워드 검색"),
    category: list[str] | None = Query(None, description="카테고리 필터 (복수)"),
    region: list[str] | None = Query(None, description="지역 필터 (복수)"),
    status: ProgramStatus | None = Query(ProgramStatus.OPEN, description="상태"),
    target_type: str | None = Query(None),
    amount_min: int | None = Query(None, ge=0, description="최소 금액 (만원)"),
    amount_max: int | None = Query(None, ge=0, description="최대 금액 (만원)"),
    source: list[str] | None = Query(None, description="소스 필터 (복수)"),
    deadline_from: date | None = Query(None),
    deadline_to: date | None = Query(None),
    sort: str = Query("created_desc", description="정렬"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # --- count ---
    count_stmt = select(func.count()).select_from(Program)
    count_stmt = _apply_filters(
        count_stmt, q=q, categories=category, regions=region,
        status=status, target_type=target_type,
        amount_min=amount_min, amount_max=amount_max,
        sources=source, deadline_from=deadline_from, deadline_to=deadline_to,
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # --- items ---
    stmt = select(*_LIST_COLUMNS)
    stmt = _apply_filters(
        stmt, q=q, categories=category, regions=region,
        status=status, target_type=target_type,
        amount_min=amount_min, amount_max=amount_max,
        sources=source, deadline_from=deadline_from, deadline_to=deadline_to,
    )
    stmt = _apply_sort(stmt, sort, q)
    stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    items = [ProgramListItem.model_validate(row) for row in result.all()]

    # --- facets (별도 쿼리, 캐시) ---
    facets = await _get_facets(db, cache_key="facets_global")

    total_pages = (total + limit - 1) // limit if total else 0

    return ProgramListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=facets,
    )


# ---------------------------------------------------------------------------
# GET /programs/calendar
# ---------------------------------------------------------------------------


@router.get("/calendar", response_model=list[CalendarDayEntry])
async def program_calendar(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    result = await db.execute(
        select(
            func.date(Program.application_end).label("deadline_date"),
            Program.id,
            Program.title,
            Program.organization,
        )
        .where(
            Program.application_end >= start,
            Program.application_end < end,
            Program.application_end.is_not(None),
        )
        .order_by(func.date(Program.application_end), Program.title)
    )
    rows = result.all()

    # Group by date
    day_map: dict[date, list[CalendarProgramItem]] = {}
    for row in rows:
        d = row.deadline_date
        if d not in day_map:
            day_map[d] = []
        day_map[d].append(
            CalendarProgramItem(id=row.id, title=row.title, organization=row.organization)
        )

    return [
        CalendarDayEntry(date=d, count=len(progs), programs=progs)
        for d, progs in sorted(day_map.items())
    ]


# ---------------------------------------------------------------------------
# GET /programs/stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=ProgramStats)
async def program_stats(db: AsyncSession = Depends(get_db)):
    cached = _stats_cache.get("stats")
    if cached is not None:
        return cached

    now = datetime.now()
    week_end = now + timedelta(days=7)

    agg = (await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Program.status == ProgramStatus.OPEN).label("open_count"),
            func.count().filter(
                and_(
                    Program.application_end >= now,
                    Program.application_end <= week_end,
                    Program.status == ProgramStatus.OPEN,
                )
            ).label("closing_this_week"),
        ).select_from(Program)
    )).one()

    cat_rows = (await db.execute(
        select(Program.category, func.count())
        .where(Program.category.is_not(None))
        .group_by(Program.category)
        .order_by(func.count().desc())
    )).all()

    src_rows = (await db.execute(
        select(Program.source, func.count())
        .group_by(Program.source)
        .order_by(func.count().desc())
    )).all()

    stats = ProgramStats(
        total=agg.total,
        open_count=agg.open_count,
        closing_this_week=agg.closing_this_week,
        by_category=[CategoryStat(category=r[0], count=r[1]) for r in cat_rows],
        by_source=[SourceStat(source=r[0], count=r[1]) for r in src_rows],
    )
    _stats_cache["stats"] = stats
    return stats


# ---------------------------------------------------------------------------
# GET /programs/{id} — 상세
# ---------------------------------------------------------------------------


@router.get("/{program_id}", response_model=ProgramDetailResponse)
async def get_program(
    program_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # view_count 비동기 증가
    background_tasks.add_task(_increment_view_count, program_id, db)

    # 관련 사업 3건 (같은 category + region, 자기 자신 제외)
    related_stmt = (
        select(
            Program.id, Program.title, Program.organization,
            Program.application_end, Program.status,
        )
        .where(
            Program.id != program_id,
            Program.status == ProgramStatus.OPEN,
        )
    )
    # 같은 카테고리 우선, 같은 지역 보조
    if program.category:
        related_stmt = related_stmt.where(Program.category == program.category)
    if program.region:
        related_stmt = related_stmt.order_by(
            case((Program.region == program.region, 0), else_=1),
            Program.application_end.asc().nullslast(),
        )
    else:
        related_stmt = related_stmt.order_by(Program.application_end.asc().nullslast())

    related_stmt = related_stmt.limit(3)
    related_rows = (await db.execute(related_stmt)).all()
    related = [ProgramRelated.model_validate(r) for r in related_rows]

    resp = ProgramDetailResponse.model_validate(program)
    resp.related = related
    return resp
