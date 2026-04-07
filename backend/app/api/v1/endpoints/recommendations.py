"""AI 요약 + 맞춤 추천 엔드포인트"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_current_user_optional
from app.database import get_db
from app.models.program import Program
from app.models.user import User
from app.services.ai_service import summarize_program, batch_summarize_new_programs
from app.services.recommendation_service import get_recommendations

router = APIRouter(tags=["ai"])


# ---------------------------------------------------------------------------
# GET /programs/{id}/summary
# ---------------------------------------------------------------------------


@router.get("/programs/{program_id}/summary")
async def get_program_summary(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """공고 AI 요약을 반환한다. 캐시된 요약이 없으면 실시간 생성."""
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # 이미 요약이 있으면 바로 반환
    if program.summary:
        return {"summary": program.summary, "cached": True}

    # 실시간 생성
    summary = await summarize_program(program)
    if not summary:
        return {"summary": None, "cached": False, "message": "AI 요약을 생성할 수 없습니다."}

    return {"summary": summary, "cached": False}


# ---------------------------------------------------------------------------
# GET /recommendations
# ---------------------------------------------------------------------------


@router.get("/recommendations")
async def get_user_recommendations(
    limit: int = Query(10, ge=1, le=30),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """사용자 맞춤 추천. 비로그인 시 인기+마감임박 조합."""
    items = await get_recommendations(user, db, limit)
    return {"items": items, "personalized": user is not None and user.profile is not None}


# ---------------------------------------------------------------------------
# POST /admin/ai/batch-summarize (관리용)
# ---------------------------------------------------------------------------


@router.post("/admin/ai/batch-summarize")
async def trigger_batch_summarize(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    """요약 미생성 공고에 대해 일괄 요약 생성 (관리자용)."""
    count = await batch_summarize_new_programs(limit)
    return {"generated": count}
