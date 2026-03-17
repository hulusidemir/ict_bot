"""
MODÜL 3: KESİNTİSİZ SİNYAL ÜRETİM MANTIĞI
FVG (Fair Value Gap) tespiti, Displacement analizi, Stop Hunt sonrası sinyal üretimi.
First Presented FVG modeli uygulanır.
"""
import asyncio
import logging
from datetime import datetime

from app.config import settings
from app.database import async_session
from app.models.signal import Signal
from app.engine.time_engine import (
    ny_now, to_ny, to_ny_str, is_signal_eligible,
    is_in_macro, is_in_opening_range, get_active_session,
    current_macro_window, unix_ms_to_ny,
)
from app.engine.market_data import get_recent_candles, on_candle_close
from app.engine.virtual_gaps import detect_equal_levels, get_all_gaps
from app.engine.risk_label import get_risk_label

logger = logging.getLogger("signal_gen")

# Son üretilen sinyallerin takibi (duplicate önleme)
_recent_signals: dict[str, datetime] = {}  # "BTCUSDT_LONG_ts" -> datetime
SIGNAL_COOLDOWN_SECONDS = 180  # Aynı yönde 3dk cooldown

# Socket.IO broadcast callback (main.py tarafından set edilir)
_broadcast_signal = None


def set_broadcast_callback(fn):
    global _broadcast_signal
    _broadcast_signal = fn


# ─── FVG Tespiti ────────────────────────────────────────────

def detect_fvgs(candles: list[dict]) -> list[dict]:
    """
    3 mumlu Fair Value Gap tespiti.
    Bullish FVG: candle[0].high < candle[2].low (boşluk yukarı)
    Bearish FVG: candle[0].low > candle[2].high (boşluk aşağı)
    """
    fvgs = []
    if len(candles) < 3:
        return fvgs

    for i in range(len(candles) - 2):
        c1 = candles[i]      # İlk mum
        c2 = candles[i + 1]  # Orta mum (displacement)
        c3 = candles[i + 2]  # Üçüncü mum

        # Bullish FVG: 1. mum high < 3. mum low
        if c1["high"] < c3["low"]:
            gap_size = c3["low"] - c1["high"]
            gap_pct = gap_size / c2["close"] * 100 if c2["close"] else 0
            if gap_pct >= settings.fvg_min_size_pct:
                fvgs.append({
                    "direction": "BULLISH",
                    "high": c3["low"],       # FVG üst sınırı
                    "low": c1["high"],        # FVG alt sınırı
                    "mid": (c3["low"] + c1["high"]) / 2,
                    "size": gap_size,
                    "size_pct": round(gap_pct, 4),
                    "candle_index": i + 1,    # Orta mum index'i
                    "timestamp": c2.get("timestamp", 0),
                })

        # Bearish FVG: 1. mum low > 3. mum high
        if c1["low"] > c3["high"]:
            gap_size = c1["low"] - c3["high"]
            gap_pct = gap_size / c2["close"] * 100 if c2["close"] else 0
            if gap_pct >= settings.fvg_min_size_pct:
                fvgs.append({
                    "direction": "BEARISH",
                    "high": c1["low"],        # FVG üst sınırı
                    "low": c3["high"],         # FVG alt sınırı
                    "mid": (c1["low"] + c3["high"]) / 2,
                    "size": gap_size,
                    "size_pct": round(gap_pct, 4),
                    "candle_index": i + 1,
                    "timestamp": c2.get("timestamp", 0),
                })

    return fvgs


# ─── Displacement Tespiti ───────────────────────────────────

def detect_displacement(candles: list[dict], direction: str) -> bool:
    """
    Son mumlarda sert kırılım (displacement) var mı?
    Tek bir büyük body mumun varlığını kontrol eder.
    """
    if len(candles) < 2:
        return False

    for c in candles[-3:]:
        body = abs(c["close"] - c["open"])
        body_pct = body / c["open"] * 100 if c["open"] else 0

        if body_pct >= settings.displacement_min_pct:
            if direction == "BULLISH" and c["close"] > c["open"]:
                return True
            if direction == "BEARISH" and c["close"] < c["open"]:
                return True
    return False


# ─── Stop Hunt Tespiti ──────────────────────────────────────

def detect_stop_hunt(candles: list[dict], liquidity: dict) -> dict | None:
    """
    Equal Highs veya Equal Lows'un sweep edilip edilmediğini kontrol eder.
    Son 3 mumun herhangi birinde likidit seviye aşılıp fiyat geri dönmüşse → stop hunt.
    """
    if len(candles) < 4:
        return None

    recent = candles[-3:]  # Son 3 mumu kontrol et
    last_close = candles[-1]["close"]

    # Equal Lows sweep → Bullish setup için
    for eq_low in liquidity.get("equal_lows", []):
        level = eq_low["price"]
        swept = any(c["low"] < level for c in recent)
        if swept and last_close > level:
            lowest_wick = min(c["low"] for c in recent)
            return {
                "type": "SWEEP_LOWS",
                "level": level,
                "direction": "BULLISH",
                "wick_low": lowest_wick,
            }

    # Equal Highs sweep → Bearish setup için
    for eq_high in liquidity.get("equal_highs", []):
        level = eq_high["price"]
        swept = any(c["high"] > level for c in recent)
        if swept and last_close < level:
            highest_wick = max(c["high"] for c in recent)
            return {
                "type": "SWEEP_HIGHS",
                "level": level,
                "direction": "BEARISH",
                "wick_high": highest_wick,
            }

    return None


