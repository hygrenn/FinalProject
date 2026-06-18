# backend/services/backtest_service.py
from __future__ import annotations

import math
import uuid as _uuid
from dataclasses import dataclass
from datetime import date

import pandas as pd
from pykrx import stock as pykrx_stock
from sqlalchemy.ext.asyncio import AsyncSession

from ml.features import build_features
from models.backtest import BacktestResult
from services.ai_service import _calc_tech_score


@dataclass
class BacktestConfig:
    code: str
    start_date: date
    end_date: date
    initial_cash: int = 10_000_000
    entry_signal_score: float = 65.0
    exit_signal_score: float = 35.0
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15
    commission_rate: float = 0.00015


def _fetch_ohlcv(code: str, start_date: date, end_date: date) -> pd.DataFrame:
    """pykrx로 OHLCV 다운로드 후 DataFrame 반환."""
    df = pykrx_stock.get_market_ohlcv_by_date(
        start_date.strftime("%Y%m%d"),
        end_date.strftime("%Y%m%d"),
        code,
    )
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.rename(
        columns={"시가": "open", "고가": "high", "저가": "low", "종가": "close", "거래량": "volume"}
    )
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def _compute_daily_scores(df: pd.DataFrame) -> list[tuple[str, float, float]]:
    """
    날짜별 (date_str, price, tech_score) 리스트 반환.
    충분한 데이터가 없으면 빈 리스트.
    """
    feat_df = build_features(df)
    if feat_df.empty:
        return []

    results = []
    for idx, row in feat_df.iterrows():
        indicators = {
            "rsi_14": float(row.get("rsi_14", 50)),
            "macd_hist": float(row.get("macd_hist", 0)),
            "close": float(row.get("close", 0)),
            "bb_upper": float(row.get("bb_upper", 0)),
            "bb_lower": float(row.get("bb_lower", 0)),
        }
        score = _calc_tech_score(indicators)
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        results.append((date_str, float(row["close"]), score))
    return results


def _simulate(
    daily: list[tuple[str, float, float]],
    config: BacktestConfig,
) -> tuple[list[dict], list[float], dict | None]:
    """
    매매 시뮬레이션.
    반환: (trades_log, equity_curve, open_position)
    trades_log: [{entry_date, exit_date, entry_price, exit_price, shares, pnl, reason}]
    equity_curve: 날짜별 평가금액 리스트
    open_position: 기간 종료 시 미청산 포지션 정보 or None
    """
    cash = float(config.initial_cash)
    position = 0
    entry_price = 0.0
    entry_cost = 0.0
    trades_log: list[dict] = []
    equity_curve: list[float] = []
    entry_date = ""

    for date_str, price, score in daily:
        if price == 0:
            equity_curve.append(cash + position * (entry_price or 0))
            continue

        # 매수 조건
        if score >= config.entry_signal_score and position == 0:
            shares = int(cash * 0.95 / price)
            if shares > 0:
                cost = shares * price * (1 + config.commission_rate)
                cash -= cost
                position = shares
                entry_price = price
                entry_cost = cost
                entry_date = date_str

        # 청산 조건
        elif position > 0:
            change = (price - entry_price) / entry_price
            reason = None
            if score <= config.exit_signal_score:
                reason = "signal"
            elif change <= -config.stop_loss_pct:
                reason = "stop_loss"
            elif change >= config.take_profit_pct:
                reason = "take_profit"

            if reason:
                revenue = position * price * (1 - config.commission_rate)
                pnl = revenue - entry_cost
                trades_log.append({
                    "entry_date": entry_date,
                    "exit_date": date_str,
                    "entry_price": round(entry_price),
                    "exit_price": round(price),
                    "shares": position,
                    "pnl": round(pnl),
                    "reason": reason,
                })
                cash += revenue
                position = 0
                entry_price = 0.0
                entry_cost = 0.0

        equity_curve.append(cash + position * price)

    open_position = None
    if position > 0 and daily:
        last_price = daily[-1][1]
        open_position = {
            "shares": position,
            "entry_date": entry_date,
            "entry_price": round(entry_price),
            "last_price": round(last_price),
            "unrealized_pnl": round(position * last_price * (1 - config.commission_rate) - entry_cost),
        }

    return trades_log, equity_curve, open_position


