"""관리용 API 엔드포인트 — 크롤링 트리거, 로그 조회, 상태 갱신

인증: 간단한 API Key 방식 (X-Admin-Key 헤더)
추후 JWT 관리자 인증으로 교체 예정.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.crawl_log import CrawlLog
from app.schemas.crawl_log import CrawlLogResponse
from app.services.crawler_service import (
    run_bizinfo_crawl,
    run_kstartup_crawl,
    update_expired_statuses,
    find_cross_source_duplicates,
)

router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_admin_key(x_admin_key: str = Header(...)) -> str:
    """간단한 API Key 인증. SECRET_KEY와 동일한 값을 사용."""
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return x_admin_key


@router.post("/crawl/bizinfo", response_model=CrawlLogResponse)
async def trigger_bizinfo_crawl(_: str = Depends(verify_admin_key)):
    """기업마당 수동 크롤링 트리거"""
    return await run_bizinfo_crawl()


@router.post("/crawl/kstartup", response_model=CrawlLogResponse)
async def trigger_kstartup_crawl(_: str = Depends(verify_admin_key)):
    """K-Startup 수동 크롤링 트리거"""
    return await run_kstartup_crawl()


@router.get("/crawl/logs", response_model=list[CrawlLogResponse])
async def get_crawl_logs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    """크롤링 로그 조회 (최신순)"""
    result = await db.execute(
        select(CrawlLog).order_by(desc(CrawlLog.started_at)).limit(limit)
    )
    return [CrawlLogResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/crawl/update-status")
async def trigger_update_status(_: str = Depends(verify_admin_key)):
    """마감 상태 일괄 갱신 (application_end < now → CLOSED)"""
    count = await update_expired_statuses()
    return {"updated_count": count}


@router.get("/crawl/duplicates")
async def get_duplicates(_: str = Depends(verify_admin_key)):
    """기업마당 ↔ K-Startup 간 중복 의심 공고 조회"""
    return await find_cross_source_duplicates()
