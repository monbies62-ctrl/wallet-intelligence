"""Analytics and whale tracking routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from wallet_intelligence.core.database import get_db
from wallet_intelligence.core.redis import cache_get, cache_set
from wallet_intelligence.models.wallet import (
    Transaction, Wallet, SmartMoneyTracker, Chain
)
from wallet_intelligence.api.schemas import WhaleTxResponse, SmartMoneyResponse

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/whales", response_model=list[WhaleTxResponse])
async def get_whale_transactions(
    chain: Chain | None = None,
    min_value_usd: float = Query(100000, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get recent whale transactions."""
    cache_key = f"whales:{chain}:{min_value_usd}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [WhaleTxResponse(**tx) for tx in cached]

    query = (
        select(Transaction)
        .where(Transaction.value_usd >= min_value_usd)
        .order_by(desc(Transaction.timestamp))
        .limit(limit)
    )
    if chain:
        query = query.where(Transaction.chain == chain)

    result = await db.execute(query)
    txs = result.scalars().all()

    response = [
        WhaleTxResponse(
            tx_hash=tx.tx_hash,
            chain=tx.chain,
            from_address=tx.from_address,
            to_address=tx.to_address,
            value_usd=tx.value_usd,
            timestamp=tx.timestamp,
            classification=tx.classification,
        )
        for tx in txs
    ]

    await cache_set(cache_key, [r.model_dump() for r in response], ttl=30)
    return response


@router.get("/analytics/smart-money", response_model=list[SmartMoneyResponse])
async def get_smart_money(
    chain: Chain | None = None,
    category: str | None = None,
    min_pnl_usd: float = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get smart money wallets ranked by performance."""
    query = select(SmartMoneyTracker).where(
        SmartMoneyTracker.total_pnl_usd >= min_pnl_usd
    )
    if chain:
        query = query.where(SmartMoneyTracker.chain == chain)
    if category:
        query = query.where(SmartMoneyTracker.category == category)
    query = query.order_by(desc(SmartMoneyTracker.total_pnl_usd)).limit(limit)

    result = await db.execute(query)
    trackers = result.scalars().all()
    return [SmartMoneyResponse.model_validate(t) for t in trackers]


@router.get("/analytics/volume")
async def get_volume_stats(
    chain: Chain | None = None,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get transaction volume statistics."""
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    query = select(
        func.count(Transaction.id).label("tx_count"),
        func.sum(Transaction.value_usd).label("total_volume_usd"),
        func.avg(Transaction.value_usd).label("avg_tx_size_usd"),
    ).where(Transaction.timestamp >= cutoff)

    if chain:
        query = query.where(Transaction.chain == chain)

    result = await db.execute(query)
    row = result.one()

    return {
        "period_hours": hours,
        "chain": chain.value if chain else "all",
        "tx_count": row.tx_count or 0,
        "total_volume_usd": float(row.total_volume_usd or 0),
        "avg_tx_size_usd": float(row.avg_tx_size_usd or 0),
    }
