import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.deps import get_current_user, get_db
from main import app


def _mock_user(mode="paper"):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.mode = mode
    user.kis_paper_key_enc = "enc_key"
    return user


def _mock_db():
    """DB 세션 mock — 실제 DB 쓰기 없이 Trade 저장 시뮬레이션."""
    session = AsyncMock()
    trade_mock = MagicMock()
    trade_mock.id = uuid.uuid4()
    trade_mock.status = "PENDING"
    trade_mock.kis_order_no = "0000123456"

    async def fake_refresh(obj):
        # Trade 객체에 id 주입
        obj.id = trade_mock.id

    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = fake_refresh
    session.execute = AsyncMock()
    return session


async def test_order_uses_system_kis_mode(client):
    """주문 기록과 체결 폴링은 실제 시스템 KIS 모드를 사용한다."""
    user = _mock_user(mode="demo")
    db = _mock_db()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    try:
        with patch("api.routes.trades.settings.SYSTEM_KIS_MODE", "real"), \
             patch("api.routes.trades.risk_service.check_order", new_callable=AsyncMock, return_value=None), \
             patch("api.routes.trades.kis_service.place_order",
                   new_callable=AsyncMock, return_value={"kis_order_no": "0000123456"}), \
             patch("api.routes.trades.poll_order_fill") as mock_task:
            mock_task.delay = MagicMock()
            resp = await client.post("/trades/order", json={
                "stock_code": "005930", "order_type": "BUY",
                "price_type": "LIMIT", "quantity": 1, "price": 70000
            })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 200
    trade = db.add.call_args.args[0]
    assert trade.mode == "real"
    mock_task.delay.assert_called_once_with(
        str(trade.id), str(user.id), "0000123456", "real"
    )


async def test_order_returns_pending(client):
    """정상 주문은 PENDING 응답."""
    user = _mock_user()
    db = _mock_db()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    try:
        with patch("api.routes.trades.risk_service.check_order", new_callable=AsyncMock, return_value=None):
            with patch("api.routes.trades.kis_service.place_order",
                       new_callable=AsyncMock, return_value={"kis_order_no": "0000123456"}):
                with patch("api.routes.trades.poll_order_fill") as mock_task:
                    mock_task.delay = MagicMock()
                    resp = await client.post("/trades/order", json={
                        "stock_code": "005930", "order_type": "BUY",
                        "price_type": "LIMIT", "quantity": 1, "price": 70000
                    })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"


async def test_order_with_warning(client):
    """경고 모드에서 주문 통과 + warning 포함."""
    user = _mock_user()
    db = _mock_db()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    try:
        with patch("api.routes.trades.risk_service.check_order",
                   new_callable=AsyncMock, return_value="종목별 한도 초과: 25.0% > 20.0%"):
            with patch("api.routes.trades.kis_service.place_order",
                       new_callable=AsyncMock, return_value={"kis_order_no": "0000123456"}):
                with patch("api.routes.trades.poll_order_fill") as mock_task:
                    mock_task.delay = MagicMock()
                    resp = await client.post("/trades/order", json={
                        "stock_code": "005930", "order_type": "BUY",
                        "price_type": "LIMIT", "quantity": 1, "price": 70000
                    })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 200
    assert "warning" in resp.json()


async def test_get_trades_list(client):
    """주문 목록 조회."""
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        resp = await client.get("/trades")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_cancel_trade_not_found(client):
    """존재하지 않는 주문 취소 시 404."""
    user = _mock_user()
    fake_id = str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        resp = await client.delete(f"/trades/{fake_id}")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert resp.status_code == 404


async def test_order_risk_hard_stop(client):
    """hard_stop 리스크 차단 시 400."""
    from fastapi import HTTPException
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch("api.routes.trades.risk_service.check_order",
                   new_callable=AsyncMock, side_effect=HTTPException(400, "한도 초과")):
            resp = await client.post("/trades/order", json={
                "stock_code": "005930", "order_type": "BUY",
                "price_type": "LIMIT", "quantity": 1, "price": 70000
            })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert resp.status_code == 400
