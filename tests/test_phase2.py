# tests/test_phase2.py
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── Task 1: KIS Token Service ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_access_token_fetches_and_caches():
    """access_token을 KIS에서 받아 Redis에 캐시한다."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # 캐시 miss

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"access_token": "tok_abc", "expires_in": 86400}

    with patch("services.kis_token_service.get_redis", return_value=mock_redis), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_client_cls.return_value = mock_client

        from services.kis_token_service import get_access_token
        token = await get_access_token("key", "secret", "paper")

    assert token == "tok_abc"
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert "access_token" in args[0]
    assert args[1] == 86340  # expires_in - 60


@pytest.mark.asyncio
async def test_get_access_token_uses_cache():
    """캐시된 access_token이 있으면 KIS를 호출하지 않는다."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"tok_cached"

    with patch("services.kis_token_service.get_redis", return_value=mock_redis), \
         patch("httpx.AsyncClient") as mock_client_cls:
        from services.kis_token_service import get_access_token
        token = await get_access_token("key", "secret", "paper")

    assert token == "tok_cached"
    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_get_approval_key_fetches_and_caches():
    """approval_key를 KIS에서 받아 Redis에 82800초로 캐시한다."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"approval_key": "approv_xyz"}

    with patch("services.kis_token_service.get_redis", return_value=mock_redis), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_client_cls.return_value = mock_client

        from services.kis_token_service import get_approval_key
        key = await get_approval_key("key", "secret", "paper")

    assert key == "approv_xyz"
    args = mock_redis.setex.call_args[0]
    assert args[1] == 82800


@pytest.mark.asyncio
async def test_get_access_token_raises_502_on_kis_error():
    """KIS가 에러를 반환하면 HTTPException 502를 발생시킨다."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("services.kis_token_service.get_redis", return_value=mock_redis), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=Exception("connection refused"))
        mock_client_cls.return_value = mock_client

        from fastapi import HTTPException
        from services.kis_token_service import get_access_token
        with pytest.raises(HTTPException) as exc_info:
            await get_access_token("key", "secret", "paper")
    assert exc_info.value.status_code == 502


# ─── Task 2: KIS REST Market Service ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_orderbook_returns_empty_when_no_system_key():
    """SYSTEM_KIS_APP_KEY가 없으면 빈 호가를 반환한다."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = ""
        from services.kis_market_service import get_orderbook
        result = await get_orderbook("005930")
    assert result == {"code": "005930", "asks": [], "bids": []}


@pytest.mark.asyncio
async def test_get_orderbook_parses_kis_response():
    """KIS 응답을 10단 호가 형태로 파싱한다."""
    fake_output1 = {
        "askp1": "60100", "askp_rsqn1": "500",
        "askp2": "60200", "askp_rsqn2": "300",
        **{f"askp{i}": str(60100 + (i-1)*100) for i in range(3, 11)},
        **{f"askp_rsqn{i}": "100" for i in range(3, 11)},
        "bidp1": "60000", "bidp_rsqn1": "1000",
        "bidp2": "59900", "bidp_rsqn2": "800",
        **{f"bidp{i}": str(60000 - (i-1)*100) for i in range(3, 11)},
        **{f"bidp_rsqn{i}": "200" for i in range(3, 11)},
    }
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"output1": fake_output1}

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("services.kis_market_service.settings") as mock_settings, \
         patch("services.kis_market_service.get_access_token", return_value="tok"), \
         patch("services.kis_market_service.get_redis", return_value=mock_redis), \
         patch("httpx.AsyncClient") as mock_cls:
        mock_settings.SYSTEM_KIS_APP_KEY = "testkey"
        mock_settings.SYSTEM_KIS_APP_SECRET = "testsecret"
        mock_settings.SYSTEM_KIS_MODE = "paper"
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_cls.return_value = mock_client

        from services.kis_market_service import get_orderbook
        result = await get_orderbook("005930")

    assert len(result["asks"]) == 10
    assert len(result["bids"]) == 10
    assert result["asks"][0] == {"price": 60100, "qty": 500}
    assert result["bids"][0] == {"price": 60000, "qty": 1000}


@pytest.mark.asyncio
async def test_get_intraday_ohlcv_returns_empty_when_no_system_key():
    """SYSTEM_KIS_APP_KEY가 없으면 빈 분봉 데이터를 반환한다."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = ""
        from services.kis_market_service import get_intraday_ohlcv
        result = await get_intraday_ohlcv("005930", "1min")
    assert result == []


