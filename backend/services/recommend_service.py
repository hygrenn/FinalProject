"""추천 종목 서비스 — 100종목 전체 스캔.

기존 AI 시그널(ai_service.get_signal: 기술지표 + LSTM)을 그대로 활용하고,
그 위에 '보조 필터'로 재무 평가와 시장 지수 추세를 얹는다.

추천 규칙(사용자 정의 — 기존 점수 + 보조 필터):
- 기존 AI 시그널이 BUY 인 종목만 후보로 삼는다.
- 재무가 '위험'(fundamental.risk)인 종목은 제외한다.
- 시장 지수가 하락 추세면 각 추천에 주의(caution) 플래그를 붙인다.
- 시그널 점수 → 재무 점수 순으로 정렬해 상위를 반환한다.
"""
from __future__ import annotations

import asyncio
import json

from core.redis_client import get_redis
from services import ai_service, fundamental_service, market_index_service
from services.market_service import _build_ticker_cache

_CONCURRENCY = 8


async def _evaluate_one(item: dict, sem: asyncio.Semaphore) -> dict | None:
    code = item["code"]
    async with sem:
        try:
            signal = await ai_service.get_signal(code)  # db 미전달 → 계산만(이력 저장 X)
        except Exception:
            return None
    if signal.get("signal") != "BUY":
        return None

    fundamental = await fundamental_service.get_fundamental(code)
    # 보조 필터: 재무가 위험이면 추천에서 제외.
    if fundamental.get("available") and fundamental.get("risk"):
        return None

    return {
        "code": code,
        "name": item.get("name", code),
        "signal": signal.get("signal"),
        "signal_score": signal.get("signal_score", 0),
        "financial_score": fundamental.get("score"),
        "financial_grade": fundamental.get("grade"),
    }


async def get_recommendations(limit: int = 20) -> dict:
    """top100 전체를 스캔해 BUY 추천 종목을 반환(캐시 5분)."""
    redis = await get_redis()
    cache_key = f"recommendations:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    tickers = await asyncio.to_thread(_build_ticker_cache, "KOSPI")
    index_ctx = await market_index_service.get_index_context()

    sem = asyncio.Semaphore(_CONCURRENCY)
    results = await asyncio.gather(*[_evaluate_one(t, sem) for t in tickers])
    picks = [r for r in results if r]

    caution = index_ctx.get("trend") == "down"
    for p in picks:
        p["market_caution"] = caution

    # 시그널 점수 → 재무 점수 순 정렬.
    picks.sort(key=lambda x: (x["signal_score"], x.get("financial_score") or 0), reverse=True)

    result = {
        "picks": picks[:limit],
        "scanned": len(tickers),
        "buy_count": len(picks),
        "market_trend": index_ctx.get("trend"),
        "market_caution": caution,
    }
    await redis.setex(cache_key, 300, json.dumps(result))
    return result
