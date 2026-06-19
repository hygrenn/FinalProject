"""자동매매 알고리즘 단위 테스트."""
import uuid

import pytest
from sqlalchemy import select

from models.auto_trade import AutoTradeLog
from models.portfolio import Portfolio
from models.trade import Trade
from models.user import User
from services.auto_trade_service import _allocate, _calculate_buying_power, _execute_paper_order


def test_allocate_caps_single_stock_at_30_percent():
    """단일 종목 배분이 총예산의 30%를 초과하지 않는다."""
    candidates = [{"code": "005930", "score": 100}]
    result = _allocate(candidates, available=500_000, total_budget=1_000_000)

    assert len(result) == 1
    assert result[0]["alloc"] == 300_000  # capped at 30% of 1_000_000


def test_calculate_buying_power_reserves_cash():
    """_calculate_buying_power 는 10% 현금 보유 후 가용 매수 금액을 반환한다."""
    # 투자된 금액이 없을 때: 1,000,000 * 0.9 = 900,000
    assert _calculate_buying_power(1_000_000, 0) == 900_000

    # 투자된 금액 800,000: 900,000 - 800,000 = 100,000
    assert _calculate_buying_power(1_000_000, 800_000) == 100_000

    # 투자된 금액이 investable_limit 과 같을 때: 0
    assert _calculate_buying_power(1_000_000, 900_000) == 0

    # 투자된 금액이 investable_limit 초과: 음수가 되어선 안 됨 → 0
    assert _calculate_buying_power(1_000_000, 950_000) == 0


@pytest.mark.asyncio
async def test_execute_paper_sell_logs_actual_filled_quantity(db_session):
    """SELL 시 holding 수량보다 많이 요청해도 AutoTradeLog/반환값은 실제 체결 수량 기준이어야 한다."""
    # 1. 사용자 생성
    user_id = uuid.uuid4()
    db_session.add(User(
        id=user_id,
        email=f"algo-test-{uuid.uuid4().hex[:6]}@test.com",
        password_hash="x",
        is_verified=True,
    ))
    await db_session.flush()

    # 2. Portfolio: 005930 보유 수량 5주
    db_session.add(Portfolio(
        user_id=user_id,
        stock_code="005930",
        stock_name="삼성전자",
        quantity=5,
        avg_price=10_000,
        mode="paper",
    ))
    await db_session.flush()

    # 3. SELL 10주 요청 (보유는 5주)
    result = await _execute_paper_order(
        user_id=user_id,
        stock_code="005930",
        stock_name="삼성전자",
        order_type="SELL",
        quantity=10,
        price=11_000,
        reason="손절",
        mode="paper",
        signal_score=0.0,
        db=db_session,
    )

    # 4. Trade 검증
    trade_res = await db_session.execute(
        select(Trade).where(Trade.user_id == user_id, Trade.stock_code == "005930")
    )
    trade = trade_res.scalar_one()
    assert trade.quantity == 5, f"Trade.quantity expected 5, got {trade.quantity}"
    assert trade.filled_quantity == 5, f"Trade.filled_quantity expected 5, got {trade.filled_quantity}"
    assert trade.realized_pnl == 5_000, f"Trade.realized_pnl expected 5000, got {trade.realized_pnl}"

    # 5. AutoTradeLog 검증
    log_res = await db_session.execute(
        select(AutoTradeLog).where(AutoTradeLog.user_id == user_id, AutoTradeLog.stock_code == "005930")
    )
    log = log_res.scalar_one()
    assert log.quantity == 5, f"AutoTradeLog.quantity expected 5, got {log.quantity}"
    assert log.total_amount == 55_000, f"AutoTradeLog.total_amount expected 55000, got {log.total_amount}"

    # 6. 반환값 검증
    assert result["quantity"] == 5, f"return quantity expected 5, got {result['quantity']}"
    assert result["total_amount"] == 55_000, f"return total_amount expected 55000, got {result['total_amount']}"


@pytest.mark.asyncio
async def test_execute_paper_buy_updates_average_price_and_log_amount(db_session):
    """BUY 시 평균단가 갱신이 올바르고 AutoTradeLog/반환값도 executed_qty 기준이어야 한다."""
    # 1. 사용자 생성
    user_id = uuid.uuid4()
    db_session.add(User(
        id=user_id,
        email=f"algo-test-{uuid.uuid4().hex[:6]}@test.com",
        password_hash="x",
        is_verified=True,
    ))
    await db_session.flush()

    # 2. Portfolio: 000660 보유 수량 2주, 평균 50,000원
    db_session.add(Portfolio(
        user_id=user_id,
        stock_code="000660",
        stock_name="SK하이닉스",
        quantity=2,
        avg_price=50_000,
        mode="paper",
    ))
    await db_session.flush()

    # 3. BUY 3주 @ 60,000원
    result = await _execute_paper_order(
        user_id=user_id,
        stock_code="000660",
        stock_name="SK하이닉스",
        order_type="BUY",
        quantity=3,
        price=60_000,
        reason="AI BUY",
        mode="paper",
        signal_score=80.0,
        db=db_session,
    )

    # 4. Portfolio 검증: 수량 5, 평균단가 56,000
    port_res = await db_session.execute(
        select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.stock_code == "000660")
    )
    portfolio = port_res.scalar_one()
    assert portfolio.quantity == 5, f"Portfolio.quantity expected 5, got {portfolio.quantity}"
    assert float(portfolio.avg_price) == 56_000.0, f"Portfolio.avg_price expected 56000, got {portfolio.avg_price}"

    # 5. AutoTradeLog 검증
    log_res = await db_session.execute(
        select(AutoTradeLog).where(AutoTradeLog.user_id == user_id, AutoTradeLog.stock_code == "000660")
    )
    log = log_res.scalar_one()
    assert log.quantity == 3, f"AutoTradeLog.quantity expected 3, got {log.quantity}"
    assert log.total_amount == 180_000, f"AutoTradeLog.total_amount expected 180000, got {log.total_amount}"

    # 6. 반환값 검증
    assert result["quantity"] == 3, f"return quantity expected 3, got {result['quantity']}"
    assert result["total_amount"] == 180_000, f"return total_amount expected 180000, got {result['total_amount']}"


@pytest.mark.asyncio
async def test_execute_paper_sell_raises_when_holding_quantity_is_zero(db_session):
    """SELL 시 보유 수량이 0이면 ValueError를 발생시킨다."""
    user_id = uuid.uuid4()
    db_session.add(User(
        id=user_id,
        email=f"algo-test-{uuid.uuid4().hex[:6]}@test.com",
        password_hash="x",
        is_verified=True,
    ))
    await db_session.flush()

    # Portfolio quantity=0 (dirty data scenario)
    db_session.add(Portfolio(
        user_id=user_id,
        stock_code="005380",
        stock_name="현대차",
        quantity=0,
        avg_price=100_000,
        mode="paper",
    ))
    await db_session.flush()

    with pytest.raises(ValueError, match="데이터 오염"):
        await _execute_paper_order(
            user_id=user_id,
            stock_code="005380",
            stock_name="현대차",
            order_type="SELL",
            quantity=1,
            price=105_000,
            reason="손절",
            mode="paper",
            signal_score=0.0,
            db=db_session,
        )
