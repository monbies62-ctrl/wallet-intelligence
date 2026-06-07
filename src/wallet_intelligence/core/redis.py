"""Redis cache manager."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from wallet_intelligence.core.config import settings

redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return redis_client


async def cache_get(key: str) -> Any | None:
    """Get value from cache."""
    r = await get_redis()
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL (seconds)."""
    r = await get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str) -> None:
    """Delete key from cache."""
    r = await get_redis()
    await r.delete(key)


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
