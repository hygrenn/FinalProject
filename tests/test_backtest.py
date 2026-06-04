# tests/test_backtest.py
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.deps import get_current_user


def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.mode = "paper"
    return user


def _mock_result():
    r = MagicMock()
    r.id = uuid.uuid4()
    r.stock_code = "005930"
    r.period_start = date(2024, 1, 1)
    r.period_end = date(2025, 1, 1)
    r.total_return_pct = 12.34
    r.mdd_pct = 5.21
    r.sharpe_ratio = 1.45
    r.win_rate_pct = 60.0
    r.total_trades = 6
    r.strategy_config = {"entry_signal_score": 65.0}
    r.result_detail = {"trades": [], "equity_curve": []}
    r.created_at = None
    return r


async def test_run_backtest_returns_result(client):
    """정상 요청은 200 + 필수 필드 반환."""
    from main import app

    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "api.routes.backtest.backtest_service.run_backtest",
        new_callable=AsyncMock,
        return_value=_mock_result(),
    ):
        resp = await client.post(
            "/backtest/run",
            json={
                "code": "005930",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
            },
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "total_return_pct" in data
    assert "mdd_pct" in data
    assert "win_rate_pct" in data
    assert "sharpe_ratio" in data


async def test_run_backtest_invalid_dates(client):
    """end_date <= start_date → 422."""
    from main import app

    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    resp = await client.post(
        "/backtest/run",
        json={
            "code": "005930",
            "start_date": "2025-01-01",
            "end_date": "2024-01-01",
        },
    )

    app.dependency_overrides.clear()
    assert resp.status_code == 422


async def test_get_backtest_not_found(client):
    """존재하지 않는 id → 404."""
    from main import app

    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    resp = await client.get(f"/backtest/{uuid.uuid4()}")
    app.dependency_overrides.clear()
    assert resp.status_code == 404


async def test_get_backtest_success(client, db_session):
    """DB에 직접 삽입한 결과를 조회."""
    from main import app
    from models.backtest import BacktestResult
    from models.user import User
    from sqlalchemy import select

    result = await db_session.execute(select(User).limit(1))
    user_row = result.scalar_one_or_none()
    if user_row is None:
        pytest.skip("No user in test DB")

    app.dependency_overrides[get_current_user] = lambda: user_row

    backtest = BacktestResult(
        user_id=user_row.id,
        stock_code="005930",
        strategy_config={"entry_signal_score": 65.0},
        period_start=date(2024, 1, 1),
        period_end=date(2025, 1, 1),
        total_return_pct=10.0,
        mdd_pct=5.0,
        sharpe_ratio=1.2,
        win_rate_pct=55.0,
        total_trades=4,
        result_detail={"trades": [], "equity_curve": []},
    )
    db_session.add(backtest)
    await db_session.commit()
    await db_session.refresh(backtest)

    resp = await client.get(f"/backtest/{backtest.id}")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["stock_code"] == "005930"
