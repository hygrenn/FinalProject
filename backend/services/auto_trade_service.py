"""AI 기반 자동매매 서비스.

paper 모드: KIS API 없이 DB에 직접 FILLED 거래 기록 + portfolio 업데이트
real  모드: KIS API로 실제 주문 (SYSTEM_KIS_APP_KEY 필요)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.auto_trade import AutoTradeConfig, AutoTradeLog
from models.portfolio import Portfolio
from models.trade import Trade

logger = logging.getLogger(__name__)


async def get_config(user_id: UUID, db: AsyncSession) -> AutoTradeConfig:
    result = await db.execute(
        select(AutoTradeConfig).where(AutoTradeConfig.user_id == user_id)
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = AutoTradeConfig(user_id=user_id)
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
    return cfg


async def update_config(user_id: UUID, data: dict, db: AsyncSession) -> AutoTradeConfig:
    cfg = await get_config(user_id, db)
    allowed = {
        "enabled", "mode", "total_budget", "budget_per_trade",
        "max_positions", "signal_threshold", "stop_loss_pct",
        "take_profit_pct", "watch_codes",
    }
    for key, val in data.items():
        if key in allowed:
            setattr(cfg, key, val)
    await db.commit()
    await db.refresh(cfg)
    return cfg


async def get_logs(user_id: UUID, db: AsyncSession, limit: int = 50) -> list[dict]:
    result = await db.execute(
        select(AutoTradeLog)
        .where(AutoTradeLog.user_id == user_id)
        .order_by(AutoTradeLog.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "stock_code": r.stock_code,
            "stock_name": r.stock_name,
            "action": r.action,
            "quantity": r.quantity,
            "price": r.price,
            "total_amount": r.total_amount,
            "reason": r.reason,
            "signal_score": r.signal_score,
            "mode": r.mode,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


async def _count_positions(user_id: UUID, mode: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).where(Portfolio.user_id == user_id, Portfolio.mode == mode)
    )
    return result.scalar_one() or 0


async def _calc_used_budget(user_id: UUID, mode: str, db: AsyncSession) -> int:
    """현재 보유 종목의 총 매입금액 합산."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.mode == mode)
    )
    holdings = result.scalars().all()
    return sum(int(h.avg_price * h.quantity) for h in holdings)


async def _execute_paper_order(
    user_id: UUID,
    stock_code: str,
    stock_name: str,
    order_type: str,
    quantity: int,
    price: int,
    reason: str,
    mode: str,
    signal_score: float,
    db: AsyncSession,
) -> dict[str, Any]:
    """KIS 없이 paper/demo 모드 직접 체결."""
    if quantity <= 0 or price <= 0:
        raise ValueError(f"invalid quantity={quantity} or price={price}")

    total = quantity * price

    # Trade 기록
    trade = Trade(
        user_id=user_id,
        stock_code=stock_code,
        stock_name=stock_name,
        order_type=order_type,
        price_type="MARKET",
        quantity=quantity,
        executed_price=price,
        filled_quantity=quantity,
        status="FILLED",
        mode=mode,
        ai_signal_at_order=reason[:10] if reason else None,
        filled_at=datetime.now(timezone.utc),
    )
    db.add(trade)

    # Portfolio 업데이트
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == user_id,
            Portfolio.stock_code == stock_code,
            Portfolio.mode == mode,
        )
    )
    holding = result.scalar_one_or_none()

    if order_type == "BUY":
        if holding is None:
            db.add(Portfolio(
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                avg_price=price,
                mode=mode,
            ))
        else:
            new_qty = holding.quantity + quantity
            new_avg = (float(holding.avg_price) * holding.quantity + price * quantity) / new_qty
            holding.quantity = new_qty
            holding.avg_price = round(new_avg, 2)
    elif order_type == "SELL":
        if holding is None:
            # 보유 없는 매도 주문 방지
            raise ValueError(f"SELL 주문 실패: {stock_code} 보유 없음")
        sell_qty = min(quantity, holding.quantity)
        realized = int((price - float(holding.avg_price)) * sell_qty)
        trade.realized_pnl = realized
        trade.filled_quantity = sell_qty
        trade.quantity = sell_qty
        holding.quantity -= sell_qty
        if holding.quantity <= 0:
            await db.delete(holding)

    # 자동매매 로그
    log = AutoTradeLog(
        user_id=user_id,
        stock_code=stock_code,
        stock_name=stock_name,
        action=order_type,
        quantity=quantity,
        price=price,
        total_amount=total,
        reason=reason,
        signal_score=signal_score,
        mode=mode,
    )
    db.add(log)
    await db.commit()

    return {
        "action": order_type,
        "stock_code": stock_code,
        "quantity": quantity,
        "price": price,
        "total_amount": total,
        "reason": reason,
    }


