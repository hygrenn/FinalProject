# backend/services/kis_market_service.py
import json

import httpx
from fastapi import HTTPException

from core.config import settings
from core.redis_client import get_redis
from services.kis_token_service import get_access_token
from services.market_service import _is_market_open


def _base(mode: str) -> str:
    return (
        "https://openapivts.koreainvestment.com:29443"
        if mode == "paper"
        else "https://openapi.koreainvestment.com:9443"
    )


def _kis_headers(access_token: str, tr_id: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "appkey": settings.SYSTEM_KIS_APP_KEY,
        "appsecret": settings.SYSTEM_KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
        "Content-Type": "application/json; charset=utf-8",
    }


async def get_orderbook(code: str) -> dict:
    """10단 호가. system KIS 키 없으면 빈 결과."""
    if not settings.SYSTEM_KIS_APP_KEY:
        return {"code": code, "asks": [], "bids": []}

    redis = await get_redis()
    cache_key = f"orderbook:{code}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    token = await get_access_token(
        settings.SYSTEM_KIS_APP_KEY, settings.SYSTEM_KIS_APP_SECRET, settings.SYSTEM_KIS_MODE
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{_base(settings.SYSTEM_KIS_MODE)}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
                headers=_kis_headers(token, "FHKST01010200"),
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
            )
            resp.raise_for_status()
            out = resp.json().get("output1", {})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"호가 조회 실패: {exc}") from exc

    asks = [
        {"price": int(out.get(f"askp{i}", 0)), "qty": int(out.get(f"askp_rsqn{i}", 0))}
        for i in range(1, 11)
    ]
    bids = [
        {"price": int(out.get(f"bidp{i}", 0)), "qty": int(out.get(f"bidp_rsqn{i}", 0))}
        for i in range(1, 11)
    ]
    data = {"code": code, "asks": asks, "bids": bids}
    ttl = 5 if _is_market_open() else 60
    await redis.setex(cache_key, ttl, json.dumps(data))
    return data


async def get_recent_trades(code: str) -> list[dict]:
    """최근 체결 20건. system KIS 키 없으면 빈 결과."""
    if not settings.SYSTEM_KIS_APP_KEY:
        return []

    redis = await get_redis()
    cache_key = f"trades:{code}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    token = await get_access_token(
        settings.SYSTEM_KIS_APP_KEY, settings.SYSTEM_KIS_APP_SECRET, settings.SYSTEM_KIS_MODE
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{_base(settings.SYSTEM_KIS_MODE)}/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion",
                headers=_kis_headers(token, "FHKST01010300"),
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
            )
            resp.raise_for_status()
            output2 = resp.json().get("output2", [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"체결 조회 실패: {exc}") from exc

    trades = [
        {
            "time": row.get("stck_cntg_hour", ""),
            "price": int(row.get("stck_prpr", 0)),
            "volume": int(row.get("cntg_vol", 0)),
            "change": row.get("prdy_vrss_sign", "3"),
        }
        for row in output2[:20]
    ]
    ttl = 3 if _is_market_open() else 60
    await redis.setex(cache_key, ttl, json.dumps(trades))
    return trades


async def get_intraday_ohlcv(code: str, interval: str) -> list[dict]:
    """분봉 OHLCV. interval: '1min'|'5min'|'15min'|'1h'. system KIS 키 없으면 빈 결과."""
    if not settings.SYSTEM_KIS_APP_KEY:
        return []

    redis = await get_redis()
    cache_key = f"intraday:{code}:{interval}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    hour_cls_map = {"1min": "0", "5min": "5", "15min": "15", "1h": "60"}
    hour_cls = hour_cls_map.get(interval, "0")

    token = await get_access_token(
        settings.SYSTEM_KIS_APP_KEY, settings.SYSTEM_KIS_APP_SECRET, settings.SYSTEM_KIS_MODE
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_base(settings.SYSTEM_KIS_MODE)}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
                headers=_kis_headers(token, "FHKST03010200"),
                params={
                    "FID_ETC_CLS_CODE": "",
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code,
                    "FID_INPUT_HOUR_1": "090000",
                    "FID_PW_DATA_INCU_YN": "Y",
                    "FID_HOUR_CLS_CODE": hour_cls,
                },
            )
            resp.raise_for_status()
            output2 = resp.json().get("output2", [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"분봉 조회 실패: {exc}") from exc

    candles = [
        {
            "date": row.get("stck_bsop_date", ""),
            "time": row.get("stck_cntg_hour", ""),
            "open": int(row.get("stck_oprc", 0)),
            "high": int(row.get("stck_hgpr", 0)),
            "low": int(row.get("stck_lwpr", 0)),
            "close": int(row.get("stck_prpr", 0)),
            "volume": int(row.get("cntg_vol", 0)),
        }
        for row in output2
    ]
    await redis.setex(cache_key, 60, json.dumps(candles))
    return candles
