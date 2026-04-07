"""기업마당(bizinfo.go.kr) Open API 크롤러

공공데이터포털의 '중소기업 지원사업 통합공고 조회 API'를 통해
지원사업 공고를 수집하고 DB에 upsert합니다.
"""

import asyncio
import logging
import re
from datetime import datetime
from urllib.parse import quote

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.program import SourceType, ProgramStatus
from app.models.crawl_log import CrawlLog, CrawlStatus
from app.schemas.program import ProgramCreate

logger = logging.getLogger(__name__)

BASE_URL = "http://apis.data.go.kr/B552735/k-startup/kisedGovSupport"
PER_PAGE = 100
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds — doubles each retry
REQUEST_INTERVAL = 0.5  # seconds between page requests

# ---------------------------------------------------------------------------
# 카테고리 & 지역 매핑
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {
    "창업사업화": "창업",
    "창업교육": "창업",
    "창업": "창업",
    "기술개발": "R&D",
    "연구개발": "R&D",
    "R&D": "R&D",
    "수출": "수출",
    "해외진출": "수출",
    "마케팅": "마케팅",
    "판로": "마케팅",
    "인력": "인력",
    "고용": "인력",
    "시설": "시설/공간",
    "공간": "시설/공간",
    "입주": "시설/공간",
    "금융": "금융/투자",
    "투자": "금융/투자",
    "융자": "금융/투자",
    "보증": "금융/투자",
    "컨설팅": "컨설팅",
    "멘토링": "컨설팅",
}

REGION_NAMES = [
    "전국", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]

# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(r"(\d[\d,]*)\s*(억|만|천만|백만)")

_UNIT_MAP = {
    "억": 10000,  # 1억 = 10000만원
    "천만": 1000,
    "백만": 100,
    "만": 1,
}


def _extract_max_amount(text_val: str | None) -> int | None:
    """지원금액 텍스트에서 최대 금액(만원 단위)을 추출한다."""
    if not text_val:
        return None
    amounts: list[int] = []
    for match in _AMOUNT_RE.finditer(text_val):
        num = int(match.group(1).replace(",", ""))
        unit = match.group(2)
        amounts.append(num * _UNIT_MAP.get(unit, 1))
    return max(amounts) if amounts else None


def _normalize_category(raw: str | None) -> str:
    """기업마당 분야 → 정규 카테고리"""
    if not raw:
        return "기타"
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in raw:
            return cat
    return "기타"


def _normalize_region(raw: str | None) -> str:
    """시도명 기준 정규화"""
    if not raw:
        return "전국"
    for region in REGION_NAMES:
        if region in raw:
            return region
    return "전국"


def _parse_date(val: str | None) -> datetime | None:
    """다양한 날짜 형식을 파싱한다."""
    if not val:
        return None
    val = val.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def _determine_status(start: datetime | None, end: datetime | None) -> ProgramStatus:
    now = datetime.now()
    if end and end < now:
        return ProgramStatus.CLOSED
    if start and start > now:
        return ProgramStatus.UPCOMING
    return ProgramStatus.OPEN


# ---------------------------------------------------------------------------
# 크롤러
# ---------------------------------------------------------------------------


