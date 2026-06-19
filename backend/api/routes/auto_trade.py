from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.middleware.rate_limit import limiter
from models.user import User
from services import auto_trade_service

router = APIRouter()


class AutoTradeConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    total_budget: Optional[int] = Field(default=None, gt=0)
    stop_loss_pct: Optional[float] = Field(default=None, ge=1.0, le=30.0)
    take_profit_pct: Optional[float] = Field(default=None, ge=1.0, le=100.0)

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v: str) -> str:
        if v not in ("paper", "real"):
            raise ValueError("mode는 'paper' 또는 'real'이어야 합니다.")
        return v


def _cfg_to_dict(cfg: Any) -> dict:
    return {
        "id": str(cfg.id),
        "enabled": cfg.enabled,
        "mode": cfg.mode,
        "total_budget": cfg.total_budget,
        "stop_loss_pct": cfg.stop_loss_pct,
        "take_profit_pct": cfg.take_profit_pct,
        "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


@router.get("/config")
@limiter.limit("30/minute")
async def get_config(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cfg = await auto_trade_service.get_config(user.id, db)
    return _cfg_to_dict(cfg)


@router.put("/config")
@limiter.limit("20/minute")
async def update_config(
    request: Request,
    body: AutoTradeConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    cfg = await auto_trade_service.update_config(user.id, data, db)
    return _cfg_to_dict(cfg)


@router.get("/logs")
@limiter.limit("30/minute")
async def get_logs(
    request: Request,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    effective_limit = max(1, min(limit, 200))
    logs = await auto_trade_service.get_logs(user.id, db, effective_limit)
    return {"logs": logs, "count": len(logs)}


@router.post("/run")
@limiter.limit("5/minute")
async def run_cycle(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await auto_trade_service.run_cycle(user.id, db)
    return result


@router.post("/stop")
@limiter.limit("10/minute")
async def kill_switch(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await auto_trade_service.kill_switch(user.id, db)
