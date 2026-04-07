"""K-Startup(창업진흥원) 창업지원사업 통합공고 API 크롤러

data.go.kr '창업진흥원 창업지원사업 통합공고 API'를 사용합니다.
기업마당과 유사한 구조이나 창업 특화 필드(사업단계, 지원유형 등)를 추가 처리합니다.
"""

import asyncio
import logging
from datetime import datetime

import httpx

from app.config import settings
from app.database import async_session
from app.models.program import SourceType
from app.models.crawl_log import CrawlLog, CrawlStatus
from app.schemas.program import ProgramCreate
from app.crawlers.utils import (
    normalize_category,
    normalize_region,
    parse_date,
    determine_status,
    extract_max_amount,
    build_tags,
    upsert_programs,
)

logger = logging.getLogger(__name__)

BASE_URL = "http://apis.data.go.kr/B552735/k-startup/kisedStrtupSupport"
PER_PAGE = 100
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0
REQUEST_INTERVAL = 0.5

# K-Startup 사업단계 → target_type 매핑
BIZ_STAGE_MAP: dict[str, str] = {
    "예비창업자": "예비창업자",
    "예비 창업자": "예비창업자",
    "1년미만": "1년이내",
    "1년이내": "1년이내",
    "3년미만": "3년이내",
    "3년이내": "3년이내",
    "5년이내": "7년이내",
    "7년미만": "7년이내",
    "7년이내": "7년이내",
    "제한없음": "제한없음",
    "무관": "제한없음",
}

# K-Startup 지원유형 → 카테고리 보조 매핑
SUPPORT_TYPE_MAP: dict[str, str] = {
    "사업화자금": "창업",
    "시설공간": "시설/공간",
    "멘토링컨설팅": "컨설팅",
    "R&D": "R&D",
    "판로마케팅": "마케팅",
    "인력": "인력",
    "융자": "금융/투자",
    "투자": "금융/투자",
    "교육": "창업",
}


def _normalize_biz_stage(raw: str | None) -> str | None:
    if not raw:
        return None
    for keyword, mapped in BIZ_STAGE_MAP.items():
        if keyword in raw:
            return mapped
    return raw


def _normalize_support_type_category(raw: str | None) -> str | None:
    """지원유형 문자열로 카테고리를 보조 추정한다."""
    if not raw:
        return None
    for keyword, cat in SUPPORT_TYPE_MAP.items():
        if keyword in raw:
            return cat
    return None


