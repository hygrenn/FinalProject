import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from api.deps import get_current_user, get_db
from api.middleware.rate_limit import limiter
from models.portfolio import Portfolio
from models.trade import Trade
from models.user import User
from services import kis_service, risk_service
from services.market_service import get_stock_current_price
from tasks.order_tasks import poll_order_fill

router = APIRouter()


class OrderRequest(BaseModel):
    stock_code: str
    order_type: Literal["BUY", "SELL"]
    price_type: Literal["MARKET", "LIMIT"]
    quantity: int = Field(gt=0)
    price: int = Field(ge=0, default=0)

    @field_validator("stock_code")
    @classmethod
    def valid_stock_code(cls, v: str) -> str:
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("stock_code는 6자리 숫자여야 합니다.")
        return v

    @model_validator(mode="after")
    def limit_requires_price(self) -> "OrderRequest":
        if self.price_type == "LIMIT" and self.price <= 0:
            raise ValueError("LIMIT 주문은 price > 0 이어야 합니다.")
        return self


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

    if body.order_type == "SELL":
        result = await db.execute(
            select(Portfolio).where(
                Portfolio.user_id == user.id,
                Portfolio.stock_code == body.stock_code,
                Portfolio.mode == user.mode,
            ).with_for_update()
        )
        holding = result.scalar_one_or_none()
        pending_result = await db.execute(
            select(func.coalesce(func.sum(Trade.quantity - Trade.filled_quantity), 0)).where(
                Trade.user_id == user.id,
                Trade.stock_code == body.stock_code,
                Trade.mode == user.mode,
                Trade.order_type == "SELL",
                Trade.status.in_(["PENDING", "PARTIALLY_FILLED"]),
            )
        )
        pending_quantity = pending_result.scalar_one()
        available = (holding.quantity if holding else 0) - pending_quantity
        if available < body.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"매도 가능 수량 부족: {available}주 가능, {body.quantity}주 매도 요청",
            )

    # 시장가 주문은 현재가로 리스크 계산 (price=0이면 체크 우회되므로)
    risk_price = body.price
    if body.price_type == "MARKET":
        try:
            price_data = await get_stock_current_price(body.stock_code)
            risk_price = price_data.get("close", 0)
        except Exception:
            risk_price = 0
        if risk_price == 0:
            raise HTTPException(
                status_code=400,
                detail="시장가 주문의 현재가를 조회할 수 없습니다. 잠시 후 다시 시도하세요.",
            )

    warning = await risk_service.check_order(
        user, body.stock_code, body.order_type, body.quantity, risk_price, db
    )

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
    if trade.mode != user.mode:
        raise HTTPException(
            status_code=409,
            detail=f"주문 모드({trade.mode})와 현재 모드({user.mode})가 달라 취소할 수 없습니다.",
        )
    if not trade.kis_order_no:
        raise HTTPException(status_code=400, detail="KIS 주문번호가 없어 취소할 수 없습니다.")

    await kis_service.cancel_order(user, trade.kis_order_no)
    trade.status = "CANCELLED"
    await db.commit()
    return {"cancelled": True, "trade_id": trade_id}
