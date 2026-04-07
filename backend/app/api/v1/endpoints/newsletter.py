"""뉴스레터 구독 엔드포인트"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subscriber import Subscriber

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


class SubscribeRequest(BaseModel):
    email: str


class SubscribeResponse(BaseModel):
    message: str
    email: str


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(body: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    # Check existing
    result = await db.execute(
        select(Subscriber).where(Subscriber.email == body.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.is_active:
            return SubscribeResponse(message="이미 구독중입니다.", email=body.email)
        # Re-activate
        existing.is_active = True
        db.add(existing)
        await db.commit()
        return SubscribeResponse(message="구독이 다시 활성화되었습니다.", email=body.email)

    subscriber = Subscriber(email=body.email)
    db.add(subscriber)
    await db.commit()
    return SubscribeResponse(message="구독 완료! 매주 맞춤 지원사업을 보내드립니다.", email=body.email)


@router.post("/unsubscribe")
async def unsubscribe(body: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscriber).where(Subscriber.email == body.email)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="구독 정보를 찾을 수 없습니다.")
    sub.is_active = False
    db.add(sub)
    await db.commit()
    return {"message": "구독이 해지되었습니다."}
