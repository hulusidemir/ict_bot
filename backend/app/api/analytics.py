"""Analytics REST API endpoints — Performans metrikleri."""
from fastapi import APIRouter
from sqlalchemy import select, func, case
from app.database import async_session
from app.models.trade import SimulatedTrade

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
async def get_analytics():
    async with async_session() as session:
        # Toplam işlem sayıları
        total_q = await session.execute(
            select(func.count(SimulatedTrade.id)).where(SimulatedTrade.status == "CLOSED")
        )
        total = total_q.scalar() or 0

        wins_q = await session.execute(
            select(func.count(SimulatedTrade.id)).where(
                SimulatedTrade.status == "CLOSED",
                SimulatedTrade.result == "TP",
            )
        )
        wins = wins_q.scalar() or 0

        losses_q = await session.execute(
            select(func.count(SimulatedTrade.id)).where(
                SimulatedTrade.status == "CLOSED",
                SimulatedTrade.result == "SL",
            )
        )
        losses = losses_q.scalar() or 0

        # Toplam PnL (R cinsinden)
        total_pnl_q = await session.execute(
            select(func.coalesce(func.sum(SimulatedTrade.pnl_r), 0)).where(
                SimulatedTrade.status == "CLOSED"
            )
        )
        total_pnl = float(total_pnl_q.scalar() or 0)

        # Win/Loss R toplamları
        win_r_q = await session.execute(
            select(func.coalesce(func.sum(SimulatedTrade.pnl_r), 0)).where(
                SimulatedTrade.status == "CLOSED",
                SimulatedTrade.result == "TP",
            )
        )
        total_win_r = float(win_r_q.scalar() or 0)

        total_loss_r = total_pnl - total_win_r

        win_rate = round((wins / total) * 100, 1) if total > 0 else 0

        # LRLR vs HRLR performans
        lrlr_stats = await _condition_stats(session, "LRLR")
        hrlr_stats = await _condition_stats(session, "HRLR")

        # Açık işlem sayısı
        open_q = await session.execute(
            select(func.count(SimulatedTrade.id)).where(SimulatedTrade.status == "OPEN")
        )
        open_count = open_q.scalar() or 0

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl_r": round(total_pnl, 2),
            "total_win_r": round(total_win_r, 2),
            "total_loss_r": round(total_loss_r, 2),
            "open_trades": open_count,
            "by_condition": {
                "LRLR": lrlr_stats,
                "HRLR": hrlr_stats,
            },
        }


@router.get("/weekly")
async def get_weekly_stats():
    """Haftalık performans verileri."""
    async with async_session() as session:
        result = await session.execute(
            select(SimulatedTrade).where(SimulatedTrade.status == "CLOSED").order_by(SimulatedTrade.exit_time)
        )
        trades = result.scalars().all()

        weekly = {}
        for t in trades:
            if t.exit_time:
                week_key = t.exit_time.strftime("%Y-W%W")
                if week_key not in weekly:
                    weekly[week_key] = {"week": week_key, "trades": 0, "wins": 0, "pnl_r": 0}
                weekly[week_key]["trades"] += 1
                if t.result == "TP":
                    weekly[week_key]["wins"] += 1
                weekly[week_key]["pnl_r"] = round(weekly[week_key]["pnl_r"] + (t.pnl_r or 0), 2)

        for w in weekly.values():
            w["win_rate"] = round((w["wins"] / w["trades"]) * 100, 1) if w["trades"] > 0 else 0

        return list(weekly.values())


async def _condition_stats(session, condition: str) -> dict:
    total_q = await session.execute(
        select(func.count(SimulatedTrade.id)).where(
            SimulatedTrade.status == "CLOSED",
            SimulatedTrade.market_condition == condition,
        )
    )
    total = total_q.scalar() or 0

    wins_q = await session.execute(
        select(func.count(SimulatedTrade.id)).where(
            SimulatedTrade.status == "CLOSED",
            SimulatedTrade.market_condition == condition,
            SimulatedTrade.result == "TP",
        )
    )
    wins = wins_q.scalar() or 0

    pnl_q = await session.execute(
        select(func.coalesce(func.sum(SimulatedTrade.pnl_r), 0)).where(
            SimulatedTrade.status == "CLOSED",
            SimulatedTrade.market_condition == condition,
        )
    )
    pnl = float(pnl_q.scalar() or 0)

    return {
        "total": total,
        "wins": wins,
        "win_rate": round((wins / total) * 100, 1) if total > 0 else 0,
        "pnl_r": round(pnl, 2),
    }
