"""API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from wallet_intelligence.models.wallet import Chain, AlertType


# ── Wallet ──────────────────────────────────────────

class WalletCreate(BaseModel):
    address: str = Field(..., description="Wallet address (0x... or base58)")
    chain: Chain
    label: str | None = None
    tags: list[str] = []

class WalletResponse(BaseModel):
    id: int
    address: str
    chain: Chain
    label: str | None
    tags: list[str]
    is_whale: bool
    is_smart_money: bool
    first_seen: datetime
    last_active: datetime | None
    total_balance_usd: float
    pnl_30d_usd: float
    win_rate: float

    model_config = {"from_attributes": True}

class WalletDetail(WalletResponse):
    holdings: list[HoldingResponse] = []
    recent_txs: list[TxResponse] = []


# ── Transaction ─────────────────────────────────────

class TxResponse(BaseModel):
    tx_hash: str
    chain: Chain
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value_usd: float
    tx_type: str | None
    classification: str | None
    protocol: str | None

    model_config = {"from_attributes": True}


# ── Holding ─────────────────────────────────────────

class HoldingResponse(BaseModel):
    token_address: str
    token_symbol: str
    token_name: str | None
    balance: float
    balance_usd: float
    price_usd: float | None
    price_change_24h: float | None

    model_config = {"from_attributes": True}


# ── Alert ───────────────────────────────────────────

class AlertCreate(BaseModel):
    wallet_id: int | None = None
    alert_type: AlertType
    chain: Chain | None = None
    threshold_usd: float = 0.0
    notify_telegram: bool = True
    notify_discord: bool = False

class AlertResponse(BaseModel):
    id: int
    wallet_id: int | None
    alert_type: AlertType
    chain: Chain | None
    threshold_usd: float
    is_active: bool
    notify_telegram: bool
    notify_discord: bool
    last_triggered: datetime | None
    trigger_count: int

    model_config = {"from_attributes": True}


# ── Smart Money ─────────────────────────────────────

class SmartMoneyResponse(BaseModel):
    address: str
    chain: Chain
    label: str | None
    category: str | None
    total_pnl_usd: float
    win_rate: float
    avg_trade_size_usd: float
    total_trades: int
    last_active: datetime | None

    model_config = {"from_attributes": True}


# ── Whale ───────────────────────────────────────────

class WhaleTxResponse(BaseModel):
    tx_hash: str
    chain: Chain
    from_address: str
    to_address: str
    value_usd: float
    timestamp: datetime
    classification: str | None


# ── P&L ─────────────────────────────────────────────

class PnLResponse(BaseModel):
    address: str
    chain: Chain
    period_days: int
    total_pnl_usd: float
    realized_pnl_usd: float
    unrealized_pnl_usd: float
    win_rate: float
    total_trades: int
    best_trade: dict | None
    worst_trade: dict | None
    top_holdings: list[HoldingResponse]


# ── WebSocket ───────────────────────────────────────

class WSMessage(BaseModel):
    event: str  # "new_tx", "whale_alert", "price_alert"
    data: dict
