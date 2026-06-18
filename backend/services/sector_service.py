"""업종(섹터) 히트맵 서비스.

pykrx get_market_sector_classifications 를 사용해
KOSPI 전 종목의 업종별 등락률·시가총액·상위 종목을 집계한다.
"""
from __future__ import annotations

import asyncio
import json
from datetime import date, timedelta

from core.redis_client import get_redis
from services.market_service import _is_market_open, _last_trading_day

_CACHE_KEY = "sector_heatmap:v1"
_TTL_OPEN   = 300
_TTL_CLOSED = 86400


def _fetch_sector_raw(date_str: str) -> list[dict]:
    """pykrx 동기 호출 — asyncio.to_thread 안에서 실행."""
    from pykrx import stock as pykrx_stock

    try:
        df = pykrx_stock.get_market_sector_classifications(date_str, "KOSPI")
    except Exception:
        return []

    if df is None or df.empty:
        return []

    sectors: dict[str, dict] = {}

    for code, row in df.iterrows():
        sector = str(row.get("업종명", "기타")).strip()
        name   = str(row.get("종목명", code)).strip()
        try:
            chg = float(row.get("등락률", 0.0))
        except (TypeError, ValueError):
            chg = 0.0
        try:
            mktcap = int(row.get("시가총액", 0))
        except (TypeError, ValueError):
            mktcap = 0

        if sector not in sectors:
            sectors[sector] = {
                "sector": sector,
                "total_mktcap": 0,
                "weighted_chg": 0.0,
                "up_count":    0,
                "down_count":  0,
                "flat_count":  0,
                "top_stocks":  [],
            }

        s = sectors[sector]
        s["total_mktcap"]  += mktcap
        s["weighted_chg"]  += chg * mktcap   # 가중합 (나중에 나누기)

        if chg > 0:
            s["up_count"]   += 1
        elif chg < 0:
            s["down_count"] += 1
        else:
            s["flat_count"] += 1

        s["top_stocks"].append({"code": str(code), "name": name, "change_pct": chg, "mktcap": mktcap})

    result = []
    for s in sectors.values():
        mc = s["total_mktcap"]
        s["change_pct"] = round(s["weighted_chg"] / mc, 2) if mc > 0 else 0.0
        del s["weighted_chg"]
        # 상위 종목: 시가총액 상위 5개
        s["top_stocks"] = sorted(s["top_stocks"], key=lambda x: x["mktcap"], reverse=True)[:5]
        result.append(s)

    # 시가총액 내림차순 정렬
    result.sort(key=lambda x: x["total_mktcap"], reverse=True)
    return result


async def get_sector_heatmap() -> dict:
    """업종별 등락률·시가총액·상위 종목 반환 (캐시 포함)."""
    redis = await get_redis()
    cached = await redis.get(_CACHE_KEY)
    if cached:
        return json.loads(cached)

    date_str = _last_trading_day()

    try:
        sectors = await asyncio.to_thread(_fetch_sector_raw, date_str)
    except Exception:
        sectors = []

    result = {
        "date": date_str,
        "available": len(sectors) > 0,
        "sectors": sectors,
    }

    ttl = _TTL_OPEN if _is_market_open() else _TTL_CLOSED
    await redis.setex(_CACHE_KEY, ttl, json.dumps(result))
    return result
