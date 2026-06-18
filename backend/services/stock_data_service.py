"""공유 종목 데이터 캐시 서비스.

100개 종목의 AI 시그널 + 재무 데이터를 한 번만 스캔하고
Redis에 5분간 캐시한다. 스크리너·AI랭킹·추천 서비스가 모두
이 캐시를 재활용하므로 중복 pykrx/네이버 호출을 없앤다.

첫 호출: 100종목 병렬 스캔 (~10-20초)
이후:    Redis hit → 즉시 반환
"""
from __future__ import annotations

import asyncio
import json

from core.redis_client import get_redis
from services import ai_service, fundamental_service
from services.market_service import _build_ticker_cache

_CACHE_KEY = "stock_data_cache:v2"
_CACHE_TTL = 300   # 5분
_CONCURRENCY = 20  # pykrx 병렬 한도


async def _fetch_one(item: dict, sem: asyncio.Semaphore) -> dict | None:
    code = item["code"]
    async with sem:
        try:
            signal = await ai_service.get_signal(code)
        except Exception:
            return None

    try:
        fund = await fundamental_service.get_fundamental(code)
    except Exception:
        fund = {"available": False}

    breakdown = signal.get("signal_breakdown") or {}
    metrics = (fund.get("metrics") or {}) if fund.get("available") else {}

    return {
        "code": code,
        "name": item.get("name", code),
        # AI
        "signal": signal.get("signal"),
        "signal_score": signal.get("signal_score", 0),
        "tech_score": breakdown.get("technical_score"),
        "lstm_score": breakdown.get("lstm_score"),
        "lstm_available": signal.get("lstm_available", False),
        # 재무
        "financial_score": fund.get("score"),
        "financial_grade": fund.get("grade"),
        "financial_risk": fund.get("risk"),
        "per": metrics.get("per"),
        "pbr": metrics.get("pbr"),
        "roe": metrics.get("roe"),
        "eps": metrics.get("eps"),
        "dividend_yield": metrics.get("dividend_yield"),
    }


async def get_all_stock_data(force_refresh: bool = False) -> list[dict]:
    """전체 종목 데이터 반환 (캐시 우선)."""
    redis = await get_redis()

    if not force_refresh:
        cached = await redis.get(_CACHE_KEY)
        if cached:
            return json.loads(cached)

    tickers = await asyncio.to_thread(_build_ticker_cache, "KOSPI")
    sem = asyncio.Semaphore(_CONCURRENCY)
    raw = await asyncio.gather(*[_fetch_one(t, sem) for t in tickers])
    data = [r for r in raw if r]

    await redis.setex(_CACHE_KEY, _CACHE_TTL, json.dumps(data))
    return data
