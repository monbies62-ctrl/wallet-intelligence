"""Alert notification service (Telegram, Discord, WebSocket)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

import httpx

from wallet_intelligence.core.config import settings
from wallet_intelligence.models.wallet import AlertType


class AlertService:
    """Send alerts via multiple channels."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._ws_queues: list[asyncio.Queue] = []

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=10)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()

    def subscribe_ws(self) -> asyncio.Queue:
        """Subscribe to alerts via WebSocket."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._ws_queues.append(queue)
        return queue

    async def send_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        chain: str = "",
        address: str = "",
        tx_hash: str = "",
        value_usd: float = 0.0,
        metadata: dict | None = None,
    ) -> None:
        """Send alert to all configured channels."""
        alert_data = {
            "type": alert_type.value,
            "title": title,
            "message": message,
            "chain": chain,
            "address": address,
            "tx_hash": tx_hash,
            "value_usd": value_usd,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        # Send to all channels in parallel
        tasks = []

        # WebSocket subscribers
        for queue in self._ws_queues:
            try:
                queue.put_nowait(alert_data)
            except asyncio.QueueFull:
                pass

        # Telegram
        if settings.telegram_bot_token and settings.telegram_chat_id:
            tasks.append(self._send_telegram(alert_data))

        # Discord
        if settings.discord_webhook_url:
            tasks.append(self._send_discord(alert_data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram(self, alert: dict) -> None:
        """Send alert to Telegram."""
        try:
            title = alert.get("title", "")
            msg = alert.get("message", "")
            chain = alert.get("chain", "")
            value = alert.get("value_usd", 0)
            tx_hash = alert.get("tx_hash", "")
            addr = alert.get("address", "")

            lines = [
                f"\U0001f6a8 *{title}*",
                "",
                msg,
                "",
                f"\U0001f517 Chain: `{chain}`",
                f"\U0001f4b0 Value: ${value:,.2f}",
            ]
            if tx_hash:
                lines.append(f"\U0001f4dd TX: `{tx_hash[:16]}...`")
            if addr:
                lines.append(f"\U0001f45b Wallet: `{addr[:16]}...`")

            text = "\n".join(lines)
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            await self._client.post(url, json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
        except Exception:
            pass

    async def _send_discord(self, alert: dict) -> None:
        """Send alert to Discord webhook."""
        try:
            embed = {
                "title": f"\U0001f6a8 {alert.get('title', '')}",
                "description": alert.get("message", ""),
                "color": 0xFF0000 if alert.get("value_usd", 0) > 100000 else 0xFFAA00,
                "fields": [
                    {"name": "Chain", "value": alert.get("chain", ""), "inline": True},
                    {"name": "Value", "value": f"${alert.get('value_usd', 0):,.2f}", "inline": True},
                ],
                "timestamp": alert.get("timestamp", ""),
            }
            if alert.get("tx_hash"):
                embed["fields"].append({
                    "name": "TX Hash",
                    "value": f"`{alert['tx_hash'][:16]}...`",
                    "inline": False,
                })

            await self._client.post(settings.discord_webhook_url, json={
                "embeds": [embed],
            })
        except Exception:
            pass

    def format_whale_alert(
        self, chain: str, from_addr: str, to_addr: str, value_usd: float, tx_hash: str
    ) -> tuple[str, str]:
        """Format a whale transaction alert."""
        title = f"Whale Transfer on {chain.title()}"
        message = "\n".join([
            "\U0001f40b Large transfer detected!",
            "",
            f"From: `{from_addr[:8]}...{from_addr[-6:]}`",
            f"To: `{to_addr[:8]}...{to_addr[-6:]}`",
            f"Amount: *${value_usd:,.2f}*",
        ])
        return title, message
