"""북마크 API — 추가, 제거, 목록, 메모 수정"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.auth import get_current_user
from app.database import get_db
from app.models.bookmark import Bookmark
from app.models.program import Program
from app.models.user import User
from app.schemas.bookmark import BookmarkCreate, BookmarkResponse, BookmarkUpdate
from app.schemas.program import ProgramListItem

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class BookmarkWithProgram(BookmarkResponse):
    program: ProgramListItem | None = None


# ---------------------------------------------------------------------------
# POST /bookmarks
# ---------------------------------------------------------------------------


@router.post("", response_model=BookmarkResponse, status_code=201)
async def add_bookmark(
    body: BookmarkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 프로그램 존재 확인
    program = await db.get(Program, body.program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # 이미 북마크 확인
    existing = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.program_id == body.program_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already bookmarked")

    bookmark = Bookmark(
        user_id=user.id,
        program_id=body.program_id,
        memo=body.memo,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return BookmarkResponse.model_validate(bookmark)


# ---------------------------------------------------------------------------
# DELETE /bookmarks/{program_id}
# ---------------------------------------------------------------------------


@router.delete("/{program_id}", status_code=204)
async def remove_bookmark(
    program_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.program_id == program_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await db.commit()


# ---------------------------------------------------------------------------
# GET /bookmarks
# ---------------------------------------------------------------------------


@router.get("", response_model=list[BookmarkWithProgram])
async def list_bookmarks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .options(joinedload(Bookmark.program))
        .order_by(Bookmark.created_at.desc())
    )
    bookmarks = result.scalars().unique().all()

    items = []
    for bm in bookmarks:
        data = BookmarkWithProgram.model_validate(bm)
        if bm.program:
            data.program = ProgramListItem.model_validate(bm.program)
        items.append(data)
    return items


# ---------------------------------------------------------------------------
# PUT /bookmarks/{program_id}/memo
# ---------------------------------------------------------------------------


@router.put("/{program_id}/memo", response_model=BookmarkResponse)
async def update_memo(
    program_id: UUID,
    body: BookmarkUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.program_id == program_id,
        )
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    bookmark.memo = body.memo
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return BookmarkResponse.model_validate(bookmark)
