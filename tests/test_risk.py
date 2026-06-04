# tests/test_risk.py
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_risk_settings(max_per_stock_pct=20.0, daily_loss_limit_pct=5.0, enforce_hard_stop=True):
    rs = MagicMock()
    rs.max_per_stock_pct = Decimal(str(max_per_stock_pct))
    rs.daily_loss_limit_pct = Decimal(str(daily_loss_limit_pct))
    rs.enforce_hard_stop = enforce_hard_stop
    return rs


async def test_check_order_passes_within_limit(client):
    """한도 미초과 주문은 통과."""
    from services.risk_service import check_order

    user = MagicMock()
    user.id = uuid.uuid4()
    user.mode = "paper"
    db = AsyncMock()

    with patch("services.risk_service.get_or_create_settings", new_callable=AsyncMock,
               return_value=_make_risk_settings(max_per_stock_pct=50.0)):
        with patch("services.risk_service._get_portfolio_total", new_callable=AsyncMock, return_value=1_000_000):
            with patch("services.risk_service._get_holding_value", new_callable=AsyncMock, return_value=100_000):
                with patch("services.risk_service._get_today_loss", new_callable=AsyncMock, return_value=0):
                    result = await check_order(user, "005930", 1, 50_000, db)
                    assert result is None


async def test_check_order_hard_stop_raises(client):
    """enforce_hard_stop=True이고 한도 초과 시 400."""
    from fastapi import HTTPException
    from services.risk_service import check_order

    user = MagicMock()
    user.id = uuid.uuid4()
    user.mode = "paper"
    db = AsyncMock()

    with patch("services.risk_service.get_or_create_settings", new_callable=AsyncMock,
               return_value=_make_risk_settings(max_per_stock_pct=10.0, enforce_hard_stop=True)):
        with patch("services.risk_service._get_portfolio_total", new_callable=AsyncMock, return_value=1_000_000):
            with patch("services.risk_service._get_holding_value", new_callable=AsyncMock, return_value=500_000):
                with patch("services.risk_service._get_today_loss", new_callable=AsyncMock, return_value=0):
                    with pytest.raises(HTTPException) as exc_info:
                        await check_order(user, "005930", 1, 50_000, db)
                    assert exc_info.value.status_code == 400


async def test_check_order_warning_mode(client):
    """enforce_hard_stop=False이고 한도 초과 시 경고 문자열 반환."""
    from services.risk_service import check_order

    user = MagicMock()
    user.id = uuid.uuid4()
    user.mode = "paper"
    db = AsyncMock()

    with patch("services.risk_service.get_or_create_settings", new_callable=AsyncMock,
               return_value=_make_risk_settings(max_per_stock_pct=10.0, enforce_hard_stop=False)):
        with patch("services.risk_service._get_portfolio_total", new_callable=AsyncMock, return_value=1_000_000):
            with patch("services.risk_service._get_holding_value", new_callable=AsyncMock, return_value=500_000):
                with patch("services.risk_service._get_today_loss", new_callable=AsyncMock, return_value=0):
                    result = await check_order(user, "005930", 1, 50_000, db)
                    assert result is not None
                    assert "한도" in result
