"""Base chain monitor interface."""

from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator

from wallet_intelligence.models.wallet import Chain


@dataclass
class TxEvent:
    """Transaction event from chain monitoring."""

    tx_hash: str
    chain: Chain
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value_raw: int  # wei/lamports
    value_usd: float
    gas_used: int | None = None
    gas_price: int | None = None
    method_id: str | None = None
    input_data: str = ""
    token_transfers: list[dict] = field(default_factory=list)
    receipt: dict | None = None


class ChainMonitor(abc.ABC):
    """Abstract base for chain monitors."""

    def __init__(self, rpc_url: str, chain: Chain):
        self.rpc_url = rpc_url
        self.chain = chain
        self._running = False
        self._subscribers: list[asyncio.Queue] = []

    @abc.abstractmethod
    async def connect(self) -> None:
        """Initialize connection to RPC."""
        ...

    @abc.abstractmethod
    async def get_latest_block(self) -> int:
        """Get latest block number."""
        ...

    @abc.abstractmethod
    async def get_transactions_for_wallet(
        self, address: str, from_block: int, to_block: int
    ) -> list[TxEvent]:
        """Get transactions for a wallet in block range."""
        ...

    @abc.abstractmethod
    async def get_balance(self, address: str) -> float:
        """Get native balance in human-readable units."""
        ...

    @abc.abstractmethod
    async def get_token_balances(self, address: str) -> list[dict]:
        """Get ERC-20/SPL token balances."""
        ...

    @abc.abstractmethod
    async def subscribe_pending(self, address: str) -> AsyncIterator[TxEvent]:
        """Subscribe to pending transactions for address."""
        ...

    async def start(self) -> None:
        """Start monitoring."""
        self._running = True
        await self.connect()

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to transaction events."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.append(queue)
        return queue

    async def publish(self, event: TxEvent) -> None:
        """Publish event to all subscribers."""
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop if subscriber is too slow
