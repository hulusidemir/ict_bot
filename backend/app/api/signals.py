"""Signals REST API endpoints."""
from fastapi import APIRouter, Query
from sqlalchemy import select, desc
from app.database import async_session
from app.models.signal import Signal

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
async def get_signals(
    symbol: str | None = None,
    status: str | None = None,
    direction: str | None = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
):
    async with async_session() as session:
        q = select(Signal).order_by(desc(Signal.id))

        if symbol:
            q = q.where(Signal.symbol == symbol)
        if status:
            q = q.where(Signal.status == status)
        if direction:
            q = q.where(Signal.direction == direction)

        q = q.offset(offset).limit(limit)
        result = await session.execute(q)
        signals = result.scalars().all()

        return [
            {
                "id": s.id,
                "created_at": str(s.created_at),
                "ny_time": s.ny_time,
                "symbol": s.symbol,
                "direction": s.direction,
                "fvg_low": s.fvg_low,
                "fvg_high": s.fvg_high,
                "fvg_mid": s.fvg_mid,
                "target": s.target,
                "stop_loss": s.stop_loss,
                "risk_reward": s.risk_reward,
                "market_condition": s.market_condition,
                "risk_label": s.risk_label,
                "session_tag": s.session_tag,
                "status": s.status,
            }
            for s in signals
        ]


@router.get("/active")
async def get_active_signals():
    async with async_session() as session:
        result = await session.execute(
            select(Signal).where(Signal.status == "ACTIVE").order_by(desc(Signal.id))
        )
        signals = result.scalars().all()
        return [
            {
                "id": s.id,
                "ny_time": s.ny_time,
                "symbol": s.symbol,
                "direction": s.direction,
                "fvg_low": s.fvg_low,
                "fvg_high": s.fvg_high,
                "fvg_mid": s.fvg_mid,
                "target": s.target,
                "stop_loss": s.stop_loss,
                "risk_reward": s.risk_reward,
                "market_condition": s.market_condition,
                "risk_label": s.risk_label,
                "session_tag": s.session_tag,
                "status": s.status,
            }
            for s in signals
        ]
