"""
ICT Bot — FastAPI Ana Giriş Noktası.
Tüm modülleri bir araya getirir, motoru başlatır.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api.signals import router as signals_router
from app.api.trades import router as trades_router
from app.api.analytics import router as analytics_router
from app.sockets.events import sio, broadcast_signal, broadcast_trade
from app.engine.signal_gen import register_signal_engine, set_broadcast_callback
from app.engine.trade_sim import register_trade_simulator, set_trade_broadcast
from app.engine.market_data import start_market_data
from app.engine.time_engine import ny_now, is_in_macro, get_active_session

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü — başlatma ve kapatma."""
    # DB tablolarını oluştur
    await init_db()
    logger.info("Database initialized.")

    # Callback'leri bağla
    set_broadcast_callback(broadcast_signal)
    set_trade_broadcast(broadcast_trade)

    # Motorları kaydet
    register_signal_engine()
    register_trade_simulator()

    # Market data toplama görevini arka planda başlat
    market_task = asyncio.create_task(start_market_data())
    logger.info("Market data engine started.")

    yield

    # Cleanup
    market_task.cancel()
    logger.info("Shutting down.")


# FastAPI uygulaması
app = FastAPI(
    title="ICT Signal Bot",
    description="ICT 2024 Mentorship konseptlerine dayalı sinyal üretim ve simülasyon sistemi",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API router'lar
app.include_router(signals_router)
app.include_router(trades_router)
app.include_router(analytics_router)

# Socket.IO mount
sio_app = socketio.ASGIApp(sio, app)


@app.get("/api/status")
async def status():
    now = ny_now()
    return {
        "status": "running",
        "ny_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "session": get_active_session(now),
        "macro_active": is_in_macro(now),
    }


# Uvicorn ile çalıştırma
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:sio_app", host="0.0.0.0", port=8083, reload=False)