# ─── Ana Sinyal Üretim Fonksiyonu ──────────────────────────

async def analyze_and_generate(symbol: str, candle: dict):
    """
    Her kapanan 1m mumda çağrılır.
    ICT kurallarına göre sinyal arar ve bulursa DB'ye kaydeder.
    """
    candles = get_recent_candles(symbol, count=settings.lookback_candles)
    if len(candles) < 10:
        return  # Yeterli veri yok

    now = ny_now()

    # Sinyal uygunluk kontrolü
    if not is_signal_eligible(now):
        return

    # Likidite tespiti
    liquidity = detect_equal_levels(candles)

    # Stop hunt kontrolü
    hunt = detect_stop_hunt(candles, liquidity)
    if not hunt:
        return

    direction = hunt["direction"]

    # Displacement kontrolü
    if not detect_displacement(candles, direction):
        return

    # FVG tespiti - "First Presented FVG" mantığı
    fvgs = detect_fvgs(candles)
    target_fvgs = [f for f in fvgs if f["direction"] == direction]
    if not target_fvgs:
        return

    # En son (first presented) FVG'yi al
    fvg = target_fvgs[-1]

    # Cooldown kontrolü
    sig_key = f"{symbol}_{direction}"
    if sig_key in _recent_signals:
        elapsed = (now - _recent_signals[sig_key]).total_seconds()
        if elapsed < SIGNAL_COOLDOWN_SECONDS:
            return

    # Risk/etiket
    risk_info = get_risk_label(candles, now)

    # Hedef: Karşı taraf likiditesi
    if direction == "BULLISH":
        # Hedef: En yakın equal high
        target_levels = [eh["price"] for eh in liquidity.get("equal_highs", [])]
        target = max(target_levels) if target_levels else fvg["high"] * 1.01
        stop_loss = fvg["low"] * 0.998  # FVG altı
    else:
        # Hedef: En yakın equal low
        target_levels = [el["price"] for el in liquidity.get("equal_lows", [])]
        target = min(target_levels) if target_levels else fvg["low"] * 0.99
        stop_loss = fvg["high"] * 1.002  # FVG üstü

    # Risk/Reward hesapla
    entry = fvg["mid"]
    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    rr = round(reward / risk, 2) if risk > 0 else 0

    # Session tag
    session_tag = get_active_session(now)
    if is_in_macro(now):
        macro_info = current_macro_window(now)
        session_tag = macro_info["label"] if macro_info else session_tag
    elif is_in_opening_range(now):
        session_tag = "Opening Range"

    # Sinyal DB'ye kaydet
    signal_data = Signal(
        ny_time=to_ny_str(now),
        symbol=symbol,
        direction="LONG" if direction == "BULLISH" else "SHORT",
        fvg_low=round(fvg["low"], 2),
        fvg_high=round(fvg["high"], 2),
        fvg_mid=round(entry, 2),
        target=round(target, 2),
        stop_loss=round(stop_loss, 2),
        risk_reward=rr,
        market_condition=risk_info["market_condition"],
        risk_label=risk_info["risk_label"],
        session_tag=session_tag,
        status="ACTIVE",
    )

    async with async_session() as session:
        session.add(signal_data)
        await session.commit()
        await session.refresh(signal_data)

    _recent_signals[sig_key] = now
    logger.info(f"📊 SIGNAL: {symbol} {'LONG' if direction == 'BULLISH' else 'SHORT'} "
                f"Entry={entry:.2f} Target={target:.2f} SL={stop_loss:.2f} RR={rr}")

    # Socket.IO broadcast
    if _broadcast_signal:
        sig_dict = {
            "id": signal_data.id,
            "ny_time": signal_data.ny_time,
            "symbol": symbol,
            "direction": signal_data.direction,
            "fvg_low": signal_data.fvg_low,
            "fvg_high": signal_data.fvg_high,
            "fvg_mid": signal_data.fvg_mid,
            "target": signal_data.target,
            "stop_loss": signal_data.stop_loss,
            "risk_reward": rr,
            "market_condition": signal_data.market_condition,
            "risk_label": signal_data.risk_label,
            "session_tag": session_tag,
            "status": "ACTIVE",
        }
        try:
            await _broadcast_signal(sig_dict)
        except Exception as e:
            logger.error(f"Broadcast error: {e}")


def register_signal_engine():
    """Market data motoruna sinyal üretim callback'ini kaydeder."""
    on_candle_close(analyze_and_generate)
    logger.info("Signal generation engine registered.")
