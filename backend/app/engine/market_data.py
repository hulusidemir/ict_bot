"""
Bybit Perpetual Futures WebSocket veri toplama motoru.
1 dakikalık (1m) kline verilerini gerçek zamanlı toplar ve veritabanına yazar.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable

import websockets

from app.config import settings
from app.database import async_session
from app.models.candle import Candle
from app.engine.time_engine import unix_ms_to_ny_str, NY_TZ, UTC_TZ
from sqlalchemy import select

logger = logging.getLogger("market_data")

# In-memory son mum cache: {symbol: Candle dict}
latest_candles: dict[str, dict] = {}
# In-memory son N mum: {symbol: [dict, ...]}
candle_buffers: dict[str, list[dict]] = {}
BUFFER_SIZE = 500  # bellekte tutulan mum sayısı

# Callbacks: yeni mum kapandığında çağrılacak fonksiyonlar
_on_candle_close_callbacks: list[Callable] = []


def on_candle_close(fn: Callable):
    _on_candle_close_callbacks.append(fn)


async def _notify_candle_close(symbol: str, candle: dict):
    for cb in _on_candle_close_callbacks:
        try:
            result = cb(symbol, candle)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Candle close callback error: {e}")


def _parse_kline(data: dict) -> dict:
    """Bybit kline WS mesajını dict'e çevir."""
    k = data
    return {
        "symbol": k.get("symbol", ""),
        "timestamp": int(k["start"]),
        "open": float(k["open"]),
        "high": float(k["high"]),
        "low": float(k["low"]),
        "close": float(k["close"]),
        "volume": float(k["volume"]),
        "confirm": k.get("confirm", False),  # True = mum kapandı
    }


async def _save_candle(candle: dict):
    """Kapanan mumu veritabanına yaz."""
    async with async_session() as session:
        exists = await session.execute(
            select(Candle).where(
                Candle.symbol == candle["symbol"],
                Candle.timestamp == candle["timestamp"],
            )
        )
        if exists.scalar_one_or_none():
            return

        dt_utc = datetime.fromtimestamp(candle["timestamp"] / 1000, tz=timezone.utc)
        c = Candle(
            symbol=candle["symbol"],
            timestamp=candle["timestamp"],
            dt_utc=dt_utc.replace(tzinfo=None),
            dt_ny=unix_ms_to_ny_str(candle["timestamp"]),
            open=candle["open"],
            high=candle["high"],
            low=candle["low"],
            close=candle["close"],
            volume=candle["volume"],
        )
        session.add(c)
        await session.commit()


def _update_buffer(symbol: str, candle: dict):
    """Bellekteki mum buffer'ını güncelle."""
    if symbol not in candle_buffers:
        candle_buffers[symbol] = []

    buf = candle_buffers[symbol]
    # Eğer aynı timestamp varsa güncelle, yoksa ekle
    if buf and buf[-1]["timestamp"] == candle["timestamp"]:
        buf[-1] = candle
    else:
        buf.append(candle)
        if len(buf) > BUFFER_SIZE:
            buf.pop(0)


def get_recent_candles(symbol: str, count: int = 20) -> list[dict]:
    """Bellekten son N mumu döndür."""
    buf = candle_buffers.get(symbol, [])
    return buf[-count:] if len(buf) >= count else buf[:]


async def _ws_subscribe(symbols: list[str]):
    """Bybit WebSocket'e bağlan ve kline stream'i dinle."""
    url = settings.bybit_ws_url
    topics = [f"kline.{settings.kline_interval}.{s}" for s in symbols]

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                sub_msg = {
                    "op": "subscribe",
                    "args": topics,
                }
                await ws.send(json.dumps(sub_msg))
                logger.info(f"Bybit WS subscribed: {topics}")

                async for raw in ws:
                    try:
                        msg = json.loads(raw)

                        # Ping-pong
                        if msg.get("op") == "pong" or msg.get("ret_msg") == "pong":
                            continue
                        if "success" in msg:
                            continue

                        topic = msg.get("topic", "")
                        if not topic.startswith("kline."):
                            continue

                        for item in msg.get("data", []):
                            candle = _parse_kline(item)
                            symbol = candle["symbol"] or topic.split(".")[-1]
                            candle["symbol"] = symbol

                            latest_candles[symbol] = candle
                            _update_buffer(symbol, candle)

                            # Mum kapandıysa DB'ye yaz ve callback'leri çağır
                            if candle["confirm"]:
                                await _save_candle(candle)
                                await _notify_candle_close(symbol, candle)

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"WS parse error: {e}")

        except (websockets.exceptions.ConnectionClosed, ConnectionError, OSError) as e:
            logger.warning(f"Bybit WS disconnected: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Bybit WS unexpected error: {e}. Reconnecting in 10s...")
            await asyncio.sleep(10)


async def start_market_data():
    """Market data toplama motorunu başlat."""
    symbols = settings.symbols
    logger.info(f"Starting market data engine for {symbols}")
    await _ws_subscribe(symbols)
