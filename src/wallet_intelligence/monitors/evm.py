"""EVM chain monitor (Ethereum, Base, Arbitrum, Polygon)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware

from wallet_intelligence.core.config import settings
from wallet_intelligence.monitors.base import ChainMonitor, TxEvent
from wallet_intelligence.models.wallet import Chain

# Standard ERC-20 Transfer event topic
ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class EVMonitor(ChainMonitor):
    """Monitor EVM-compatible chains."""

    def __init__(self, rpc_url: str, chain: Chain):
        super().__init__(rpc_url, chain)
        self.w3: AsyncWeb3 | None = None
        self._http_client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Initialize Web3 connection."""
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        # Add POA middleware for Base/Arbitrum/Polygon
        if self.chain in (Chain.BASE, Chain.ARBITRUM, Chain.POLYGON):
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self._http_client = httpx.AsyncClient(timeout=30)
        connected = await self.w3.is_connected()
        if not connected:
            raise ConnectionError(f"Failed to connect to {self.chain.value} RPC: {self.rpc_url}")

    async def get_latest_block(self) -> int:
        """Get latest block number."""
        return await self.w3.eth.block_number

    async def get_balance(self, address: str) -> float:
        """Get native balance in ETH/BNB/etc."""
        balance_wei = await self.w3.eth.get_balance(address)
        return float(self.w3.from_wei(balance_wei, "ether"))

    async def get_token_balances(self, address: str) -> list[dict]:
        """Get ERC-20 token balances via RPC + token list."""
        # Use eth_getLogs to find Transfer events TO this address
        # For production, use Alchemy/Ankr token balance API
        if settings.etherscan_api_key and self.chain == Chain.ETHEREUM:
            return await self._get_token_balances_etherscan(address)
        return []

    async def _get_token_balances_etherscan(self, address: str) -> list[dict]:
        """Get token balances via Etherscan API."""
        url = "https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "sort": "desc",
            "page": 1,
            "offset": 100,
            "apikey": settings.etherscan_api_key,
        }
        resp = await self._http_client.get(url, params=params)
        data = resp.json()
        if data.get("status") != "1":
            return []

        # Deduplicate tokens
        tokens = {}
        for tx in data.get("result", []):
            contract = tx["contractAddress"].lower()
            if contract not in tokens:
                tokens[contract] = {
                    "address": contract,
                    "symbol": tx.get("tokenSymbol", ""),
                    "name": tx.get("tokenName", ""),
                    "decimals": int(tx.get("tokenDecimal", 18)),
                }
        return list(tokens.values())

    async def get_transactions_for_wallet(
        self, address: str, from_block: int, to_block: int
    ) -> list[TxEvent]:
        """Get transactions for wallet in block range using eth_getLogs."""
        address = address.lower()
        events = []

        # Get native transfers (from/to)
        try:
            logs = await self.w3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": to_block,
                "$or": [
                    {"from": address},
                    {"to": address},
                ],
            })
        except Exception:
            # Some RPCs don't support $or, fall back to block scan
            return await self._scan_blocks_for_txs(address, from_block, to_block)

        for log in logs:
            try:
                tx = await self.w3.eth.get_transaction(log["transactionHash"].hex())
                receipt = await self.w3.eth.get_transaction_receipt(log["transactionHash"].hex())
                block = await self.w3.eth.get_block(tx["blockNumber"])

                value_eth = float(self.w3.from_wei(tx["value"], "ether"))
                # Rough USD estimate (would need price feed in production)
                value_usd = value_eth * 0.0  # TODO: integrate price oracle

                events.append(TxEvent(
                    tx_hash=tx["hash"].hex(),
                    chain=self.chain,
                    block_number=tx["blockNumber"],
                    timestamp=datetime.fromtimestamp(block["timestamp"], tz=timezone.utc),
                    from_address=tx["from"].lower(),
                    to_address=(tx.get("to") or "").lower(),
                    value_raw=tx["value"],
                    value_usd=value_usd,
                    gas_used=receipt["gasUsed"],
                    gas_price=tx["gasPrice"],
                    input_data=tx["input"].hex() if isinstance(tx["input"], bytes) else tx["input"],
                ))
            except Exception:
                continue

        return events

    async def _scan_blocks_for_txs(
        self, address: str, from_block: int, to_block: int
    ) -> list[TxEvent]:
        """Fallback: scan blocks for transactions."""
        events = []
        for block_num in range(from_block, to_block + 1):
            try:
                block = await self.w3.eth.get_block(block_num, full_transactions=True)
                for tx in block["transactions"]:
                    if tx["from"].lower() == address or (tx.get("to") or "").lower() == address:
                        value_eth = float(self.w3.from_wei(tx["value"], "ether"))
                        events.append(TxEvent(
                            tx_hash=tx["hash"].hex(),
                            chain=self.chain,
                            block_number=block_num,
                            timestamp=datetime.fromtimestamp(block["timestamp"], tz=timezone.utc),
                            from_address=tx["from"].lower(),
                            to_address=(tx.get("to") or "").lower(),
                            value_raw=tx["value"],
                            value_usd=value_eth * 0.0,
                        ))
            except Exception:
                continue
        return events

    async def subscribe_pending(self, address: str) -> AsyncIterator[TxEvent]:
        """Poll for new blocks and filter transactions."""
        last_block = await self.get_latest_block()
        while self._running:
            try:
                current_block = await self.get_latest_block()
                if current_block > last_block:
                    txs = await self.get_transactions_for_wallet(address, last_block + 1, current_block)
                    for tx in txs:
                        yield tx
                    last_block = current_block
            except Exception:
                pass
            await asyncio.sleep(settings.poll_interval_seconds)

    async def close(self) -> None:
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()


def create_evm_monitor(chain: Chain) -> EVMonitor:
    """Factory for EVM monitors."""
    rpc_map = {
        Chain.ETHEREUM: settings.eth_rpc_url,
        Chain.BASE: settings.base_rpc_url,
        Chain.ARBITRUM: settings.arb_rpc_url,
        Chain.POLYGON: settings.polygon_rpc_url,
    }
    return EVMonitor(rpc_url=rpc_map[chain], chain=chain)
