"""Token price oracle using DexScreener and CoinGecko."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx

from wallet_intelligence.core.config import settings
from wallet_intelligence.core.redis import cache_get, cache_set


class PriceOracle:
    """Multi-source token price oracle."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._cache_ttl = 60  # seconds

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=15)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()

    async def get_price_usd(self, token_address: str, chain: str = "ethereum") -> float | None:
        """Get token price in USD."""
        cache_key = f"price:{chain}:{token_address}"
        cached = await cache_get(cache_key)
        if cached:
            return cached.get("price")

        price = await self._fetch_dexscreener_price(token_address, chain)
        if price is None:
            price = await self._fetch_coingecko_price(token_address, chain)

        if price is not None:
            await cache_set(cache_key, {"price": price}, ttl=self._cache_ttl)

        return price

    async def get_native_price(self, chain: str) -> float | None:
        """Get native token price (ETH, SOL, etc.)."""
        native_map = {
            "ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "base": "0x4200000000000000000000000000000000000006",  # WETH on Base
            "arbitrum": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",  # WETH on Arb
            "polygon": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",  # MATIC
            "solana": "So11111111111111111111111111111111111111112",  # SOL
        }
        address = native_map.get(chain)
        if not address:
            return None
        return await self.get_price_usd(address, chain)

    async def _fetch_dexscreener_price(self, token_address: str, chain: str) -> float | None:
        """Fetch price from DexScreener."""
        try:
            url = f"{settings.dexscreener_api_url}/dex/tokens/{token_address}"
            resp = await self._client.get(url)
            data = resp.json()
            pairs = data.get("pairs", [])
            if pairs:
                return float(pairs[0].get("priceUsd", 0))
        except Exception:
            pass
        return None

    async def _fetch_coingecko_price(self, token_address: str, chain: str) -> float | None:
        """Fetch price from CoinGecko (free API)."""
        try:
            platform_map = {
                "ethereum": "ethereum",
                "base": "base",
                "arbitrum": "arbitrum-one",
                "polygon": "polygon-pos",
                "solana": "solana",
            }
            platform = platform_map.get(chain, "ethereum")
            url = f"https://api.coingecko.com/api/v3/simple/token_price/{platform}"
            params = {
                "contract_addresses": token_address,
                "vs_currencies": "usd",
            }
            resp = await self._client.get(url, params=params)
            data = resp.json()
            price = data.get(token_address.lower(), {}).get("usd")
            if price:
                return float(price)
        except Exception:
            pass
        return None

    async def get_token_info(self, token_address: str, chain: str = "ethereum") -> dict | None:
        """Get token metadata (name, symbol, decimals)."""
        cache_key = f"token_info:{chain}:{token_address}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        try:
            url = f"{settings.dexscreener_api_url}/dex/tokens/{token_address}"
            resp = await self._client.get(url)
            data = resp.json()
            pairs = data.get("pairs", [])
            if pairs:
                info = {
                    "name": pairs[0].get("baseToken", {}).get("name", ""),
                    "symbol": pairs[0].get("baseToken", {}).get("symbol", ""),
                    "price_usd": float(pairs[0].get("priceUsd", 0)),
                    "liquidity_usd": pairs[0].get("liquidity", {}).get("usd", 0),
                    "volume_24h": pairs[0].get("volume", {}).get("h24", 0),
                    "price_change_24h": pairs[0].get("priceChange", {}).get("h24", 0),
                }
                await cache_set(cache_key, info, ttl=300)
                return info
        except Exception:
            pass
        return None
