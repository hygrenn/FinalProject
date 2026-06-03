# backend/api/routes/realtime.py
from typing import AsyncGenerator

from fastapi import APIRouter, Path, Request
from sse_starlette.sse import EventSourceResponse

from api.middleware.rate_limit import limiter
from core.redis_client import get_redis
from services.websocket_service import kis_pool

router = APIRouter()


@router.get("/ws/stocks/{code}")
@limiter.limit("20/minute")
async def stock_stream(
    request: Request,
    code: str = Path(..., pattern=r"^[0-9]{6}$"),
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict, None]:
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"stock:{code}")
        await kis_pool.subscribe(code)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    yield {"data": data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data}
        finally:
            await kis_pool.unsubscribe(code)
            await pubsub.aclose()

    return EventSourceResponse(event_generator())
