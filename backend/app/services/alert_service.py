"""알림 매칭 및 발송 서비스

크롤링 후 키워드/카테고리 매칭, 매일 마감 알림 체크,
이메일 발송(httpx → Resend API or SMTP fallback).
"""

import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import async_session
from app.models.alert import Alert, AlertType, ChannelType
from app.models.bookmark import Bookmark
from app.models.program import Program, ProgramStatus
from app.models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

RESEND_API_URL = "https://api.resend.com/emails"


async def _send_email(to: str, subject: str, html: str) -> bool:
    """Resend API로 이메일 발송. API 키 미설정 시 로그만 남긴다."""
    resend_key = getattr(settings, "RESEND_API_KEY", "")
    if not resend_key:
        logger.info("Email (dry-run) to=%s subject=%s", to, subject)
        return True

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {resend_key}"},
                json={
                    "from": "SearchPro <noreply@searchpro.kr>",
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=10,
            )
            if resp.status_code in (200, 201):
                logger.info("Email sent to %s", to)
                return True
            logger.warning("Email send failed: %s %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.exception("Email send error: %s", e)
        return False


def _build_programs_email(programs: list[Program], alert_label: str) -> str:
    """공고 카드 리스트 형태의 HTML 이메일 생성."""
    cards = ""
    for p in programs[:10]:
        deadline = ""
        if p.application_end:
            deadline = f"<span style='color:#dc2626;'>마감: {p.application_end.strftime('%Y.%m.%d')}</span>"
        cards += f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px;">
            <div style="font-weight:600;font-size:14px;margin-bottom:4px;">{p.title}</div>
            <div style="font-size:12px;color:#6b7280;">
                {p.organization or ''} · {p.category or ''} · {p.region or ''}
            </div>
            {f'<div style="font-size:12px;margin-top:4px;">{deadline}</div>' if deadline else ''}
            {f'<div style="font-size:12px;color:#0d9488;margin-top:2px;">{p.support_amount}</div>' if p.support_amount else ''}
        </div>
        """

    return f"""
    <div style="font-family:Pretendard,-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="text-align:center;margin-bottom:24px;">
            <span style="font-weight:700;font-size:20px;color:#1e3a5f;">Search</span>
            <span style="font-weight:700;font-size:20px;color:#0d9488;">Pro</span>
        </div>
        <h2 style="font-size:16px;margin-bottom:16px;">{alert_label}</h2>
        <p style="font-size:13px;color:#6b7280;margin-bottom:16px;">
            조건에 맞는 {len(programs)}건의 지원사업을 안내드립니다.
        </p>
        {cards}
        <div style="text-align:center;margin-top:24px;">
            <a href="{settings.NEXT_PUBLIC_API_URL if hasattr(settings, 'NEXT_PUBLIC_API_URL') else 'http://localhost:3000'}/programs"
               style="background:#1e3a5f;color:white;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:14px;">
                전체 목록 보기
            </a>
        </div>
        <p style="font-size:11px;color:#9ca3af;text-align:center;margin-top:24px;">
            본 메일은 SearchPro 알림 설정에 의해 발송되었습니다.
        </p>
    </div>
    """


# ---------------------------------------------------------------------------
# Alert checking
# ---------------------------------------------------------------------------


async def check_keyword_alerts(new_programs: list[Program]) -> int:
    """새로 수집된 공고와 KEYWORD/CATEGORY 알림을 매칭하여 이메일 발송.
    발송 건수를 반환한다.
    """
    if not new_programs:
        return 0

    sent_count = 0
    async with async_session() as session:
        # 활성 키워드/카테고리 알림 조회
        result = await session.execute(
            select(Alert)
            .where(Alert.is_active.is_(True))
            .where(Alert.type.in_([AlertType.KEYWORD, AlertType.CATEGORY]))
            .options(joinedload(Alert.user))
        )
        alerts = result.scalars().unique().all()

        for alert in alerts:
            matched: list[Program] = []
            cond = alert.condition or {}

            if alert.type == AlertType.KEYWORD:
                keywords = [k.lower() for k in cond.get("keywords", [])]
                for p in new_programs:
                    title_lower = (p.title or "").lower()
                    if any(kw in title_lower for kw in keywords):
                        matched.append(p)

            elif alert.type == AlertType.CATEGORY:
                cats = set(cond.get("categories", []))
                regions = set(cond.get("regions", []))
                for p in new_programs:
                    cat_match = not cats or p.category in cats
                    reg_match = not regions or p.region in regions
                    if cat_match and reg_match:
                        matched.append(p)

            if matched and alert.user:
                label = (
                    f"키워드 알림: {', '.join(cond.get('keywords', []))}"
                    if alert.type == AlertType.KEYWORD
                    else f"카테고리 알림: {', '.join(cond.get('categories', []))}"
                )
                html = _build_programs_email(matched, label)
                ok = await _send_email(
                    alert.user.email,
                    f"[SearchPro] {label} — {len(matched)}건 새 공고",
                    html,
                )
                if ok:
                    sent_count += 1

    logger.info("Keyword/category alerts: sent %d emails", sent_count)
    return sent_count


async def check_deadline_alerts() -> int:
    """북마크한 사업의 마감 알림. D-7, D-3, D-1에 해당하는 건을 찾아 발송.
    발송 건수를 반환한다.
    """
    sent_count = 0
    async with async_session() as session:
        # 활성 마감 알림 조회
        result = await session.execute(
            select(Alert)
            .where(Alert.is_active.is_(True))
            .where(Alert.type == AlertType.DEADLINE)
            .options(joinedload(Alert.user))
        )
        alerts = result.scalars().unique().all()

        for alert in alerts:
            days_before = alert.condition.get("days_before", [7, 3, 1])
            user = alert.user
            if not user:
                continue

            # 사용자 북마크 조회
            bm_result = await session.execute(
                select(Bookmark)
                .where(Bookmark.user_id == user.id)
                .options(joinedload(Bookmark.program))
            )
            bookmarks = bm_result.scalars().unique().all()

            matched: list[Program] = []
            today = datetime.now().date()
            for bm in bookmarks:
                prog = bm.program
                if not prog or not prog.application_end or prog.status == ProgramStatus.CLOSED:
                    continue
                days_left = (prog.application_end.date() - today).days
                if days_left in days_before:
                    matched.append(prog)

            if matched:
                label = f"마감 임박 알림 ({len(matched)}건)"
                html = _build_programs_email(matched, label)
                ok = await _send_email(
                    user.email,
                    f"[SearchPro] 북마크 사업 마감 임박 — {len(matched)}건",
                    html,
                )
                if ok:
                    sent_count += 1

    logger.info("Deadline alerts: sent %d emails", sent_count)
    return sent_count
