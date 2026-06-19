"""자동매매 알고리즘 단위 테스트."""
import pytest

from services.auto_trade_service import _allocate, _calculate_buying_power


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