@pytest.mark.asyncio
async def test_get_recent_trades_returns_empty_when_no_system_key():
    """SYSTEM_KIS_APP_KEY가 없으면 빈 체결 목록을 반환한다."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = ""
        from services.kis_market_service import get_recent_trades
        result = await get_recent_trades("005930")
    assert result == []


@pytest.mark.asyncio
async def test_get_orderbook_raises_502_on_kis_error():
    """KIS 호가 API 실패 시 HTTPException 502를 반환한다."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("services.kis_market_service.settings") as mock_settings, \
         patch("services.kis_market_service.get_access_token", return_value="tok"), \
         patch("services.kis_market_service.get_redis", return_value=mock_redis), \
         patch("httpx.AsyncClient") as mock_cls:
        mock_settings.SYSTEM_KIS_APP_KEY = "key"
        mock_settings.SYSTEM_KIS_APP_SECRET = "secret"
        mock_settings.SYSTEM_KIS_MODE = "paper"
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("timeout"))
        mock_cls.return_value = mock_client

        from fastapi import HTTPException
        from services.kis_market_service import get_orderbook
        with pytest.raises(HTTPException) as exc_info:
            await get_orderbook("005930")
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_get_intraday_ohlcv_rejects_invalid_interval():
    """알 수 없는 interval은 HTTPException 400을 반환한다."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = "key"
        mock_settings.SYSTEM_KIS_APP_SECRET = "secret"
        mock_settings.SYSTEM_KIS_MODE = "paper"
        from fastapi import HTTPException
        from services.kis_market_service import get_intraday_ohlcv
        with pytest.raises(HTTPException) as exc_info:
            await get_intraday_ohlcv("005930", "30min")
    assert exc_info.value.status_code == 400


# ─── Task 3: Chart + Orderbook/Trades Routes ─────────────────────────────────

@pytest.mark.asyncio
async def test_chart_intraday_returns_empty_without_system_key(client):
    """분봉 요청 시 system KIS 키가 없으면 빈 data를 반환한다 (200)."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = ""
        response = await client.get("/stocks/005930/chart?period=1d&interval=1min")
    assert response.status_code == 200
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_chart_1d_period_accepted(client):
    """period=1d가 유효한 값으로 받아들여진다."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex = AsyncMock()
    with patch("services.market_service.get_ohlcv_from_pykrx", return_value=[]), \
         patch("services.market_service.get_redis", return_value=mock_redis):
        response = await client.get("/stocks/005930/chart?period=1d&interval=day")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chart_invalid_interval_rejected(client):
    """지원하지 않는 interval은 422를 반환한다."""
    response = await client.get("/stocks/005930/chart?interval=2min")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_orderbook_endpoint_returns_empty_without_system_key(client):
    """GET /stocks/{code}/orderbook: system 키 없으면 빈 asks/bids 반환."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = ""
        response = await client.get("/stocks/005930/orderbook")
    assert response.status_code == 200
    data = response.json()
    assert data["asks"] == []
    assert data["bids"] == []


@pytest.mark.asyncio
async def test_trades_endpoint_returns_empty_without_system_key(client):
    """GET /stocks/{code}/trades: system 키 없으면 빈 목록 반환."""
    with patch("services.kis_market_service.settings") as mock_settings:
        mock_settings.SYSTEM_KIS_APP_KEY = ""
        response = await client.get("/stocks/005930/trades")
    assert response.status_code == 200
    assert response.json() == []
