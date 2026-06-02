from fastapi import APIRouter, Query, Request

from api.middleware.rate_limit import limiter
from services import market_service

router = APIRouter()


@router.get("")
@limiter.limit("100/minute")
async def list_stocks(
    request: Request,
    market: str = Query("kospi", pattern="^(kospi|kosdaq)$"),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
):
    return await market_service.get_stock_list(market, limit, page)


@router.get("/search")
@limiter.limit("100/minute")
async def search_stocks(request: Request, q: str = Query(..., min_length=1)):
    return await market_service.search_stocks(q)


@router.get("/indices")
@limiter.limit("100/minute")
async def get_indices(request: Request):
    return await market_service.get_indices()


@router.get("/{code}/chart")
@limiter.limit("100/minute")
async def get_stock_chart(
    request: Request,
    code: str,
    period: str = Query("1m", pattern="^(1w|1m|3m|6m|1y|3y)$"),
    interval: str = Query("day", pattern="^(day|week|month)$"),
):
    data = await market_service.get_ohlcv_cached(code, period, interval)
    return {"code": code, "period": period, "interval": interval, "data": data}


@router.get("/{code}")
@limiter.limit("100/minute")
async def get_stock_detail(request: Request, code: str):
    return await market_service.get_stock_current_price(code)
