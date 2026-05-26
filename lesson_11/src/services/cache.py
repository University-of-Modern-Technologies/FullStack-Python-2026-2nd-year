"""Кеш списку todos у Redis."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class CacheService:
    def __init__(self, redis_url: str):
        self._client = redis.from_url(redis_url, decode_responses=True)

    async def ping(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            logger.exception("Redis ping failed")
            return False

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def todos_list_key(user_id: int, limit: int, offset: int) -> str:
        return f"todos:list:{user_id}:{limit}:{offset}"

    async def get_json(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    async def invalidate_user_todos(self, user_id: int) -> None:
        pattern = f"todos:list:{user_id}:*"
        async for key in self._client.scan_iter(match=pattern):
            await self._client.delete(key)


cache_service = CacheService(settings.REDIS_URL)