def _compute_metrics(
    equity_curve: list[float],
    trades_log: list[dict],
    initial_cash: float,
) -> dict:
    """MDD, 샤프비율, 승률, 총 수익률 계산."""
    if not equity_curve:
        return {
            "total_return_pct": 0.0,
            "mdd_pct": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate_pct": 0.0,
        }

    # MDD
    peak = equity_curve[0]
    mdd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0
        if dd > mdd:
            mdd = dd

    # 샤프비율
    if len(equity_curve) > 1:
        daily_returns = [
            (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            for i in range(1, len(equity_curve))
            if equity_curve[i - 1] > 0
        ]
        if daily_returns:
            mean_r = sum(daily_returns) / len(daily_returns)
            std_r = math.sqrt(
                sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
            )
            sharpe = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0
        else:
            sharpe = 0.0
    else:
        sharpe = 0.0

    # 승률
    wins = sum(1 for t in trades_log if t["pnl"] > 0)
    win_rate = (wins / len(trades_log) * 100) if trades_log else 0.0

    # 총 수익률
    total_return = (equity_curve[-1] - initial_cash) / initial_cash * 100

    return {
        "total_return_pct": round(total_return, 4),
        "mdd_pct": round(mdd * 100, 4),
        "sharpe_ratio": round(sharpe, 4),
        "win_rate_pct": round(win_rate, 2),
    }


async def run_backtest(
    config: BacktestConfig,
    user_id,
    db: AsyncSession,
) -> BacktestResult:
    """
    백테스팅 실행 → BacktestResult DB 저장 → 반환.
    pykrx 동기 호출은 asyncio.to_thread 사용.
    """
    import asyncio

    if isinstance(user_id, str):
        user_id = _uuid.UUID(user_id)

    try:
        df = await asyncio.to_thread(_fetch_ohlcv, config.code, config.start_date, config.end_date)
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=f"시세 데이터 조회 실패: {exc}") from exc

    if df.empty:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"{config.code} 데이터를 가져올 수 없습니다.")

    daily = _compute_daily_scores(df)
    if not daily:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="지표 계산에 충분한 데이터가 없습니다.")

    trades_log, equity_curve, open_position = _simulate(daily, config)
    metrics = _compute_metrics(equity_curve, trades_log, config.initial_cash)

    dates = [d[0] for d in daily]
    equity_with_dates = [
        {"date": dates[i], "equity": round(equity_curve[i])}
        for i in range(0, len(equity_curve), 5)
    ]

    result_detail: dict = {"trades": trades_log, "equity_curve": equity_with_dates}
    if open_position:
        result_detail["open_position"] = open_position

    result = BacktestResult(
        user_id=user_id,
        stock_code=config.code,
        strategy_config={
            "entry_signal_score": config.entry_signal_score,
            "exit_signal_score": config.exit_signal_score,
            "stop_loss_pct": config.stop_loss_pct,
            "take_profit_pct": config.take_profit_pct,
            "commission_rate": config.commission_rate,
            "initial_cash": config.initial_cash,
        },
        period_start=config.start_date,
        period_end=config.end_date,
        total_return_pct=metrics["total_return_pct"],
        mdd_pct=metrics["mdd_pct"],
        sharpe_ratio=metrics["sharpe_ratio"],
        win_rate_pct=metrics["win_rate_pct"],
        total_trades=len(trades_log),
        result_detail=result_detail,
    )
    if user_id is not None:
        db.add(result)
        await db.commit()
        await db.refresh(result)
    return result
