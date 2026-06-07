"""Solana chain monitor."""

from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from wallet_intelligence.core.config import settings
from wallet_intelligence.monitors.base import ChainMonitor, TxEvent
from wallet_intelligence.models.wallet import Chain


class SolanaMonitor(ChainMonitor):
    """Monitor Solana wallets."""

    def __init__(self, rpc_url: str = settings.solana_rpc_url):
        super().__init__(rpc_url, Chain.SOLANA)
        self._client: httpx.AsyncClient | None = None
        self._last_slot: int = 0

    async def connect(self) -> None:
        """Initialize Solana RPC connection."""
        self._client = httpx.AsyncClient(timeout=30)
        # Verify connection
        resp = await self._client.post(self.rpc_url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth",
        })
        if resp.status_code != 200:
            raise ConnectionError(f"Failed to connect to Solana RPC: {self.rpc_url}")

    async def _rpc_call(self, method: str, params: list | None = None) -> dict:
        """Make JSON-RPC call to Solana."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        resp = await self._client.post(self.rpc_url, json=payload)
        data = resp.json()
        if "error" in data:
            raise Exception(f"Solana RPC error: {data['error']}")
        return data.get("result", {})

    async def get_latest_block(self) -> int:
        """Get latest slot."""
        result = await self._rpc_call("getSlot", [{"commitment": "confirmed"}])
        return result

    async def get_balance(self, address: str) -> float:
        """Get SOL balance."""
        result = await self._rpc_call("getBalance", [address])
        return result["value"] / 1e9  # lamports to SOL

    async def get_token_balances(self, address: str) -> list[dict]:
        """Get SPL token balances."""
        result = await self._rpc_call("getTokenAccountsByOwner", [
            address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"},
        ])

        balances = []
        for account in result.get("value", []):
            info = account["account"]["data"]["parsed"]["info"]
            token_amount = info.get("tokenAmount", {})
            if float(token_amount.get("uiAmount", 0)) > 0:
                balances.append({
                    "address": info.get("mint", ""),
                    "balance": float(token_amount.get("uiAmount", 0)),
                    "decimals": token_amount.get("decimals", 9),
                })
        return balances

    async def get_transactions_for_wallet(
        self, address: str, from_slot: int, to_slot: int
    ) -> list[TxEvent]:
        """Get recent transactions for wallet."""
        result = await self._rpc_call("getSignaturesForAddress", [
            address,
            {"limit": 100},
        ])

        events = []
        for sig_info in result:
            slot = sig_info.get("slot", 0)
            if slot < from_slot or slot > to_slot:
                continue

            try:
                tx_detail = await self._rpc_call("getTransaction", [
                    sig_info["signature"],
                    {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
                ])

                if not tx_detail:
                    continue

                meta = tx_detail.get("meta", {})
                message = tx_detail.get("transaction", {}).get("message", {})

                # Calculate SOL transfer amount
                pre_balances = meta.get("preBalances", [])
                post_balances = meta.get("postBalances", [])
                account_keys = message.get("accountKeys", [])

                from_idx = None
                for i, key in enumerate(account_keys):
                    pubkey = key if isinstance(key, str) else key.get("pubkey", "")
                    if pubkey == address and i < len(pre_balances):
                        from_idx = i
                        break

                value_lamports = 0
                if from_idx is not None and from_idx < len(pre_balances):
                    value_lamports = abs(post_balances[from_idx] - pre_balances[from_idx])

                timestamp = tx_detail.get("blockTime", 0)
                events.append(TxEvent(
                    tx_hash=sig_info["signature"],
                    chain=Chain.SOLANA,
                    block_number=slot,
                    timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp else datetime.now(timezone.utc),
                    from_address=address,
                    to_address="",
                    value_raw=value_lamports,
                    value_usd=0.0,  # needs price feed
                    token_transfers=self._extract_token_transfers(meta),
                ))
            except Exception:
                continue

        return events

    def _extract_token_transfers(self, meta: dict) -> list[dict]:
        """Extract token transfers from transaction meta."""
        transfers = []
        pre = {t["accountIndex"]: t for t in meta.get("preTokenBalances", [])}
        post = {t["accountIndex"]: t for t in meta.get("postTokenBalances", [])}

        for idx in set(pre.keys()) | set(post.keys()):
            pre_bal = pre.get(idx, {}).get("uiTokenAmount", {}).get("uiAmount", 0) or 0
            post_bal = post.get(idx, {}).get("uiTokenAmount", {}).get("uiAmount", 0) or 0
            if pre_bal != post_bal:
                mint = post.get(idx, {}).get("mint") or pre.get(idx, {}).get("mint", "")
                transfers.append({
                    "mint": mint,
                    "amount_change": post_bal - pre_bal,
                })
        return transfers

    async def subscribe_pending(self, address: str) -> AsyncIterator[TxEvent]:
        """Poll for new transactions."""
        self._last_slot = await self.get_latest_block()
        seen_sigs: set = set()

        while self._running:
            try:
                current_slot = await self.get_latest_block()
                if current_slot > self._last_slot:
                    txs = await self.get_transactions_for_wallet(address, self._last_slot, current_slot)
                    for tx in txs:
                        if tx.tx_hash not in seen_sigs:
                            seen_sigs.add(tx.tx_hash)
                            yield tx
                    self._last_slot = current_slot

                    # Keep seen_sigs from growing forever
                    if len(seen_sigs) > 10000:
                        seen_sigs.clear()
            except Exception:
                pass
            await asyncio.sleep(settings.poll_interval_seconds)

    async def close(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.aclose()
