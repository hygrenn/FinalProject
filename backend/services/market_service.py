import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pykrx import stock as pykrx_stock

from core.redis_client import get_redis

_KST = ZoneInfo("Asia/Seoul")


def _is_market_open() -> bool:
    now = datetime.now(_KST)
    if now.weekday() >= 5:
        return False
    t = now.hour * 100 + now.minute
    return 900 <= t <= 1530


def _last_trading_day() -> str:
    """Return the most recent weekday date string (YYYYMMDD)."""
    now = datetime.now(_KST)
    day = now
    # Step back until weekday (Mon=0 … Fri=4)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day.strftime("%Y%m%d")


async def get_ohlcv_from_pykrx(code: str, period: str, interval: str) -> list[dict]:
    period_days = {"1w": 7, "1m": 30, "3m": 90, "6m": 180, "1y": 365, "3y": 1095}
    freq_map = {"day": "d", "week": "w", "month": "m"}

    end = datetime.now(_KST)
    start = end - timedelta(days=period_days.get(period, 30))
    try:
        df = pykrx_stock.get_market_ohlcv_by_date(
            start.strftime("%Y%m%d"),
            end.strftime("%Y%m%d"),
            code,
            freq=freq_map.get(interval, "d"),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"시세 데이터 조회 실패: {exc}") from exc

    if df is None or df.empty:
        return []

    return [
        {
            "date": date.strftime("%Y%m%d"),
            "open": int(row.get("시가", 0)),
            "high": int(row.get("고가", 0)),
            "low": int(row.get("저가", 0)),
            "close": int(row.get("종가", 0)),
            "volume": int(row.get("거래량", 0)),
        }
        for date, row in df.iterrows()
    ]


async def get_ohlcv_cached(code: str, period: str, interval: str) -> list[dict]:
    redis = await get_redis()
    cache_key = f"ohlcv:{code}:{period}:{interval}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    data = await get_ohlcv_from_pykrx(code, period, interval)
    ttl = 30 if _is_market_open() else 86400
    await redis.setex(cache_key, ttl, json.dumps(data))
    return data


async def get_stock_current_price(code: str) -> dict:
    redis = await get_redis()
    cache_key = f"price:{code}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    date_str = _last_trading_day()
    try:
        df = pykrx_stock.get_market_ohlcv_by_date(date_str, date_str, code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"현재가 조회 실패: {exc}") from exc

    if df is None or df.empty:
        return {"code": code}

    row = df.iloc[-1]
    data = {
        "code": code,
        "close": int(row.get("종가", 0)),
        "open": int(row.get("시가", 0)),
        "high": int(row.get("고가", 0)),
        "low": int(row.get("저가", 0)),
        "volume": int(row.get("거래량", 0)),
    }
    ttl = 30 if _is_market_open() else 86400
    await redis.setex(cache_key, ttl, json.dumps(data))
    return data


def _build_ticker_cache(market_str: str) -> list[dict]:
    """Fetch tickers with names from pykrx and return as [{code, name}] list."""
    try:
        codes = pykrx_stock.get_market_ticker_list(market=market_str)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"종목 목록 조회 실패: {exc}") from exc
    result = []
    for code in codes:
        try:
            name = pykrx_stock.get_market_ticker_name(code)
        except Exception:
            name = ""
        result.append({"code": code, "name": name})
    return result


async def _get_ticker_list(market: str) -> list[dict]:
    """Return cached [{code, name}] list for the given market key ('kospi'/'kosdaq')."""
    redis = await get_redis()
    cache_key = f"stocklist:{market.lower()}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    market_str = "KOSPI" if market.lower() == "kospi" else "KOSDAQ"
    tickers = _build_ticker_cache(market_str)
    await redis.setex(cache_key, 86400, json.dumps(tickers))
    return tickers


async def get_stock_list(market: str, limit: int, page: int) -> list[dict]:
    tickers = await _get_ticker_list(market)
    start = (page - 1) * limit
    return tickers[start : start + limit]


async def search_stocks(query: str) -> list[dict]:
    all_tickers: list[dict] = []
    for market in ["kospi", "kosdaq"]:
        all_tickers.extend(await _get_ticker_list(market))

    q = query.lower()
    results = []
    for item in all_tickers:
        if q in item["code"].lower() or q in item["name"].lower():
            results.append(item)
        if len(results) >= 20:
            break
    return results


async def get_indices() -> list[dict]:
    redis = await get_redis()
    cache_key = "indices"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    date_str = _last_trading_day()
    result = []
    for name, code in [("KOSPI", "1"), ("KOSDAQ", "2")]:
        try:
            df = pykrx_stock.get_index_ohlcv_by_date(date_str, date_str, code)
            if df is not None and not df.empty:
                row = df.iloc[-1]
                result.append({
                    "name": name,
                    "value": float(row.get("종가", 0)),
                    "change_rate": float(row.get("등락률", 0)),
                })
        except Exception:
            pass

    ttl = 30 if _is_market_open() else 3600
    await redis.setex(cache_key, ttl, json.dumps(result))
    return result
