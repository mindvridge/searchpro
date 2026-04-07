"""위비티(wevity.com) 공모전/대외활동 웹 크롤러

씽굿과 동일한 HTML 파싱 구조. robots.txt 준수, 3초 간격.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.database import async_session
from app.models.program import SourceType
from app.models.crawl_log import CrawlLog, CrawlStatus
from app.schemas.program import ProgramCreate
from app.crawlers.utils import (
    normalize_region,
    parse_date,
    determine_status,
    extract_max_amount,
    build_tags,
    upsert_programs,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.wevity.com"
LIST_URL = f"{BASE_URL}/?c=find&s=1"
USER_AGENT = "SearchProBot/1.0 (+https://searchpro.kr/about)"
REQUEST_INTERVAL = 3.0
MAX_PAGES = 10

WEVITY_CATEGORY_MAP: dict[str, str] = {
    "기획/아이디어": "창업",
    "광고/마케팅": "마케팅",
    "디자인": "마케팅",
    "영상/사진": "마케팅",
    "IT/SW": "R&D",
    "과학/공학": "R&D",
    "문학/글": "기타",
    "창업": "창업",
    "봉사활동": "기타",
    "해외탐방": "수출",
    "기타": "기타",
}


def _map_category(raw: str | None) -> str:
    if not raw:
        return "기타"
    for key, val in WEVITY_CATEGORY_MAP.items():
        if key in raw:
            return val
    return "기타"


def _make_source_id(title: str, org: str) -> str:
    h = hashlib.md5(f"{title}:{org}".encode()).hexdigest()[:16]
    return f"WV_{h}"


class WevityCrawler:
    """위비티 공모전/대외활동 크롤러"""

    async def _fetch_page(self, client: httpx.AsyncClient, page: int) -> str:
        params = {"page": page}
        resp = await client.get(
            LIST_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text

    def _parse_list_page(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []

        # 위비티 카드/리스트 구조
        for card in soup.select(".contest-card, .thumList li, .list_item, .thumb_wrap"):
            try:
                item = self._parse_card(card)
                if item and item.get("title"):
                    items.append(item)
            except Exception as e:
                logger.debug("Wevity card parse error: %s", e)

        # 링크 폴백
        if not items:
            for link in soup.select("a[href*='view']"):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if title and len(title) > 5:
                    items.append({
                        "title": title,
                        "detail_url": href if href.startswith("http") else f"{BASE_URL}{href}",
                    })

        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one("h3, h4, .title, .tit, a.tit")
        if not title_el:
            title_el = card.select_one("a")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        href = ""
        link_el = card.select_one("a[href]")
        if link_el:
            href = link_el.get("href", "")
            if href and not href.startswith("http"):
                href = f"{BASE_URL}{href}"

        org_el = card.select_one(".org, .host, .company, .organizer, .sponsor")
        org = org_el.get_text(strip=True) if org_el else None

        date_el = card.select_one(".date, .period, .dday, .deadline, .d_day")
        date_text = date_el.get_text(strip=True) if date_el else None

        cat_el = card.select_one(".category, .field, .cate")
        cat = cat_el.get_text(strip=True) if cat_el else None

        prize_el = card.select_one(".prize, .reward, .benefit")
        prize = prize_el.get_text(strip=True) if prize_el else None

        return {
            "title": title,
            "organization": org,
            "date_text": date_text,
            "category_raw": cat,
            "prize": prize,
            "detail_url": href,
        }

    def _parse_dates(self, date_text: str | None) -> tuple[datetime | None, datetime | None]:
        if not date_text:
            return None, None
        parts = re.split(r"[~\-–]", date_text.replace(" ", ""))
        start = parse_date(parts[0].strip()) if len(parts) >= 1 else None
        end = parse_date(parts[-1].strip()) if len(parts) >= 2 else None
        return start, end

    def parse_program(self, raw: dict) -> ProgramCreate:
        title = raw.get("title", "")
        organization = raw.get("organization") or None
        source_id = _make_source_id(title, organization or "")

        app_start, app_end = self._parse_dates(raw.get("date_text"))
        category = _map_category(raw.get("category_raw"))
        status = determine_status(app_start, app_end)
        prize = raw.get("prize")
        amount_max = extract_max_amount(prize)

        tags = build_tags(
            category if category != "기타" else None,
            "공모전",
            raw.get("category_raw"),
        )

        return ProgramCreate(
            source=SourceType.WEVITY,
            source_id=source_id,
            title=title.strip(),
            organization=organization,
            category=category,
            sub_category=raw.get("category_raw"),
            region="전국",
            target_type=None,
            support_amount=prize,
            support_amount_max=amount_max,
            application_start=app_start,
            application_end=app_end,
            status=status,
            description=None,
            eligibility=None,
            detail_url=raw.get("detail_url"),
            raw_data=raw,
            tags=tags,
        )

    async def fetch_all(self) -> list[dict]:
        all_items: list[dict] = []
        async with httpx.AsyncClient() as client:
            for page in range(1, MAX_PAGES + 1):
                try:
                    html = await self._fetch_page(client, page)
                    items = self._parse_list_page(html)
                    if not items:
                        break
                    all_items.extend(items)
                    logger.info("Wevity page %d: %d items", page, len(items))
                except httpx.HTTPError as e:
                    logger.warning("Wevity page %d failed: %s", page, e)
                    break
                await asyncio.sleep(REQUEST_INTERVAL)

        logger.info("Wevity: fetched %d items total", len(all_items))
        return all_items

    async def run(self) -> CrawlLog:
        async with async_session() as session:
            log = CrawlLog(source="WEVITY", status=CrawlStatus.RUNNING)
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

                new_count, updated_count = await upsert_programs(session, programs)

                log.total_fetched = len(raw_items)
                log.new_count = new_count
                log.updated_count = updated_count
                log.error_count = len(errors)
                log.error_detail = "\n".join(errors) if errors else None
                log.status = CrawlStatus.SUCCESS
                log.finished_at = datetime.now()

            except Exception as e:
                logger.exception("Wevity crawl failed: %s", e)
                log.status = CrawlStatus.FAILED
                log.error_count = len(errors) + 1
                errors.append(f"Fatal: {e}")
                log.error_detail = "\n".join(errors)
                log.finished_at = datetime.now()

            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log
