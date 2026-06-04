import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.middleware.rate_limit import limiter
from models.trade import Trade
from models.user import User
from services import kis_service, risk_service
from tasks.order_tasks import poll_order_fill

router = APIRouter()


class OrderRequest(BaseModel):
    stock_code: str
    order_type: str   # "BUY" | "SELL"
    price_type: str   # "MARKET" | "LIMIT"
    quantity: int
    price: int = 0


@router.post("/order")
@limiter.limit("30/minute")
async def place_order(
    request: Request,
    body: OrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.mode == "demo":
        raise HTTPException(status_code=403, detail="KIS 키를 먼저 등록하세요.")

    warning = await risk_service.check_order(user, body.stock_code, body.quantity, body.price, db)

    result = await kis_service.place_order(
        user, body.stock_code, body.order_type, body.price_type, body.quantity, body.price
    )
    kis_order_no = result["kis_order_no"]

    trade = Trade(
        user_id=user.id,
        stock_code=body.stock_code,
        order_type=body.order_type,
        price_type=body.price_type,
        quantity=body.quantity,
        order_price=body.price if body.price_type == "LIMIT" else None,
        status="PENDING",
        mode=user.mode,
        kis_order_no=kis_order_no,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)

    poll_order_fill.delay(str(trade.id), str(user.id), kis_order_no, user.mode)

    response: dict = {"trade_id": str(trade.id), "status": "PENDING", "kis_order_no": kis_order_no}
    if warning:
        response["warning"] = warning
    return response


@router.get("")
@limiter.limit("60/minute")
async def list_trades(
    request: Request,
    status: str | None = None,
    mode: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Trade).where(Trade.user_id == user.id)
    if status:
        query = query.where(Trade.status == status)
    if mode:
        query = query.where(Trade.mode == mode)
    else:
        query = query.where(Trade.mode == user.mode)
    query = query.order_by(Trade.created_at.desc()).limit(100)

    result = await db.execute(query)
    trades = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "stock_code": t.stock_code,
            "order_type": t.order_type,
            "quantity": t.quantity,
            "order_price": float(t.order_price) if t.order_price else None,
            "executed_price": float(t.executed_price) if t.executed_price else None,
            "status": t.status,
            "mode": t.mode,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in trades
    ]


@router.delete("/{trade_id}")
@limiter.limit("20/minute")
async def cancel_trade(
    request: Request,
    trade_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tid = uuid.UUID(trade_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 trade_id")

    result = await db.execute(
        select(Trade).where(Trade.id == tid, Trade.user_id == user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    if trade.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"취소 불가 상태: {trade.status}")

    await kis_service.cancel_order(user, trade.kis_order_no)
    trade.status = "CANCELLED"
    await db.commit()
    return {"cancelled": True, "trade_id": trade_id}
