# tests/test_simulate.py
import pytest
from datetime import date


# ──── 단위 테스트 (DB/pykrx 없이 실행 가능) ────────────────────────

def _make_prices():
    """2024-01-02 ~ 2024-01-10 삼성전자 가격 픽스처 (주말 제외)."""
    return {
        "2024-01-02": 70000.0,
        "2024-01-03": 71000.0,
        "2024-01-04": 72000.0,
        "2024-01-05": 73000.0,
        "2024-01-08": 74000.0,
        "2024-01-09": 73500.0,
        "2024-01-10": 75000.0,
    }


def test_calc_lumpsum_logic():
    """100만원으로 70000원 주식 14주 매수 → 매도가 기반 수익 계산."""
    from services.simulator_service import calc_lumpsum

    prices = _make_prices()
    result = calc_lumpsum(
        ticker="005930",
        buy_date=date(2024, 1, 2),
        sell_date=date(2024, 1, 10),
        amount_krw=1_000_000,
        prices=prices,
        name="삼성전자",
    )

    assert result["shares"] == 14         # int(1_000_000 / 70000)
    assert result["buy_price"] == 70000
    assert result["sell_price"] == 75000
    assert result["buy_value_krw"] == 980_000   # 14 * 70000
    assert result["sell_value_krw"] == 1_050_000  # 14 * 75000
    assert result["profit_krw"] == 70_000
    assert result["return_pct"] == pytest.approx(7.1429, abs=0.01)
    assert result["buy_date_actual"] == "2024-01-02"
    assert result["sell_date_actual"] == "2024-01-10"
    assert len(result["chart_data"]) == len(prices)
    assert result["chart_data"][0] == {"date": "2024-01-02", "return_pct": 0.0}


def test_calc_lumpsum_weekend_adjustment():
    """토요일 매수일 → 다음 월요일로 조정."""
    from services.simulator_service import calc_lumpsum

    prices = _make_prices()
    result = calc_lumpsum(
        ticker="005930",
        buy_date=date(2024, 1, 6),   # 토요일
        sell_date=date(2024, 1, 10),
        amount_krw=1_000_000,
        prices=prices,
        name="삼성전자",
    )
    assert result["buy_date_actual"] == "2024-01-08"   # 다음 월요일


def test_calc_recurring_logic():
    """3개월 적립: 매월 첫 영업일에 매수."""
    from services.simulator_service import calc_recurring

    prices = {
        "2024-01-02": 70000.0,
        "2024-02-01": 72000.0,
        "2024-03-04": 68000.0,
        "2024-03-31": 69000.0,  # 마지막 날
    }
    result = calc_recurring(
        ticker="005930",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        monthly_amount_krw=300_000,
        prices=prices,
        name="삼성전자",
    )

    # 1월: int(300000/70000)=4주, 2월: int(300000/72000)=4주, 3월: int(300000/68000)=4주
    assert result["total_purchases"] == 3
    assert result["total_shares"] == 12    # 4+4+4
    jan_invested = 4 * 70000               # 280000
    feb_invested = 4 * 72000               # 288000
    mar_invested = 4 * 68000               # 272000
    assert result["total_invested_krw"] == jan_invested + feb_invested + mar_invested
    # 최종가 69000
    assert result["current_value_krw"] == 12 * 69000
    assert len(result["chart_data"]) == 3