class KStartupCrawler:
    """K-Startup 창업지원사업 통합공고 API 크롤러"""

    def __init__(self) -> None:
        self.api_key = settings.DATA_GO_KR_API_KEY

    async def _request(self, client: httpx.AsyncClient, page: int) -> dict:
        params = {
            "page": page,
            "perPage": PER_PAGE,
            "serviceKey": self.api_key,
        }
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(BASE_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and data.get("resultCode") and data["resultCode"] != "00":
                    raise ValueError(f"API error: {data.get('resultMsg', data)}")
                return data
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                wait = RETRY_BACKOFF * (2 ** attempt)
                logger.warning(
                    "KStartup API failed (attempt %d/%d): %s — retry in %.1fs",
                    attempt + 1, MAX_RETRIES, exc, wait,
                )
                await asyncio.sleep(wait)
        raise RuntimeError(f"KStartup API failed after {MAX_RETRIES} retries: {last_exc}")

    async def fetch_all(self) -> list[dict]:
        all_items: list[dict] = []
        async with httpx.AsyncClient() as client:
            first = await self._request(client, page=1)
            total_count = first.get("totalCount", 0)
            items = first.get("data", [])
            if isinstance(items, list):
                all_items.extend(items)

            total_pages = (total_count + PER_PAGE - 1) // PER_PAGE if total_count else 0
            logger.info("KStartup: totalCount=%d, totalPages=%d", total_count, total_pages)

            for page in range(2, total_pages + 1):
                await asyncio.sleep(REQUEST_INTERVAL)
                data = await self._request(client, page=page)
                page_items = data.get("data", [])
                if isinstance(page_items, list):
                    all_items.extend(page_items)

        logger.info("KStartup: fetched %d items total", len(all_items))
        return all_items

    def parse_program(self, raw: dict) -> ProgramCreate:
        source_id = str(
            raw.get("pblancId") or raw.get("bizPblancId")
            or raw.get("id") or hash(raw.get("pblancNm", ""))
        )
        title = raw.get("pblancNm") or raw.get("bizPblancNm") or ""
        organization = raw.get("jrsdInsttNm") or raw.get("excInsttNm") or None

        # 카테고리: 분야명 우선, 없으면 지원유형으로 추정
        raw_category = raw.get("pldirSportRealmLclsNm") or raw.get("sportRealmLclsNm") or ""
        support_type_raw = raw.get("sprtTypNm") or ""
        category = normalize_category(raw_category)
        if category == "기타" and support_type_raw:
            inferred = _normalize_support_type_category(support_type_raw)
            if inferred:
                category = inferred

        sub_category = raw.get("pldirSportRealmMclsNm") or raw.get("sportRealmMclsNm") or None
        raw_region = raw.get("jrsdInsttNm") or ""
        region = normalize_region(raw_region)

        # 사업단계 → target_type
        biz_stage_raw = raw.get("bizEnyy") or raw.get("trgetNm") or None
        target_type = _normalize_biz_stage(biz_stage_raw)

        support_amount_text = raw.get("sprtAmt") or raw.get("sportCn") or None
        app_start = parse_date(raw.get("reqstBeginDe") or raw.get("pblancRcptBgnde"))
        app_end = parse_date(raw.get("reqstEndDe") or raw.get("pblancRcptEndde"))
        detail_url = raw.get("detailUrl") or raw.get("pblancUrl") or None
        description = raw.get("bsnsSumryCn") or raw.get("sportCn") or None
        eligibility = raw.get("trgetCn") or None

        status = determine_status(app_start, app_end)
        amount_max = extract_max_amount(support_amount_text)
        tags = build_tags(
            category if category != "기타" else None,
            sub_category,
            target_type,
            support_type_raw if support_type_raw else None,
        )

        return ProgramCreate(
            source=SourceType.KSTARTUP,
            source_id=source_id,
            title=title.strip(),
            organization=organization,
            category=category,
            sub_category=sub_category,
            region=region,
            target_type=target_type,
            support_amount=support_amount_text,
            support_amount_max=amount_max,
            application_start=app_start,
            application_end=app_end,
            status=status,
            description=description,
            eligibility=eligibility,
            detail_url=detail_url,
            raw_data=raw,
            tags=tags,
        )

    async def run(self) -> CrawlLog:
        async with async_session() as session:
            log = CrawlLog(source="KSTARTUP", status=CrawlStatus.RUNNING)
            session.add(log)
            await session.commit()
            await session.refresh(log)

            errors: list[str] = []
            try:
                raw_items = await self.fetch_all()

                programs: list[ProgramCreate] = []
                for item in raw_items:
                    try:
                        programs.append(self.parse_program(item))
                    except Exception as e:
                        errors.append(f"Parse error: {e}")
                        logger.warning("Failed to parse KStartup item: %s", e)

                new_count, updated_count = await upsert_programs(session, programs)

                log.total_fetched = len(raw_items)
                log.new_count = new_count
                log.updated_count = updated_count
                log.error_count = len(errors)
                log.error_detail = "\n".join(errors) if errors else None
                log.status = CrawlStatus.SUCCESS
                log.finished_at = datetime.now()

            except Exception as e:
                logger.exception("KStartup crawl failed: %s", e)
                log.status = CrawlStatus.FAILED
                log.error_count = len(errors) + 1
                errors.append(f"Fatal: {e}")
                log.error_detail = "\n".join(errors)
                log.finished_at = datetime.now()

            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log
