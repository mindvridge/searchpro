"""크롤러 공통 유틸리티

카테고리/지역 정규화, 날짜 파싱, 금액 추출, upsert SQL 등
모든 크롤러가 공유하는 함수를 모아둡니다.
"""

import re
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.program import ProgramStatus
from app.schemas.program import ProgramCreate

# ---------------------------------------------------------------------------
# 카테고리 매핑
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

# ---------------------------------------------------------------------------
# 지역 매핑
# ---------------------------------------------------------------------------

REGION_NAMES = [
    "전국", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]

# ---------------------------------------------------------------------------
# 금액 추출
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(r"(\d[\d,]*)\s*(억|만|천만|백만)")
_UNIT_MAP = {"억": 10000, "천만": 1000, "백만": 100, "만": 1}


def extract_max_amount(text_val: str | None) -> int | None:
    """지원금액 텍스트에서 최대 금액(만원 단위)을 추출한다."""
    if not text_val:
        return None
    amounts: list[int] = []
    for match in _AMOUNT_RE.finditer(text_val):
        num = int(match.group(1).replace(",", ""))
        unit = match.group(2)
        amounts.append(num * _UNIT_MAP.get(unit, 1))
    return max(amounts) if amounts else None


# ---------------------------------------------------------------------------
# 정규화 함수
# ---------------------------------------------------------------------------


def normalize_category(raw: str | None) -> str:
    """원본 분야 문자열 → 정규 카테고리"""
    if not raw:
        return "기타"
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in raw:
            return cat
    return "기타"


def normalize_region(raw: str | None) -> str:
    """시도명 기준 정규화"""
    if not raw:
        return "전국"
    for region in REGION_NAMES:
        if region in raw:
            return region
    return "전국"


# ---------------------------------------------------------------------------
# 날짜 파싱
# ---------------------------------------------------------------------------

_DATE_FORMATS = ("%Y-%m-%d", "%Y%m%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S")


def parse_date(val: str | None) -> datetime | None:
    """다양한 날짜 형식을 파싱한다."""
    if not val:
        return None
    val = val.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# 상태 판별
# ---------------------------------------------------------------------------


def determine_status(start: datetime | None, end: datetime | None) -> ProgramStatus:
    now = datetime.now()
    if end and end < now:
        return ProgramStatus.CLOSED
    if start and start > now:
        return ProgramStatus.UPCOMING
    return ProgramStatus.OPEN


# ---------------------------------------------------------------------------
# 태그 생성
# ---------------------------------------------------------------------------


def build_tags(*values: str | None) -> list[str] | None:
    """중복 제거된 태그 리스트를 생성한다."""
    seen: set[str] = set()
    tags: list[str] = []
    for v in values:
        if v and v not in seen:
            tags.append(v)
            seen.add(v)
    return tags or None


# ---------------------------------------------------------------------------
# 공통 upsert SQL
# ---------------------------------------------------------------------------

_UPSERT_SQL = text("""
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
""")


async def upsert_programs(
    session: AsyncSession, programs: list[ProgramCreate]
) -> tuple[int, int]:
    """DB에 upsert. (new_count, updated_count) 반환."""
    new_count = 0
    updated_count = 0

    for prog in programs:
        result = await session.execute(
            _UPSERT_SQL,
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
