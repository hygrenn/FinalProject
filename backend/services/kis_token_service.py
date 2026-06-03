# backend/services/kis_token_service.py
import httpx

from core.redis_client import get_redis

_KIS_REAL = "https://openapi.koreainvestment.com:9443"
_KIS_PAPER = "https://openapivts.koreainvestment.com:29443"


def _base(mode: str) -> str:
    return _KIS_PAPER if mode == "paper" else _KIS_REAL


async def get_access_token(app_key: str, app_secret: str, mode: str) -> str:
    redis = await get_redis()
    cache_key = f"access_token:{mode}:{app_key[:8]}"

    cached = await redis.get(cache_key)
    if cached:
        return cached.decode() if isinstance(cached, bytes) else cached

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_base(mode)}/oauth2/tokenP",
            json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    token: str = data["access_token"]
    ttl: int = int(data.get("expires_in", 86400)) - 60
    await redis.setex(cache_key, ttl, token)
    return token


async def get_approval_key(app_key: str, app_secret: str, mode: str) -> str:
    redis = await get_redis()
    cache_key = f"approval_key:{mode}:{app_key[:8]}"

    cached = await redis.get(cache_key)
    if cached:
        return cached.decode() if isinstance(cached, bytes) else cached

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_base(mode)}/oauth2/Approval",
            json={"grant_type": "client_credentials", "appkey": app_key, "secretkey": app_secret},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    key: str = data["approval_key"]
    await redis.setex(cache_key, 82800, key)
    return key
