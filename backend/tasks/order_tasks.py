import asyncio
import uuid

from tasks import celery_app


@celery_app.task(bind=True, max_retries=5, default_retry_delay=10)
def poll_order_fill(self, trade_id: str, user_id: str, kis_order_no: str, mode: str) -> None:
    """KIS 체결 폴링 (10초 간격, 최대 5회). 체결 시 trades/portfolios 업데이트 + 이메일."""
    asyncio.run(_poll_async(self, trade_id, user_id, kis_order_no, mode))


async def _poll_async(task, trade_id: str, user_id: str, kis_order_no: str, mode: str) -> None:
    from core.database import AsyncSessionLocal
    from models.portfolio import Portfolio
    from models.trade import Trade
    from models.user import User
    from services import kis_service
    from sqlalchemy import select, update
    from tasks.email_tasks import send_fill_notification

    trade_uuid = uuid.UUID(trade_id)
    user_uuid = uuid.UUID(user_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
        if not user:
            return

        fill = await kis_service.poll_fill(user, kis_order_no)
        if fill is None:
            if task.request.retries < task.max_retries:
                raise task.retry()
            # 최대 재시도 초과 → UNKNOWN으로 표시 (수동 확인 필요)
            await db.execute(
                update(Trade)
                .where(Trade.id == trade_uuid)
                .values(status="UNKNOWN")
            )
            await db.commit()
            return

        await db.execute(
            update(Trade)
            .where(Trade.id == trade_uuid)
            .values(
                status="FILLED",
                executed_price=fill["executed_price"],
                filled_at=fill.get("filled_at"),
            )
        )

        result2 = await db.execute(select(Trade).where(Trade.id == trade_uuid))
        trade = result2.scalar_one_or_none()

        if trade:
            await _update_portfolio(db, trade, fill["executed_price"])

        await db.commit()

    send_fill_notification.delay(user_id, trade_id)


async def _update_portfolio(db, trade, executed_price: int) -> None:
    """체결 후 portfolios 테이블 UPSERT."""
    from models.portfolio import Portfolio
    from sqlalchemy import select

    result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == trade.user_id,
            Portfolio.stock_code == trade.stock_code,
            Portfolio.mode == trade.mode,
        )
    )
    holding = result.scalar_one_or_none()

    if trade.order_type == "BUY":
        if holding is None:
            db.add(Portfolio(
                user_id=trade.user_id,
                stock_code=trade.stock_code,
                stock_name=trade.stock_name,
                quantity=trade.quantity,
                avg_price=executed_price,
                mode=trade.mode,
            ))
        else:
            total_qty = holding.quantity + trade.quantity
            new_avg = (holding.avg_price * holding.quantity + executed_price * trade.quantity) / total_qty
            holding.quantity = total_qty
            holding.avg_price = round(new_avg, 2)
    elif trade.order_type == "SELL" and holding:
        # 체결 전 평균매수가 기준 실현손익 계산
        trade.realized_pnl = int((executed_price - float(holding.avg_price)) * trade.quantity)
        holding.quantity -= trade.quantity
        if holding.quantity <= 0:
            await db.delete(holding)
