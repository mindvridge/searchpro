"""알림 설정 API — CRUD + 토글"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    body: AlertCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = Alert(
        user_id=user.id,
        type=body.type,
        condition=body.condition,
        channel=body.channel,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .where(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
    )
    return [AlertResponse.model_validate(a) for a in result.scalars().all()]


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    body: AlertUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await _get_user_alert(alert_id, user.id, db)
    if body.condition is not None:
        alert.condition = body.condition
    if body.channel is not None:
        alert.channel = body.channel
    if body.is_active is not None:
        alert.is_active = body.is_active
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await _get_user_alert(alert_id, user.id, db)
    await db.delete(alert)
    await db.commit()


@router.put("/{alert_id}/toggle", response_model=AlertResponse)
async def toggle_alert(
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await _get_user_alert(alert_id, user.id, db)
    alert.is_active = not alert.is_active
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


async def _get_user_alert(alert_id: UUID, user_id: UUID, db: AsyncSession) -> Alert:
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
