"""
MODÜL 2: Kripto Sanal Boşlukları (Virtual Gaps) ve Likidite
NDOG, NWOG, ORG hesaplama + Equal Highs/Lows tespiti.
"""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from app.database import async_session
from app.models.candle import Candle
from app.config import settings
from app.engine.time_engine import NY_TZ

logger = logging.getLogger("virtual_gaps")


# ─── Yardımcı: Belirli NY saatine en yakın mumu bul ──────────
async def _candle_at_ny_time(symbol: str, date: datetime, hour: int, minute: int = 0) -> dict | None:
    """Belirli bir NY tarih/saat'e en yakın 1m mumu döndürür."""
    target_ny = date.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=NY_TZ)
    target_utc = target_ny.astimezone(ZoneInfo("UTC"))
    target_ts = int(target_utc.timestamp() * 1000)

    async with async_session() as session:
        # ±2 dakika tolerans
        result = await session.execute(
            select(Candle).where(
                and_(
                    Candle.symbol == symbol,
                    Candle.timestamp >= target_ts - 120_000,
                    Candle.timestamp <= target_ts + 120_000,
                )
            ).order_by(Candle.timestamp).limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            return {"open": row.open, "high": row.high, "low": row.low, "close": row.close,
                    "timestamp": row.timestamp, "dt_ny": row.dt_ny}
    return None


# ─── NDOG (New Day Opening Gap) ────────────────────────────
# Günlük 17:00 EST close → 18:00 EST open arasındaki fark.

async def calc_ndog(symbol: str, date: datetime | None = None) -> dict | None:
    """
    NDOG: Dünkü 17:00 EST close vs bugünkü 18:00 EST open.
    Döndürür: {high, low, mid, direction}
    """
    today = date or datetime.now(NY_TZ)
    yesterday = today - timedelta(days=1)

    close_17 = await _candle_at_ny_time(symbol, yesterday, 17, 0)
    open_18 = await _candle_at_ny_time(symbol, yesterday, 18, 0)

    if not close_17 or not open_18:
        return None

    p1 = close_17["close"]
    p2 = open_18["open"]
    high = max(p1, p2)
    low = min(p1, p2)
    mid = (high + low) / 2

    return {
        "type": "NDOG",
        "high": high,
        "low": low,
        "mid": mid,
        "size": high - low,
        "direction": "BULLISH" if p2 > p1 else "BEARISH",
        "date": yesterday.strftime("%Y-%m-%d"),
    }


# ─── NWOG (New Week Opening Gap) ───────────────────────────
# Cuma 17:00 EST close → Pazar 18:00 EST open.

async def calc_nwog(symbol: str, date: datetime | None = None) -> dict | None:
    today = date or datetime.now(NY_TZ)

    # Bu haftanın Cuma'sını bul (geçen haftanınki eğer henüz Cuma olmadıysa)
    days_since_friday = (today.weekday() - 4) % 7
    if days_since_friday == 0 and today.hour < 18:
        days_since_friday = 7
    last_friday = today - timedelta(days=days_since_friday)
    last_sunday = last_friday + timedelta(days=2)

    close_fri = await _candle_at_ny_time(symbol, last_friday, 17, 0)
    open_sun = await _candle_at_ny_time(symbol, last_sunday, 18, 0)

    if not close_fri or not open_sun:
        return None

    p1 = close_fri["close"]
    p2 = open_sun["open"]
    high = max(p1, p2)
    low = min(p1, p2)

    return {
        "type": "NWOG",
        "high": high,
        "low": low,
        "mid": (high + low) / 2,
        "size": high - low,
        "direction": "BULLISH" if p2 > p1 else "BEARISH",
        "friday_date": last_friday.strftime("%Y-%m-%d"),
    }


# ─── ORG (Opening Range Gap) ───────────────────────────────
# Önceki günün 16:14 EST fiyatı vs bugünün 09:30 EST fiyatı.

async def calc_org(symbol: str, date: datetime | None = None) -> dict | None:
    today = date or datetime.now(NY_TZ)
    yesterday = today - timedelta(days=1)

    close_1614 = await _candle_at_ny_time(symbol, yesterday, 16, 14)
    open_0930 = await _candle_at_ny_time(symbol, today, 9, 30)

    if not close_1614 or not open_0930:
        return None

    p1 = close_1614["close"]
    p2 = open_0930["open"]
    high = max(p1, p2)
    low = min(p1, p2)
    size = high - low
    mid = (high + low) / 2

    # Geniş gap kontrolü (40+ point)
    is_wide = size >= settings.opening_range_gap_wide_points

    return {
        "type": "ORG",
        "high": high,
        "low": low,
        "mid": mid,
        "size": size,
        "is_wide": is_wide,
        "fill_probability": 0.70 if is_wide else 0.50,
        "direction": "GAP_UP" if p2 > p1 else "GAP_DOWN",
        "date": today.strftime("%Y-%m-%d"),
    }


# ─── Equal Highs / Equal Lows (Likidite) ───────────────────

def detect_equal_levels(candles: list[dict], tolerance_pct: float | None = None) -> dict:
    """
    Son N mumda göreceli eşit tepeler ve dipler tespit eder.
    Döndürür: {"equal_highs": [...], "equal_lows": [...]}
    """
    tol = tolerance_pct or settings.equal_level_tolerance_pct

    highs = [(c["high"], i) for i, c in enumerate(candles)]
    lows = [(c["low"], i) for i, c in enumerate(candles)]

    equal_highs = _find_equal_levels([h for h, _ in highs], tol)
    equal_lows = _find_equal_levels([l for l, _ in lows], tol)

    eq_h = []
    for level, indices in equal_highs:
        eq_h.append({
            "price": level,
            "touches": len(indices),
            "indices": indices,
            "type": "EQUAL_HIGH",
        })

    eq_l = []
    for level, indices in equal_lows:
        eq_l.append({
            "price": level,
            "touches": len(indices),
            "indices": indices,
            "type": "EQUAL_LOW",
        })

    return {"equal_highs": eq_h, "equal_lows": eq_l}


def _find_equal_levels(prices: list[float], tolerance_pct: float) -> list[tuple[float, list[int]]]:
    """Tolerans dahilinde eşit seviyeleri gruplar."""
    if not prices:
        return []

    used = set()
    groups = []

    for i, p in enumerate(prices):
        if i in used:
            continue
        group_indices = [i]
        for j in range(i + 1, len(prices)):
            if j in used:
                continue
            diff_pct = abs(prices[j] - p) / p * 100 if p != 0 else 0
            if diff_pct <= tolerance_pct:
                group_indices.append(j)
                used.add(j)

        if len(group_indices) >= 2:  # En az 2 temas
            avg_price = sum(prices[k] for k in group_indices) / len(group_indices)
            groups.append((round(avg_price, 2), group_indices))
        used.add(i)

    return groups


# ─── Tüm gap'leri topla ────────────────────────────────────

async def get_all_gaps(symbol: str) -> dict:
    ndog = await calc_ndog(symbol)
    nwog = await calc_nwog(symbol)
    org = await calc_org(symbol)
    return {
        "ndog": ndog,
        "nwog": nwog,
        "org": org,
    }