async def run_cycle(user_id: UUID, db: AsyncSession) -> dict[str, Any]:
    """한 사용자에 대한 자동매매 사이클 실행."""
    from services import ai_service
    from services.market_service import get_stock_current_price

    cfg = await get_config(user_id, db)
    if not cfg.enabled:
        return {"skipped": True, "reason": "not_enabled"}

    watch_codes: list[str] = cfg.watch_codes or []
    if not watch_codes:
        return {"skipped": True, "reason": "no_watch_codes"}

    actions: list[dict] = []

    # ── 1. 기존 보유 포지션 손절/익절 체크 ───────────────────────────
    holdings_result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.mode == cfg.mode)
    )
    for holding in holdings_result.scalars().all():
        if holding.stock_code not in watch_codes:
            continue
        try:
            price_data = await get_stock_current_price(holding.stock_code)
            current_price = price_data.get("close", 0)
        except Exception:
            logger.warning("자동매매: 현재가 조회 실패 %s", holding.stock_code)
            continue
        if current_price <= 0:
            continue

        avg = float(holding.avg_price)
        pct = (current_price - avg) / avg * 100.0

        if pct <= -cfg.stop_loss_pct:
            try:
                log = await _execute_paper_order(
                    user_id, holding.stock_code, holding.stock_name or "",
                    "SELL", holding.quantity, current_price,
                    f"손절({pct:.1f}%)", cfg.mode, 0.0, db,
                )
                actions.append(log)
            except Exception as exc:
                logger.error("자동매매 손절 실패 %s: %s", holding.stock_code, exc)
        elif pct >= cfg.take_profit_pct:
            try:
                log = await _execute_paper_order(
                    user_id, holding.stock_code, holding.stock_name or "",
                    "SELL", holding.quantity, current_price,
                    f"익절({pct:.1f}%)", cfg.mode, 0.0, db,
                )
                actions.append(log)
            except Exception as exc:
                logger.error("자동매매 익절 실패 %s: %s", holding.stock_code, exc)

    # ── 2. AI 신호 기반 매수/매도 ─────────────────────────────────────
    pos_count = await _count_positions(user_id, cfg.mode, db)
    used_budget = await _calc_used_budget(user_id, cfg.mode, db)

    for code in watch_codes:
        try:
            signal_data = await ai_service.get_signal(code, db)
        except Exception:
            logger.warning("자동매매: AI 신호 조회 실패 %s", code)
            continue

        sig = signal_data.get("signal", "HOLD")
        score = float(signal_data.get("signal_score", 0))

        # 현재 보유 여부 확인
        holding_result = await db.execute(
            select(Portfolio).where(
                Portfolio.user_id == user_id,
                Portfolio.stock_code == code,
                Portfolio.mode == cfg.mode,
            )
        )
        holding = holding_result.scalar_one_or_none()

        if sig == "BUY" and score >= cfg.signal_threshold and holding is None:
            if pos_count >= cfg.max_positions:
                continue
            if used_budget + cfg.budget_per_trade > cfg.total_budget:
                continue
            try:
                price_data = await get_stock_current_price(code)
                current_price = price_data.get("close", 0)
            except Exception:
                continue
            if current_price <= 0:
                continue
            quantity = cfg.budget_per_trade // current_price
            if quantity < 1:
                continue

            stock_name = price_data.get("name", code)
            try:
                log = await _execute_paper_order(
                    user_id, code, stock_name, "BUY", quantity, current_price,
                    f"AI BUY({score:.0f}점)", cfg.mode, score, db,
                )
                actions.append(log)
                pos_count += 1
                used_budget += quantity * current_price
            except Exception as exc:
                logger.error("자동매매 매수 실패 %s: %s", code, exc)

        elif sig == "SELL" and holding is not None:
            try:
                price_data = await get_stock_current_price(code)
                current_price = price_data.get("close", 0)
            except Exception:
                continue
            if current_price <= 0:
                continue
            try:
                log = await _execute_paper_order(
                    user_id, code, holding.stock_name or code,
                    "SELL", holding.quantity, current_price,
                    f"AI SELL({score:.0f}점)", cfg.mode, score, db,
                )
                actions.append(log)
                pos_count -= 1
            except Exception as exc:
                logger.error("자동매매 매도 실패 %s: %s", code, exc)

    return {"executed": len(actions), "actions": actions}


async def kill_switch(user_id: UUID, db: AsyncSession) -> dict[str, Any]:
    """긴급 정지: 자동매매 비활성화."""
    cfg = await get_config(user_id, db)
    cfg.enabled = False
    await db.commit()
    return {"stopped": True, "message": "자동매매가 비활성화되었습니다."}
