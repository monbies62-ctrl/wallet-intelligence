"""Wallet database models."""

from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import String, Float, Boolean, Enum, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from wallet_intelligence.core.database import Base


class Chain(str, enum.Enum):
    """Supported blockchain networks."""

    ETHEREUM = "ethereum"
    BASE = "base"
    ARBITRUM = "arbitrum"
    POLYGON = "polygon"
    SOLANA = "solana"


class AlertType(str, enum.Enum):
    """Alert trigger types."""

    WHALE_TX = "whale_tx"
    LARGE_SWAP = "large_swap"
    NEW_TOKEN = "new_token"
    WALLET_ACTIVITY = "wallet_activity"
    PRICE_MOVE = "price_move"


class Wallet(Base):
    """Tracked wallet."""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(128), index=True)
    chain: Mapped[Chain] = mapped_column(Enum(Chain))
    label: Mapped[str | None] = mapped_column(String(256))
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_whale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_smart_money: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime | None] = mapped_column(DateTime)
    total_balance_usd: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_30d_usd: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="wallet")
    holdings: Mapped[list["Holding"]] = relationship(back_populates="wallet")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="wallet")

    __table_args__ = (
        Index("ix_wallets_chain_address", "chain", "address", unique=True),
    )


class Transaction(Base):
    """Wallet transaction."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    tx_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    chain: Mapped[Chain] = mapped_column(Enum(Chain))
    block_number: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    from_address: Mapped[str] = mapped_column(String(128))
    to_address: Mapped[str] = mapped_column(String(128))
    value_usd: Mapped[float] = mapped_column(Float, default=0.0)
    gas_used: Mapped[int | None] = mapped_column(Integer)
    gas_price_gwei: Mapped[float | None] = mapped_column(Float)
    tx_type: Mapped[str | None] = mapped_column(String(64))  # swap, transfer, approve, etc.
    classification: Mapped[str | None] = mapped_column(String(128))  # AI classification
    classification_confidence: Mapped[float | None] = mapped_column(Float)
    protocol: Mapped[str | None] = mapped_column(String(128))  # Uniswap, Aave, etc.
    tokens: Mapped[list] = mapped_column(JSONB, default=list)  # token addresses involved
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("ix_txs_wallet_timestamp", "wallet_id", "timestamp"),
    )


class Holding(Base):
    """Token holding for a wallet."""

    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    chain: Mapped[Chain] = mapped_column(Enum(Chain))
    token_address: Mapped[str] = mapped_column(String(128))
    token_symbol: Mapped[str] = mapped_column(String(32))
    token_name: Mapped[str | None] = mapped_column(String(256))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    balance_usd: Mapped[float] = mapped_column(Float, default=0.0)
    price_usd: Mapped[float | None] = mapped_column(Float)
    price_change_24h: Mapped[float | None] = mapped_column(Float)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    wallet: Mapped["Wallet"] = relationship(back_populates="holdings")

    __table_args__ = (
        Index("ix_holdings_wallet_token", "wallet_id", "token_address", unique=True),
    )


class Alert(Base):
    """Alert rule and history."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int | None] = mapped_column(ForeignKey("wallets.id"), index=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    chain: Mapped[Chain | None] = mapped_column(Enum(Chain))
    threshold_usd: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_telegram: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_discord: Mapped[bool] = mapped_column(Boolean, default=False)
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    wallet: Mapped["Wallet"] = relationship(back_populates="alerts")


class SmartMoneyTracker(Base):
    """Smart money wallet metrics."""

    __tablename__ = "smart_money"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    chain: Mapped[Chain] = mapped_column(Enum(Chain))
    label: Mapped[str | None] = mapped_column(String(256))
    category: Mapped[str | None] = mapped_column(String(64))  # fund, whale, trader, etc.
    total_pnl_usd: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_trade_size_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[datetime | None] = mapped_column(DateTime)
    top_tokens: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
