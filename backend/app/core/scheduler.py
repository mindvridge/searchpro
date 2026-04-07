"""APScheduler 통합 — 정기 크롤링 및 상태 갱신 스케줄"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.crawler_service import (
    run_bizinfo_crawl,
    run_kstartup_crawl,
    update_expired_statuses,
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def _register_jobs() -> None:
    # 기업마당 크롤링: 매일 06:00, 18:00 KST
    scheduler.add_job(
        run_bizinfo_crawl,
        CronTrigger(hour="6,18", minute=0, timezone="Asia/Seoul"),
        id="crawl_bizinfo",
        name="BizInfo 크롤링",
        replace_existing=True,
    )

    # K-Startup 크롤링: 매일 07:00, 19:00 KST
    scheduler.add_job(
        run_kstartup_crawl,
        CronTrigger(hour="7,19", minute=0, timezone="Asia/Seoul"),
        id="crawl_kstartup",
        name="KStartup 크롤링",
        replace_existing=True,
    )

    # 마감 상태 갱신: 매일 00:05 KST
    scheduler.add_job(
        update_expired_statuses,
        CronTrigger(hour=0, minute=5, timezone="Asia/Seoul"),
        id="update_expired",
        name="마감 상태 일괄 갱신",
        replace_existing=True,
    )


def start_scheduler() -> None:
    _register_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
