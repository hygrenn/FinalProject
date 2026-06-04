from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.middleware.rate_limit import limiter
from models.ai_signal import AISignalHistory
from services import ai_service, pattern_service
from services.market_service import get_ohlcv_cached

router = APIRouter()


async def _get_ohlcv_df(code: str, period: str = "3m") -> pd.DataFrame:
    raw = await get_ohlcv_cached(code, period, "day")
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.set_index("date").sort_index()


@router.get("/top-picks")
@limiter.limit("20/minute")
async def get_top_picks(request: Request):
    return await ai_service.get_top_picks()


@router.get("/signals/history/{code}")
@limiter.limit("20/minute")
async def get_signals_history(
    request: Request, code: str, db: AsyncSession = Depends(get_db)
):
    cutoff = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(AISignalHistory)
        .where(AISignalHistory.stock_code == code)
        .where(AISignalHistory.recorded_at >= cutoff)
        .order_by(desc(AISignalHistory.recorded_at))
        .limit(100)
    )
    rows = result.scalars().all()
    return {
        "code": code,
        "history": [
            {
                "signal": r.signal,
                "signal_score": float(r.signal_score or 0),
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in rows
        ],
    }


@router.get("/{code}/signal")
@limiter.limit("20/minute")
async def get_signal(request: Request, code: str, db: AsyncSession = Depends(get_db)):
    return await ai_service.get_signal(code, db)


@router.get("/{code}/predict")
@limiter.limit("20/minute")
async def get_predict(request: Request, code: str):
    return await ai_service.get_prediction(code)


@router.get("/{code}/indicators")
@limiter.limit("20/minute")
async def get_indicators_endpoint(request: Request, code: str):
    result = await ai_service.get_indicators(code)
    if not result:
        raise HTTPException(status_code=404, detail="지표 계산 불가 (데이터 부족)")
    return result


@router.get("/{code}/patterns")
@limiter.limit("20/minute")
async def get_patterns(request: Request, code: str):
    df = await _get_ohlcv_df(code, "3m")
    patterns = pattern_service.detect_patterns(df)
    return {"code": code, "patterns": patterns}


@router.get("/{code}/similar")
@limiter.limit("20/minute")
async def get_similar(request: Request, code: str):
    return await ai_service.get_similar(code)


@router.get("/{code}/multiframe")
@limiter.limit("20/minute")
async def get_multiframe(request: Request, code: str):
    return await ai_service.get_multiframe(code)
