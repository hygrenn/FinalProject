"""종합 분석 라우트 — 재무 평가 / 추천 종목 / 지수 컨텍스트.

기존 라우트를 수정하지 않고 추가하는 신규 엔드포인트.
데이터 소스는 키 불필요한 네이버 금융(실데이터).
"""
from fastapi import APIRouter, Query, Request

from api.middleware.rate_limit import limiter
from services import comprehensive_service, fundamental_service, market_index_service, recommend_service

router = APIRouter()


@router.get("/fundamental/{code}")
@limiter.limit("60/minute")
async def get_fundamental(request: Request, code: str):
    """종목 재무 평가 (5.0 만점, 소수 1자리, 2.5 미만이면 위험)."""
    return await fundamental_service.get_fundamental(code)


@router.get("/recommendations")
@limiter.limit("20/minute")
async def get_recommendations(request: Request, limit: int = Query(20, ge=1, le=50)):
    """top100 전체 스캔 → AI BUY + 재무·지수 보조 필터로 추천 종목."""
    return await recommend_service.get_recommendations(limit)


@router.get("/indices")
@limiter.limit("60/minute")
async def get_indices(request: Request):
    """KOSPI/KOSDAQ/KOSPI200 + 시장 추세."""
    return await market_index_service.get_index_context()


@router.get("/comprehensive/{code}")
@limiter.limit("30/minute")
async def get_comprehensive(request: Request, code: str):
    """AI 시그널 + 재무 평가 + 시장 지수 → 종합 판단 (0-10점)."""
    return await comprehensive_service.get_comprehensive(code)
