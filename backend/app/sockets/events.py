"""Socket.IO event handlers."""
import logging
import socketio

logger = logging.getLogger("sockets")

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


async def broadcast_signal(signal_data: dict):
    """Yeni sinyal tüm bağlı client'lara gönder."""
    await sio.emit("new_signal", signal_data)
    logger.info(f"Broadcasted signal: {signal_data.get('symbol')} {signal_data.get('direction')}")


async def broadcast_trade(trade_data: dict):
    """Trade güncellemesi tüm client'lara gönder."""
    event = trade_data.get("event", "trade_update")
    await sio.emit(event, trade_data)
    logger.info(f"Broadcasted trade: {event} {trade_data.get('symbol')}")
