"""
Paper Trade Simülasyon Modülü.
Üretilen sinyalleri izler; fiyat giriş bölgesine dokunursa işlemi açar,
TP veya SL'ye ulaşırsa kapatır.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import select, and_
from app.database import async_session
from app.models.signal import Signal
from app.models.trade import SimulatedTrade
from app.engine.time_engine import ny_now, to_ny_str
from app.engine.market_data import latest_candles, on_candle_close

logger = logging.getLogger("trade_sim")

# Socket.IO broadcast callback
_broadcast_trade = None


def set_trade_broadcast(fn):
    global _broadcast_trade
    _broadcast_trade = fn


async def _check_signal_entry(symbol: str, candle: dict):
    """Aktif sinyallerde fiyat FVG giriş bölgesine dokundu mu?"""
    async with async_session() as session:
        result = await session.execute(
            select(Signal).where(
                and_(
                    Signal.symbol == symbol,
                    Signal.status == "ACTIVE",
                )
            )
        )
        active_signals = result.scalars().all()

        for sig in active_signals:
            price_low = candle["low"]
            price_high = candle["high"]

            # Fiyat FVG bölgesine dokundu mu?
            touched = False
            if sig.direction == "LONG":
                # Fiyat FVG bölgesine düşmeli
                if price_low <= sig.fvg_high and price_high >= sig.fvg_low:
                    touched = True
            else:  # SHORT
                # Fiyat FVG bölgesine yükselmeli
                if price_high >= sig.fvg_low and price_low <= sig.fvg_high:
                    touched = True

            if touched:
                now = ny_now()
                sig.status = "TRIGGERED"

                trade = SimulatedTrade(
                    signal_id=sig.id,
                    symbol=symbol,
                    direction=sig.direction,
                    entry_price=sig.fvg_mid,
                    target_price=sig.target,
                    stop_price=sig.stop_loss,
                    entry_time=datetime.utcnow(),
                    entry_ny_time=to_ny_str(now),
                    market_condition=sig.market_condition,
                    risk_label=sig.risk_label,
                    status="OPEN",
                )
                session.add(trade)
                await session.commit()
                await session.refresh(trade)

                logger.info(f"🟢 TRADE OPENED: {symbol} {sig.direction} @ {sig.fvg_mid:.2f}")

                if _broadcast_trade:
                    try:
                        await _broadcast_trade({
                            "event": "trade_opened",
                            "id": trade.id,
                            "signal_id": sig.id,
                            "symbol": symbol,
                            "direction": sig.direction,
                            "entry_price": sig.fvg_mid,
                            "target_price": sig.target,
                            "stop_price": sig.stop_loss,
                            "entry_ny_time": trade.entry_ny_time,
                            "market_condition": sig.market_condition,
                            "risk_label": sig.risk_label,
                            "status": "OPEN",
                        })
                    except Exception as e:
                        logger.error(f"Trade broadcast error: {e}")


async def _check_trade_exit(symbol: str, candle: dict):
    """Açık işlemlerde TP veya SL'ye ulaşıldı mı?"""
    async with async_session() as session:
        result = await session.execute(
            select(SimulatedTrade).where(
                and_(
                    SimulatedTrade.symbol == symbol,
                    SimulatedTrade.status == "OPEN",
                )
            )
        )
        open_trades = result.scalars().all()

        for trade in open_trades:
            price_high = candle["high"]
            price_low = candle["low"]
            hit_tp = False
            hit_sl = False

            if trade.direction == "LONG":
                if price_high >= trade.target_price:
                    hit_tp = True
                if price_low <= trade.stop_price:
                    hit_sl = True
            else:  # SHORT
                if price_low <= trade.target_price:
                    hit_tp = True
                if price_high >= trade.stop_price:
                    hit_sl = True

            # Eğer ikisi de aynı mumda olduysa, SL'yi öncelikli kabul et (muhafazakar)
            if hit_sl:
                trade.result = "SL"
                trade.exit_price = trade.stop_price
                trade.pnl_r = -1.0
            elif hit_tp:
                trade.result = "TP"
                trade.exit_price = trade.target_price
                risk = abs(trade.entry_price - trade.stop_price)
                reward = abs(trade.target_price - trade.entry_price)
                trade.pnl_r = round(reward / risk, 2) if risk > 0 else 0

            if hit_tp or hit_sl:
                now = ny_now()
                trade.exit_time = datetime.utcnow()
                trade.exit_ny_time = to_ny_str(now)
                trade.status = "CLOSED"
                await session.commit()

                logger.info(f"{'🟢' if trade.result == 'TP' else '🔴'} TRADE CLOSED: "
                            f"{symbol} {trade.direction} → {trade.result} "
                            f"PnL={trade.pnl_r}R")

                if _broadcast_trade:
                    try:
                        await _broadcast_trade({
                            "event": "trade_closed",
                            "id": trade.id,
                            "symbol": symbol,
                            "direction": trade.direction,
                            "result": trade.result,
                            "entry_price": trade.entry_price,
                            "exit_price": trade.exit_price,
                            "pnl_r": trade.pnl_r,
                            "exit_ny_time": trade.exit_ny_time,
                            "status": "CLOSED",
                        })
                    except Exception as e:
                        logger.error(f"Trade close broadcast error: {e}")


async def process_candle_for_trades(symbol: str, candle: dict):
    """Her mum kapandığında giriş ve çıkış kontrolü yap."""
    await _check_signal_entry(symbol, candle)
    await _check_trade_exit(symbol, candle)


def register_trade_simulator():
    """Market data motoruna trade sim callback'ini kaydeder."""
    on_candle_close(process_candle_for_trades)
    logger.info("Trade simulator registered.")
