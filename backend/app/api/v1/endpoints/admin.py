"""관리자 API — 대시보드 통계, 크롤링 관리, 사용자/공고 CRUD

인증: X-Admin-Key 헤더 (SECRET_KEY 매칭)
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.crawl_log import CrawlLog
from app.models.program import Program, ProgramStatus
from app.models.user import User
from app.models.subscriber import Subscriber
from app.schemas.crawl_log import CrawlLogResponse
from app.schemas.program import ProgramCreate, ProgramResponse, ProgramUpdate
from app.schemas.user import UserResponse
from app.services.crawler_service import (
    run_bizinfo_crawl,
    run_kstartup_crawl,
    run_thinkcontest_crawl,
    run_wevity_crawl,
    update_expired_statuses,
    find_cross_source_duplicates,
)
from app.services.ai_service import summarize_program

router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_admin_key(x_admin_key: str = Header(...)) -> str:
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return x_admin_key


# ── Crawl triggers ──────────────────────────────────────────────

@router.post("/crawl/bizinfo", response_model=CrawlLogResponse)
async def trigger_bizinfo_crawl(_: str = Depends(verify_admin_key)):
    return await run_bizinfo_crawl()


@router.post("/crawl/kstartup", response_model=CrawlLogResponse)
async def trigger_kstartup_crawl(_: str = Depends(verify_admin_key)):
    return await run_kstartup_crawl()


@router.post("/crawl/thinkcontest", response_model=CrawlLogResponse)
async def trigger_thinkcontest_crawl(_: str = Depends(verify_admin_key)):
    return await run_thinkcontest_crawl()


@router.post("/crawl/wevity", response_model=CrawlLogResponse)
async def trigger_wevity_crawl(_: str = Depends(verify_admin_key)):
    return await run_wevity_crawl()


@router.get("/crawl/logs", response_model=list[CrawlLogResponse])
async def get_crawl_logs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    result = await db.execute(
        select(CrawlLog).order_by(desc(CrawlLog.started_at)).limit(limit)
    )
    return [CrawlLogResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/crawl/update-status")
async def trigger_update_status(_: str = Depends(verify_admin_key)):
    count = await update_expired_statuses()
    return {"updated_count": count}


@router.get("/crawl/duplicates")
async def get_duplicates(_: str = Depends(verify_admin_key)):
    return await find_cross_source_duplicates()


# ── Dashboard stats ─────────────────────────────────────────────


class AdminStats(BaseModel):
    total_programs: int
    programs_by_status: dict[str, int]
    programs_by_source: list[dict]
    programs_by_category: list[dict]
    today_new: int
    today_updated: int
    total_users: int
    today_new_users: int
    total_subscribers: int
    recent_crawl_logs: list[CrawlLogResponse]


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Programs aggregate
    total = (await db.execute(select(func.count()).select_from(Program))).scalar() or 0

    status_rows = (await db.execute(
        select(Program.status, func.count()).group_by(Program.status)
    )).all()
    by_status = {r[0]: r[1] for r in status_rows}

    source_rows = (await db.execute(
        select(Program.source, func.count()).group_by(Program.source).order_by(desc(func.count()))
    )).all()
    by_source = [{"source": r[0], "count": r[1]} for r in source_rows]

    cat_rows = (await db.execute(
        select(Program.category, func.count())
        .where(Program.category.is_not(None))
        .group_by(Program.category)
        .order_by(desc(func.count()))
    )).all()
    by_category = [{"category": r[0], "count": r[1]} for r in cat_rows]

    # Today crawl stats
    today_logs = (await db.execute(
        select(
            func.coalesce(func.sum(CrawlLog.new_count), 0).label("new"),
            func.coalesce(func.sum(CrawlLog.updated_count), 0).label("updated"),
        )
        .where(CrawlLog.started_at >= today_start)
    )).one()

    # Users
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    today_users = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )).scalar() or 0

    # Subscribers
    total_subs = (await db.execute(
        select(func.count()).select_from(Subscriber).where(Subscriber.is_active.is_(True))
    )).scalar() or 0

    # Recent logs
    logs_result = await db.execute(
        select(CrawlLog).order_by(desc(CrawlLog.started_at)).limit(10)
    )
    recent_logs = [CrawlLogResponse.model_validate(r) for r in logs_result.scalars().all()]

    return AdminStats(
        total_programs=total,
        programs_by_status=by_status,
        programs_by_source=by_source,
        programs_by_category=by_category,
        today_new=today_logs.new,
        today_updated=today_logs.updated,
        total_users=total_users,
        today_new_users=today_users,
        total_subscribers=total_subs,
        recent_crawl_logs=recent_logs,
    )


# ── Users management ────────────────────────────────────────────


class UserListItem(BaseModel):
    id: str
    email: str
    name: str | None
    provider: str
    is_premium: bool
    profile: dict | None
    created_at: datetime


class UserPatch(BaseModel):
    is_premium: bool | None = None
    name: str | None = None


@router.get("/users", response_model=list[UserListItem])
async def list_users(
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    result = await db.execute(
        select(User).order_by(desc(User.created_at)).offset(offset).limit(limit)
    )
    return [
        UserListItem(
            id=str(u.id), email=u.email, name=u.name, provider=u.provider,
            is_premium=u.is_premium, profile=u.profile, created_at=u.created_at,
        )
        for u in result.scalars().all()
    ]


@router.patch("/users/{user_id}", response_model=UserListItem)
async def patch_user(
    user_id: UUID,
    body: UserPatch,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.is_premium is not None:
        user.is_premium = body.is_premium
    if body.name is not None:
        user.name = body.name
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserListItem(
        id=str(user.id), email=user.email, name=user.name, provider=user.provider,
        is_premium=user.is_premium, profile=user.profile, created_at=user.created_at,
    )


# ── Programs management ─────────────────────────────────────────


@router.get("/programs", response_model=list[ProgramResponse])
async def list_admin_programs(
    limit: int = Query(20, le=100),
    offset: int = 0,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    stmt = select(Program).order_by(desc(Program.created_at))
    if q:
        stmt = stmt.where(Program.title.ilike(f"%{q}%"))
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return [ProgramResponse.model_validate(p) for p in result.scalars().all()]


@router.post("/programs", response_model=ProgramResponse, status_code=201)
async def create_program(
    body: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    program = Program(**body.model_dump())
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return ProgramResponse.model_validate(program)


@router.put("/programs/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: UUID,
    body: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(program, field, value)
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return ProgramResponse.model_validate(program)


@router.delete("/programs/{program_id}", status_code=204)
async def delete_program(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    await db.delete(program)
    await db.commit()


@router.post("/programs/{program_id}/regenerate-summary")
async def regenerate_summary(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    # Clear existing summary to force regeneration
    program.summary = None
    db.add(program)
    await db.commit()
    summary = await summarize_program(program)
    return {"summary": summary}
