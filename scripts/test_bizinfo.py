#!/usr/bin/env python3
"""기업마당 API 크롤러 연동 테스트 스크립트

API 키가 있으면 실제 API를 호출하고,
없으면 mock 응답으로 파싱 로직을 테스트합니다.

사용법:
    cd backend
    python -m scripts.test_bizinfo          # mock
    DATA_GO_KR_API_KEY=xxx python -m scripts.test_bizinfo   # 실제 호출
"""

import asyncio
import sys
import os

# backend/ 를 파이썬 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from app.crawlers.bizinfo import BizinfoCrawler
from app.crawlers.utils import (
    extract_max_amount as _extract_max_amount,
    normalize_category as _normalize_category,
    normalize_region as _normalize_region,
    determine_status as _determine_status,
    parse_date as _parse_date,
)
from app.models.program import ProgramStatus

# ---------------------------------------------------------------------------
# Mock 응답 데이터
# ---------------------------------------------------------------------------

MOCK_ITEMS = [
    {
        "pblancId": "PBLN_000000000000001",
        "pblancNm": "2026년 예비창업패키지 지원사업",
        "jrsdInsttNm": "중소벤처기업부",
        "excInsttNm": "창업진흥원",
        "pldirSportRealmLclsNm": "창업사업화",
        "pldirSportRealmMclsNm": "예비창업자",
        "trgetNm": "예비창업자",
        "sprtAmt": "최대 1억원",
        "reqstBeginDe": "2026-03-01",
        "reqstEndDe": "2026-04-30",
        "bsnsSumryCn": "혁신적인 기술 창업 아이디어를 보유한 예비창업자를 선발하여 사업화 자금 등을 지원합니다.",
        "trgetCn": "만 39세 이하 예비창업자",
        "detailUrl": "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=PBLN_000000000000001",
    },
    {
        "pblancId": "PBLN_000000000000002",
        "pblancNm": "2026년 수출바우처 지원사업",
        "jrsdInsttNm": "서울특별시",
        "pldirSportRealmLclsNm": "수출",
        "pldirSportRealmMclsNm": "해외마케팅",
        "trgetNm": "중소기업",
        "sprtAmt": "최대 5천만원",
        "reqstBeginDe": "2026-01-15",
        "reqstEndDe": "2026-02-28",
        "bsnsSumryCn": "수출 역량을 강화하기 위한 바우처 지원",
        "trgetCn": "수출 실적이 있는 중소기업",
    },
    {
        "pblancId": "PBLN_000000000000003",
        "pblancNm": "2026년 R&D 기술개발 지원사업",
        "jrsdInsttNm": "경기도",
        "pldirSportRealmLclsNm": "기술개발",
        "sprtAmt": "과제당 3억원 이내",
        "reqstBeginDe": "2026-05-01",
        "reqstEndDe": "2026-06-30",
        "bsnsSumryCn": "중소기업 기술개발 연구비 지원",
    },
]


# ---------------------------------------------------------------------------
# 유닛 테스트: 유틸리티 함수
# ---------------------------------------------------------------------------


def test_extract_max_amount():
    assert _extract_max_amount("최대 1억원") == 10000
    assert _extract_max_amount("최대 5천만원") == 5000
    assert _extract_max_amount("과제당 3억원 이내") == 30000
    assert _extract_max_amount("500만원 ~ 2,000만원") == 2000
    assert _extract_max_amount(None) is None
    assert _extract_max_amount("별도 공지") is None
    print("  [PASS] _extract_max_amount")


def test_normalize_category():
    assert _normalize_category("창업사업화") == "창업"
    assert _normalize_category("기술개발") == "R&D"
    assert _normalize_category("수출") == "수출"
    assert _normalize_category("판로") == "마케팅"
    assert _normalize_category(None) == "기타"
    assert _normalize_category("기타지원") == "기타"
    print("  [PASS] _normalize_category")


def test_normalize_region():
    assert _normalize_region("서울특별시") == "서울"
    assert _normalize_region("경기도") == "경기"
    assert _normalize_region("중소벤처기업부") == "전국"
    assert _normalize_region(None) == "전국"
    print("  [PASS] _normalize_region")


def test_determine_status():
    from datetime import datetime, timedelta
    now = datetime.now()
    assert _determine_status(now - timedelta(days=10), now + timedelta(days=10)) == ProgramStatus.OPEN
    assert _determine_status(now + timedelta(days=5), now + timedelta(days=30)) == ProgramStatus.UPCOMING
    assert _determine_status(now - timedelta(days=30), now - timedelta(days=1)) == ProgramStatus.CLOSED
    print("  [PASS] _determine_status")


def test_parse_date():
    assert _parse_date("2026-03-01") is not None
    assert _parse_date("20260301") is not None
    assert _parse_date("2026.03.01") is not None
    assert _parse_date(None) is None
    assert _parse_date("invalid") is None
    print("  [PASS] _parse_date")


# ---------------------------------------------------------------------------
# Mock 파싱 테스트
# ---------------------------------------------------------------------------


def test_parse_mock():
    crawler = BizinfoCrawler()
    for i, item in enumerate(MOCK_ITEMS):
        prog = crawler.parse_program(item)
        print(f"\n  --- Item {i+1}: {prog.title} ---")
        print(f"  source_id:    {prog.source_id}")
        print(f"  category:     {prog.category}")
        print(f"  region:       {prog.region}")
        print(f"  status:       {prog.status}")
        print(f"  amount_max:   {prog.support_amount_max}")
        print(f"  app_start:    {prog.application_start}")
        print(f"  app_end:      {prog.application_end}")
        print(f"  tags:         {prog.tags}")
        assert prog.source_id
        assert prog.title
    print("\n  [PASS] parse_program (mock)")


# ---------------------------------------------------------------------------
# 실제 API 호출 테스트
# ---------------------------------------------------------------------------


async def test_live_api():
    crawler = BizinfoCrawler()
    print("\n  Calling BizInfo API (page 1 only)...")
    import httpx
    async with httpx.AsyncClient() as client:
        data = await crawler._request(client, page=1)

    total = data.get("totalCount", 0)
    items = data.get("data", [])
    print(f"  totalCount: {total}")
    print(f"  items on page 1: {len(items)}")

    if items:
        prog = crawler.parse_program(items[0])
        print(f"\n  First item parsed:")
        print(f"    title:      {prog.title}")
        print(f"    source_id:  {prog.source_id}")
        print(f"    category:   {prog.category}")
        print(f"    region:     {prog.region}")
        print(f"    status:     {prog.status}")
        print(f"    amount_max: {prog.support_amount_max}")
    print("\n  [PASS] live API test")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print(" BizInfo Crawler Test")
    print("=" * 60)

    print("\n[1] Unit tests — utility functions")
    test_extract_max_amount()
    test_normalize_category()
    test_normalize_region()
    test_determine_status()
    test_parse_date()

    print("\n[2] Mock parsing test")
    test_parse_mock()

    if settings.DATA_GO_KR_API_KEY:
        print("\n[3] Live API test (API key found)")
        asyncio.run(test_live_api())
    else:
        print("\n[3] Live API test — SKIPPED (DATA_GO_KR_API_KEY not set)")

    print("\n" + "=" * 60)
    print(" All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
