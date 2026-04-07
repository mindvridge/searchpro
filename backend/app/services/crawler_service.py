"""크롤러 실행 서비스 레이어"""

import logging
from datetime import datetime

from sqlalchemy import text, update

from app.crawlers.bizinfo import BizinfoCrawler
from app.crawlers.kstartup import KStartupCrawler
from app.database import async_session
from app.models.crawl_log import CrawlLog
from app.models.program import Program, ProgramStatus
from app.schemas.crawl_log import CrawlLogResponse

logger = logging.getLogger(__name__)


async def run_bizinfo_crawl() -> CrawlLogResponse:
    """기업마당 크롤러를 수동 트리거하고 결과 로그를 반환한다."""
    logger.info("Starting BizInfo crawl (manual trigger)")
    crawler = BizinfoCrawler()
    log: CrawlLog = await crawler.run()
    logger.info(
        "BizInfo crawl done — status=%s, fetched=%d, new=%d, updated=%d, errors=%d",
        log.status, log.total_fetched, log.new_count, log.updated_count, log.error_count,
    )
    return CrawlLogResponse.model_validate(log)


async def run_kstartup_crawl() -> CrawlLogResponse:
    """K-Startup 크롤러를 수동 트리거하고 결과 로그를 반환한다."""
    logger.info("Starting KStartup crawl (manual trigger)")
    crawler = KStartupCrawler()
    log: CrawlLog = await crawler.run()
    logger.info(
        "KStartup crawl done — status=%s, fetched=%d, new=%d, updated=%d, errors=%d",
        log.status, log.total_fetched, log.new_count, log.updated_count, log.error_count,
    )
    return CrawlLogResponse.model_validate(log)


async def update_expired_statuses() -> int:
    """마감일이 지난 공고의 상태를 CLOSED로 일괄 갱신한다. 변경 건수를 반환."""
    async with async_session() as session:
        result = await session.execute(
            update(Program)
            .where(Program.application_end < datetime.now())
            .where(Program.status != ProgramStatus.CLOSED)
            .values(status=ProgramStatus.CLOSED, updated_at=datetime.now())
        )
        await session.commit()
        count = result.rowcount
        logger.info("Updated %d programs to CLOSED status", count)
        return count


async def find_cross_source_duplicates() -> list[dict]:
    """기업마당 ↔ K-Startup 간 중복 의심 공고를 찾는다.

    pg_trgm similarity > 0.8 기준으로 title + organization이 유사한 쌍을 반환.
    기업마당 버전을 우선(더 포괄적)으로 표시한다.
    """
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT
                a.id AS bizinfo_id,
                a.title AS bizinfo_title,
                b.id AS kstartup_id,
                b.title AS kstartup_title,
                similarity(a.title, b.title) AS title_sim
            FROM programs a
            JOIN programs b
                ON a.source = 'BIZINFO'
                AND b.source = 'KSTARTUP'
                AND similarity(a.title, b.title) > 0.8
            ORDER BY title_sim DESC
            LIMIT 100
        """))
        rows = result.fetchall()
        return [
            {
                "bizinfo_id": str(r.bizinfo_id),
                "bizinfo_title": r.bizinfo_title,
                "kstartup_id": str(r.kstartup_id),
                "kstartup_title": r.kstartup_title,
                "similarity": round(float(r.title_sim), 3),
            }
            for r in rows
        ]
