"""크롤러 실행 서비스 레이어"""

import logging

from app.crawlers.bizinfo import BizinfoCrawler
from app.models.crawl_log import CrawlLog
from app.schemas.crawl_log import CrawlLogResponse

logger = logging.getLogger(__name__)


async def run_bizinfo_crawl() -> CrawlLogResponse:
    """기업마당 크롤러를 수동 트리거하고 결과 로그를 반환한다."""
    logger.info("Starting BizInfo crawl (manual trigger)")
    crawler = BizinfoCrawler()
    log: CrawlLog = await crawler.run()
    logger.info(
        "BizInfo crawl finished — status=%s, fetched=%d, new=%d, updated=%d, errors=%d",
        log.status,
        log.total_fetched,
        log.new_count,
        log.updated_count,
        log.error_count,
    )
    return CrawlLogResponse.model_validate(log)
