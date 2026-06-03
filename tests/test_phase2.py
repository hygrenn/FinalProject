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
