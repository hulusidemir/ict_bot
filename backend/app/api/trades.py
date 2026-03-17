"""Trades REST API endpoints."""
from fastapi import APIRouter, Query
from sqlalchemy import select, desc
from app.database import async_session
from app.models.trade import SimulatedTrade

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("")
async def get_trades(
    symbol: str | None = None,
    status: str | None = None,
    result_filter: str | None = Query(default=None, alias="result"),
    limit: int = Query(default=50, le=500),
    offset: int = 0,
):
    async with async_session() as session:
        q = select(SimulatedTrade).order_by(desc(SimulatedTrade.id))

        if symbol:
            q = q.where(SimulatedTrade.symbol == symbol)
        if status:
            q = q.where(SimulatedTrade.status == status)
        if result_filter:
            q = q.where(SimulatedTrade.result == result_filter)

        q = q.offset(offset).limit(limit)
        result = await session.execute(q)
        trades = result.scalars().all()

        return [_trade_dict(t) for t in trades]


@router.get("/open")
async def get_open_trades():
    async with async_session() as session:
        result = await session.execute(
            select(SimulatedTrade)
            .where(SimulatedTrade.status == "OPEN")
            .order_by(desc(SimulatedTrade.id))
        )
        trades = result.scalars().all()
        return [_trade_dict(t) for t in trades]


def _trade_dict(t: SimulatedTrade) -> dict:
    return {
        "id": t.id,
        "signal_id": t.signal_id,
        "symbol": t.symbol,
        "direction": t.direction,
        "entry_price": t.entry_price,
        "target_price": t.target_price,
        "stop_price": t.stop_price,
        "entry_ny_time": t.entry_ny_time,
        "exit_price": t.exit_price,
        "exit_ny_time": t.exit_ny_time,
        "result": t.result,
        "pnl_r": t.pnl_r,
        "market_condition": t.market_condition,
        "risk_label": t.risk_label,
        "status": t.status,
    }
