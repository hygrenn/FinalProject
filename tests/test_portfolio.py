import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.deps import get_current_user


def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.mode = "paper"
    return user


async def test_portfolio_empty(client):
    """보유종목 없으면 빈 리스트."""
    from main import app
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    with patch("api.routes.portfolio._get_holdings", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/portfolio")

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["holdings"] == []


async def test_portfolio_with_holdings(client):
    """보유종목 있으면 수익률 계산 포함."""
    from main import app
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    mock_holding = MagicMock()
    mock_holding.stock_code = "005930"
    mock_holding.stock_name = "삼성전자"
    mock_holding.quantity = 10
    mock_holding.avg_price = 70000
    mock_holding.mode = "paper"

    with patch("api.routes.portfolio._get_holdings",
               new_callable=AsyncMock, return_value=[mock_holding]):
        with patch("api.routes.portfolio.get_stock_current_price",
                   new_callable=AsyncMock, return_value={"close": 75000}):
            resp = await client.get("/portfolio")

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["holdings"]) == 1
    assert data["holdings"][0]["return_pct"] > 0


async def test_portfolio_metrics(client):
    """metrics 엔드포인트는 mdd_pct/win_rate_pct/sharpe_ratio 포함."""
    from main import app
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    resp = await client.get("/portfolio/metrics")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert "mdd_pct" in data
    assert "win_rate_pct" in data
    assert "sharpe_ratio" in data


async def test_portfolio_export_csv(client):
    """CSV export는 text/csv Content-Type 반환."""
    from main import app
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    with patch("api.routes.portfolio._get_holdings", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/portfolio/export")

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


async def test_portfolio_performance(client):
    """performance 엔드포인트 200 응답, 리스트 반환."""
    from main import app
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    resp = await client.get("/portfolio/performance")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
