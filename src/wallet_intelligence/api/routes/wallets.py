"""Wallet management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wallet_intelligence.core.database import get_db
from wallet_intelligence.core.redis import cache_get, cache_set
from wallet_intelligence.models.wallet import Wallet, Transaction, Holding, Chain
from wallet_intelligence.api.schemas import (
    WalletCreate, WalletResponse, WalletDetail,
    TxResponse, HoldingResponse, PnLResponse,
)

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.get("", response_model=list[WalletResponse])
async def list_wallets(
    chain: Chain | None = None,
    is_whale: bool | None = None,
    is_smart_money: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List tracked wallets with optional filters."""
    query = select(Wallet)
    if chain:
        query = query.where(Wallet.chain == chain)
    if is_whale is not None:
        query = query.where(Wallet.is_whale == is_whale)
    if is_smart_money is not None:
        query = query.where(Wallet.is_smart_money == is_smart_money)
    query = query.order_by(Wallet.last_active.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=WalletResponse, status_code=201)
async def create_wallet(
    data: WalletCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a wallet to track."""
    # Check if already tracked
    existing = await db.execute(
        select(Wallet).where(
            Wallet.address == data.address.lower(),
            Wallet.chain == data.chain,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Wallet already tracked")

    wallet = Wallet(
        address=data.address.lower(),
        chain=data.chain,
        label=data.label,
        tags=data.tags,
    )
    db.add(wallet)
    await db.flush()
    await db.refresh(wallet)
    return wallet


@router.get("/{address}", response_model=WalletDetail)
async def get_wallet(
    address: str,
    chain: Chain = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get wallet details with holdings and recent transactions."""
    result = await db.execute(
        select(Wallet)
        .where(Wallet.address == address.lower(), Wallet.chain == chain)
        .options(selectinload(Wallet.holdings), selectinload(Wallet.transactions))
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(404, "Wallet not found")
    return wallet


@router.get("/{address}/txs", response_model=list[TxResponse])
async def get_wallet_transactions(
    address: str,
    chain: Chain = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get wallet transaction history."""
    # Get wallet ID
    wallet_result = await db.execute(
        select(Wallet.id).where(Wallet.address == address.lower(), Wallet.chain == chain)
    )
    wallet_id = wallet_result.scalar_one_or_none()
    if not wallet_id:
        raise HTTPException(404, "Wallet not found")

    tx_result = await db.execute(
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return tx_result.scalars().all()


@router.get("/{address}/pnl", response_model=PnLResponse)
async def get_wallet_pnl(
    address: str,
    chain: Chain = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get wallet P&L analysis."""
    # Check cache first
    cache_key = f"pnl:{chain}:{address}:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return PnLResponse(**cached)

    wallet_result = await db.execute(
        select(Wallet).where(Wallet.address == address.lower(), Wallet.chain == chain)
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(404, "Wallet not found")

    # Get holdings
    holdings_result = await db.execute(
        select(Holding).where(Holding.wallet_id == wallet.id)
    )
    holdings = holdings_result.scalars().all()

    # Calculate P&L (simplified — production would be more sophisticated)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    tx_result = await db.execute(
        select(Transaction).where(
            Transaction.wallet_id == wallet.id,
            Transaction.timestamp >= cutoff,
        )
    )
    txs = tx_result.scalars().all()

    total_pnl = sum(tx.value_usd for tx in txs if tx.classification == "swap")
    realized = total_pnl * 0.7  # simplified
    unrealized = wallet.total_balance_usd - (wallet.total_balance_usd * 0.9)  # simplified

    response = PnLResponse(
        address=address,
        chain=chain,
        period_days=days,
        total_pnl_usd=total_pnl,
        realized_pnl_usd=realized,
        unrealized_pnl_usd=unrealized,
        win_rate=wallet.win_rate,
        total_trades=len(txs),
        best_trade=None,  # TODO
        worst_trade=None,  # TODO
        top_holdings=[HoldingResponse.model_validate(h) for h in holdings[:10]],
    )

    await cache_set(cache_key, response.model_dump(), ttl=300)
    return response


@router.delete("/{address}", status_code=204)
async def delete_wallet(
    address: str,
    chain: Chain = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Stop tracking a wallet."""
    result = await db.execute(
        select(Wallet).where(Wallet.address == address.lower(), Wallet.chain == chain)
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(404, "Wallet not found")
    await db.delete(wallet)
