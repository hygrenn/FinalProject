"""스크리너 서비스 — 사용자 정의 조건으로 종목 필터링.

캐시된 AI 시그널 + 재무 데이터를 재활용하므로
첫 스캔 이후에는 빠르게 응답한다.

필터 조건:
  signals          - BUY/HOLD/SELL 포함 여부 (미지정 시 전체)
  min_score        - AI 점수 최솟값 (0-100)
  grades           - 재무 등급 포함 여부 (우수/양호/보통/위험)
  max_per          - PER 최댓값
  max_pbr          - PBR 최댓값
  min_roe          - ROE 최솟값 (%)
  exclude_risk     - 재무 위험 종목 제외
  sort_by          - signal_score | financial_score | per | pbr
"""
from __future__ import annotations

import asyncio

from services import ai_service, fundamental_service
from services.market_service import _build_ticker_cache

_CONCURRENCY = 10


async def _fetch_one(item: dict, sem: asyncio.Semaphore) -> dict | None:
    code = item["code"]
    async with sem:
        try:
            signal = await ai_service.get_signal(code)
        except Exception:
            return None

    fund = await fundamental_service.get_fundamental(code)
    breakdown = signal.get("signal_breakdown") or {}

    return {
        "code": code,
        "name": item.get("name", code),
        "signal": signal.get("signal"),
        "signal_score": signal.get("signal_score", 0),
        "tech_score": breakdown.get("technical_score"),
        "lstm_score": breakdown.get("lstm_score"),
        "lstm_available": signal.get("lstm_available", False),
        "financial_score": fund.get("score"),
        "financial_grade": fund.get("grade"),
        "financial_risk": fund.get("risk"),
        "per": (fund.get("metrics") or {}).get("per"),
        "pbr": (fund.get("metrics") or {}).get("pbr"),
        "roe": (fund.get("metrics") or {}).get("roe"),
        "eps": (fund.get("metrics") or {}).get("eps"),
        "dividend_yield": (fund.get("metrics") or {}).get("dividend_yield"),
    }


def _passes(
    item: dict,
    signals: list[str] | None,
    min_score: float | None,
    grades: list[str] | None,
    max_per: float | None,
    max_pbr: float | None,
    min_roe: float | None,
    exclude_risk: bool,
) -> bool:
    if signals and item.get("signal") not in signals:
        return False
    if min_score is not None and (item.get("signal_score") or 0) < min_score:
        return False
    if grades and item.get("financial_grade") not in grades:
        return False
    if max_per is not None:
        per = item.get("per")
        if per is None or per > max_per:
            return False
    if max_pbr is not None:
        pbr = item.get("pbr")
        if pbr is None or pbr > max_pbr:
            return False
    if min_roe is not None:
        roe = item.get("roe")
        if roe is None or roe < min_roe:
            return False
    if exclude_risk and item.get("financial_risk"):
        return False
    return True


_SORT_KEY = {
    "signal_score":    lambda x: x.get("signal_score") or 0,
    "financial_score": lambda x: x.get("financial_score") or 0,
    "per":             lambda x: x.get("per") or 9999,
    "pbr":             lambda x: x.get("pbr") or 9999,
}


async def run_screener(
    signals: list[str] | None = None,
    min_score: float | None = None,
    grades: list[str] | None = None,
    max_per: float | None = None,
    max_pbr: float | None = None,
    min_roe: float | None = None,
    exclude_risk: bool = False,
    sort_by: str = "signal_score",
    limit: int = 50,
) -> dict:
    tickers = await asyncio.to_thread(_build_ticker_cache, "KOSPI")
    sem = asyncio.Semaphore(_CONCURRENCY)
    raw = await asyncio.gather(*[_fetch_one(t, sem) for t in tickers])

    results = [
        r for r in raw
        if r and _passes(r, signals, min_score, grades, max_per, max_pbr, min_roe, exclude_risk)
    ]

    key_fn = _SORT_KEY.get(sort_by, _SORT_KEY["signal_score"])
    reverse = sort_by not in ("per", "pbr")
    results.sort(key=key_fn, reverse=reverse)

    return {
        "results": results[:limit],
        "matched": len(results),
        "scanned": len(tickers),
    }