class BizinfoCrawler:
    """기업마당 API 크롤러"""

    def __init__(self) -> None:
        self.api_key = settings.DATA_GO_KR_API_KEY

    # ----- HTTP helpers -----

    async def _request(
        self, client: httpx.AsyncClient, page: int
    ) -> dict:
        """단일 페이지 요청 (재시도 포함)."""
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
                # 공공데이터포털 에러 응답 체크
                if isinstance(data, dict) and data.get("resultCode") and data["resultCode"] != "00":
                    raise ValueError(f"API error: {data.get('resultMsg', data)}")
                return data
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                wait = RETRY_BACKOFF * (2 ** attempt)
                logger.warning(
                    "BizInfo API request failed (attempt %d/%d): %s — retrying in %.1fs",
                    attempt + 1, MAX_RETRIES, exc, wait,
                )
                await asyncio.sleep(wait)
        raise RuntimeError(
            f"BizInfo API failed after {MAX_RETRIES} retries: {last_exc}"
        )

    # ----- fetch -----

    async def fetch_all(self) -> list[dict]:
        """전체 공고 수집 (페이지네이션 처리)."""
        all_items: list[dict] = []
        async with httpx.AsyncClient() as client:
            # 1) 첫 페이지로 totalCount 확인
            first = await self._request(client, page=1)
            total_count = first.get("totalCount", 0)
            items = first.get("data", [])
            if isinstance(items, list):
                all_items.extend(items)
            else:
                logger.warning("Unexpected 'data' field type: %s", type(items))

            total_pages = (total_count + PER_PAGE - 1) // PER_PAGE if total_count else 0
            logger.info(
                "BizInfo: totalCount=%d, totalPages=%d", total_count, total_pages
            )

            # 2) 나머지 페이지 순회
            for page in range(2, total_pages + 1):
                await asyncio.sleep(REQUEST_INTERVAL)
                data = await self._request(client, page=page)
                page_items = data.get("data", [])
                if isinstance(page_items, list):
                    all_items.extend(page_items)

        logger.info("BizInfo: fetched %d items total", len(all_items))
        return all_items

    # ----- parse -----

    def parse_program(self, raw: dict) -> ProgramCreate:
        """API 응답 단건을 ProgramCreate 스키마로 변환."""
        source_id = str(
            raw.get("pblancId")
            or raw.get("bizPblancId")
            or raw.get("id")
            or hash(raw.get("pblancNm", ""))
        )

        title = raw.get("pblancNm") or raw.get("bizPblancNm") or ""
        organization = raw.get("jrsdInsttNm") or raw.get("excInsttNm") or None
        raw_category = raw.get("pldirSportRealmLclsNm") or raw.get("sportRealmLclsNm") or ""
        sub_category = raw.get("pldirSportRealmMclsNm") or raw.get("sportRealmMclsNm") or None
        raw_region = raw.get("jrsdInsttNm") or ""
        target_type = raw.get("trgetNm") or None
        support_amount_text = raw.get("sprtAmt") or raw.get("sportCn") or None

        app_start = _parse_date(raw.get("reqstBeginDe") or raw.get("pblancRcptBgnde"))
        app_end = _parse_date(raw.get("reqstEndDe") or raw.get("pblancRcptEndde"))

        detail_url = raw.get("detailUrl") or raw.get("pblancUrl") or None
        description = raw.get("bsnsSumryCn") or raw.get("sportCn") or None
        eligibility = raw.get("trgetCn") or raw.get("jrsdInsttNm") or None

        category = _normalize_category(raw_category)
        region = _normalize_region(raw_region)
        status = _determine_status(app_start, app_end)
        amount_max = _extract_max_amount(support_amount_text)

        # 태그 생성 (중복 제거, 순서 유지)
        seen: set[str] = set()
        tags: list[str] = []
        for t in [category if category != "기타" else None, sub_category, target_type]:
            if t and t not in seen:
                tags.append(t)
                seen.add(t)

        return ProgramCreate(
            source=SourceType.BIZINFO,
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
            tags=tags or None,
        )

    # ----- upsert -----

    async def upsert_programs(
        self, session: AsyncSession, programs: list[ProgramCreate]
    ) -> tuple[int, int]:
        """DB에 upsert. (new_count, updated_count) 반환."""
        new_count = 0
        updated_count = 0

        for prog in programs:
            result = await session.execute(
                text("""
                    INSERT INTO programs (
                        id, source, source_id, title, organization,
                        category, sub_category, region, target_type,
                        support_amount, support_amount_max,
                        application_start, application_end, status,
                        description, eligibility, detail_url,
                        raw_data, tags, view_count,
                        created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), :source, :source_id, :title, :organization,
                        :category, :sub_category, :region, :target_type,
                        :support_amount, :support_amount_max,
                        :application_start, :application_end, :status,
                        :description, :eligibility, :detail_url,
                        :raw_data, :tags, 0,
                        now(), now()
                    )
                    ON CONFLICT (source, source_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        organization = EXCLUDED.organization,
                        category = EXCLUDED.category,
                        sub_category = EXCLUDED.sub_category,
                        region = EXCLUDED.region,
                        target_type = EXCLUDED.target_type,
                        support_amount = EXCLUDED.support_amount,
                        support_amount_max = EXCLUDED.support_amount_max,
                        application_start = EXCLUDED.application_start,
                        application_end = EXCLUDED.application_end,
                        status = EXCLUDED.status,
                        description = EXCLUDED.description,
                        eligibility = EXCLUDED.eligibility,
                        detail_url = EXCLUDED.detail_url,
                        raw_data = EXCLUDED.raw_data,
                        tags = EXCLUDED.tags,
                        updated_at = now()
                    RETURNING (xmax = 0) AS is_insert
                """),
                {
                    "source": prog.source.value,
                    "source_id": prog.source_id,
                    "title": prog.title,
                    "organization": prog.organization,
                    "category": prog.category,
                    "sub_category": prog.sub_category,
                    "region": prog.region,
                    "target_type": prog.target_type,
                    "support_amount": prog.support_amount,
                    "support_amount_max": prog.support_amount_max,
                    "application_start": prog.application_start,
                    "application_end": prog.application_end,
                    "status": prog.status.value,
                    "description": prog.description,
                    "eligibility": prog.eligibility,
                    "detail_url": prog.detail_url,
                    "raw_data": prog.raw_data,
                    "tags": prog.tags,
                },
            )
            row = result.fetchone()
            if row and row.is_insert:
                new_count += 1
            else:
                updated_count += 1

        await session.commit()
        return new_count, updated_count

    # ----- run -----

    async def run(self) -> CrawlLog:
        """전체 크롤링 실행 + 로그 기록."""
        async with async_session() as session:
            # 로그 생성
            log = CrawlLog(source="BIZINFO", status=CrawlStatus.RUNNING)
            session.add(log)
            await session.commit()
            await session.refresh(log)

            errors: list[str] = []
            try:
                raw_items = await self.fetch_all()

                # 파싱
                programs: list[ProgramCreate] = []
                for item in raw_items:
                    try:
                        programs.append(self.parse_program(item))
                    except Exception as e:
                        errors.append(f"Parse error: {e}")
                        logger.warning("Failed to parse item: %s", e)

                # upsert
                new_count, updated_count = await self.upsert_programs(session, programs)

                log.total_fetched = len(raw_items)
                log.new_count = new_count
                log.updated_count = updated_count
                log.error_count = len(errors)
                log.error_detail = "\n".join(errors) if errors else None
                log.status = CrawlStatus.SUCCESS
                log.finished_at = datetime.now()

            except Exception as e:
                logger.exception("BizInfo crawl failed: %s", e)
                log.status = CrawlStatus.FAILED
                log.error_count = len(errors) + 1
                errors.append(f"Fatal: {e}")
                log.error_detail = "\n".join(errors)
                log.finished_at = datetime.now()

            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log
