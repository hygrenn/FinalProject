import json
from datetime import datetime, timedelta

from pykrx import stock as pykrx_stock

from core.redis_client import get_redis


def _is_market_open() -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.hour * 100 + now.minute
    return 900 <= t <= 1530


async def get_ohlcv_from_pykrx(code: str, period: str, interval: str) -> list[dict]:
    period_days = {"1w": 7, "1m": 30, "3m": 90, "6m": 180, "1y": 365, "3y": 1095}
    freq_map = {"day": "d", "week": "w", "month": "m"}

    end = datetime.now()
    start = end - timedelta(days=period_days.get(period, 30))
    df = pykrx_stock.get_market_ohlcv_by_date(
        start.strftime("%Y%m%d"),
        end.strftime("%Y%m%d"),
        code,
        freq=freq_map.get(interval, "d"),
    )
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

    today = datetime.now().strftime("%Y%m%d")
    df = pykrx_stock.get_market_ohlcv_by_date(today, today, code)
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


async def get_stock_list(market: str, limit: int, page: int) -> list[dict]:
    redis = await get_redis()
    cache_key = f"stocklist:{market.lower()}"

    cached = await redis.get(cache_key)
    if cached:
        tickers = json.loads(cached)
    else:
        market_str = "KOSPI" if market.lower() == "kospi" else "KOSDAQ"
        tickers = list(pykrx_stock.get_market_ticker_list(market=market_str))
        await redis.setex(cache_key, 86400, json.dumps(tickers))

    start = (page - 1) * limit
    page_tickers = tickers[start : start + limit]
    return [{"code": t, "name": pykrx_stock.get_market_ticker_name(t)} for t in page_tickers]


async def search_stocks(query: str) -> list[dict]:
    redis = await get_redis()
    all_tickers: list[str] = []

    for market in ["kospi", "kosdaq"]:
        cache_key = f"stocklist:{market}"
        cached = await redis.get(cache_key)
        if cached:
            all_tickers.extend(json.loads(cached))
        else:
            tickers = list(pykrx_stock.get_market_ticker_list(market=market.upper()))
            await redis.setex(cache_key, 86400, json.dumps(tickers))
            all_tickers.extend(tickers)

    q = query.lower()
    results = []
    for code in all_tickers:
        name = pykrx_stock.get_market_ticker_name(code)
        if q in code.lower() or q in name.lower():
            results.append({"code": code, "name": name})
        if len(results) >= 20:
            break
    return results


async def get_indices() -> list[dict]:
    redis = await get_redis()
    cache_key = "indices"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    today = datetime.now().strftime("%Y%m%d")
    result = []
    for name, code in [("KOSPI", "1"), ("KOSDAQ", "2")]:
        try:
            df = pykrx_stock.get_index_ohlcv_by_date(today, today, code)
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
