"""맞춤 추천 서비스 — 규칙 기반 (Phase 1 MVP)

사용자 프로필(업종, 지역, 관심분야)을 기반으로
진행중 공고를 점수화하여 추천합니다.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.bookmark import Bookmark
from app.models.program import Program, ProgramStatus
from app.models.user import User
from app.schemas.program import ProgramListItem

logger = logging.getLogger(__name__)


async def get_recommendations(
    user: User | None,
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """사용자 프로필 기반 맞춤 추천. 비로그인 시 인기+마감임박 조합.

    반환: [{...program fields, reason: str}, ...]
    """
    if not user or not user.profile:
        return await _get_popular_programs(db, limit)

    profile = user.profile
    interests = profile.get("interests", [])
    region = profile.get("region")
    biz_type = profile.get("business_type")

    now = datetime.now()
    week_later = now + timedelta(days=7)

    # 이미 북마크한 사업 ID
    bm_result = await db.execute(
        select(Bookmark.program_id).where(Bookmark.user_id == user.id)
    )
    bookmarked_ids = {row[0] for row in bm_result.all()}

    # 기본 조건: OPEN 상태
    stmt = select(Program).where(Program.status == ProgramStatus.OPEN)

    # 관심 분야 또는 지역 매칭 조건 (OR)
    conditions = []
    if interests:
        conditions.append(Program.category.in_(interests))
    if region:
        conditions.append(or_(Program.region == region, Program.region == "전국"))
    if biz_type:
        conditions.append(Program.target_type.ilike(f"%{biz_type}%"))

    if conditions:
        stmt = stmt.where(or_(*conditions))

    # 점수화 정렬
    score_expr = (
        # 카테고리 매칭 가중치
        case(
            (Program.category.in_(interests) if interests else Program.id.is_not(None), 3),
            else_=0,
        )
        # 지역 매칭 가중치
        + case(
            (or_(Program.region == region, Program.region == "전국") if region else Program.id.is_not(None), 2),
            else_=0,
        )
        # 마감 임박 가중치 (7일 이내)
        + case(
            (and_(Program.application_end >= now, Program.application_end <= week_later), 2),
            else_=0,
        )
        # 인기도 보조
        + case(
            (Program.view_count > 10, 1),
            else_=0,
        )
    )

    stmt = stmt.order_by(desc(score_expr), Program.application_end.asc().nullslast())
    stmt = stmt.limit(limit + len(bookmarked_ids))  # 북마크 제외 여유분

    result = await db.execute(stmt)
    programs = result.scalars().all()

    # 북마크 제외 및 추천 이유 생성
    recommendations = []
    for p in programs:
        if p.id in bookmarked_ids:
            continue
        if len(recommendations) >= limit:
            break

        reasons = []
        if interests and p.category in interests:
            reasons.append(p.category)
        if region and p.region in (region, "전국"):
            reasons.append(p.region)
        if p.application_end:
            days_left = (p.application_end - now).days
            if 0 <= days_left <= 7:
                reasons.append(f"D-{days_left}")

        item = ProgramListItem.model_validate(p)
        recommendations.append({
            **item.model_dump(),
            "reason": " · ".join(reasons) if reasons else "추천",
        })

    return recommendations


async def _get_popular_programs(db: AsyncSession, limit: int) -> list[dict]:
    """비로그인 사용자용: 인기순 + 마감임박 조합."""
    now = datetime.now()
    week_later = now + timedelta(days=7)

    stmt = (
        select(Program)
        .where(Program.status == ProgramStatus.OPEN)
        .order_by(
            case(
                (and_(Program.application_end >= now, Program.application_end <= week_later), 0),
                else_=1,
            ),
            desc(Program.view_count),
            Program.application_end.asc().nullslast(),
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    programs = result.scalars().all()

    return [
        {
            **ProgramListItem.model_validate(p).model_dump(),
            "reason": "인기" if p.view_count > 0 else "추천",
        }
        for p in programs
    ]
