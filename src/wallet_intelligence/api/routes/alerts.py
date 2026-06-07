"""Alert management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wallet_intelligence.core.database import get_db
from wallet_intelligence.models.wallet import Alert, AlertType, Chain
from wallet_intelligence.api.schemas import AlertCreate, AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    is_active: bool | None = None,
    alert_type: AlertType | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List alert rules."""
    query = select(Alert)
    if is_active is not None:
        query = query.where(Alert.is_active == is_active)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    query = query.order_by(Alert.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert rule."""
    alert = Alert(
        wallet_id=data.wallet_id,
        alert_type=data.alert_type,
        chain=data.chain,
        threshold_usd=data.threshold_usd,
        notify_telegram=data.notify_telegram,
        notify_discord=data.notify_discord,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    is_active: bool | None = None,
    threshold_usd: float | None = None,
    notify_telegram: bool | None = None,
    notify_discord: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update an alert rule."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")

    if is_active is not None:
        alert.is_active = is_active
    if threshold_usd is not None:
        alert.threshold_usd = threshold_usd
    if notify_telegram is not None:
        alert.notify_telegram = notify_telegram
    if notify_discord is not None:
        alert.notify_discord = notify_discord

    await db.flush()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert rule."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.delete(alert)
