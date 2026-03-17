"""
MODÜL 1: ZAMAN MOTORU — NY Time Protocol
Tüm zaman hesaplamaları New York (EST/EDT) bazlıdır.
Makrolar, Opening Range ve session bilgilerini sağlar.
"""
import datetime
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(UTC_TZ)


def ny_now() -> datetime.datetime:
    return datetime.datetime.now(NY_TZ)


def to_ny(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(NY_TZ)


def to_ny_str(dt: datetime.datetime) -> str:
    return to_ny(dt).strftime("%Y-%m-%d %H:%M:%S %Z")


def unix_ms_to_ny(ts_ms: int) -> datetime.datetime:
    dt = datetime.datetime.fromtimestamp(ts_ms / 1000, tz=UTC_TZ)
    return dt.astimezone(NY_TZ)


def unix_ms_to_ny_str(ts_ms: int) -> str:
    return unix_ms_to_ny(ts_ms).strftime("%Y-%m-%d %H:%M:%S %Z")


# ─── Macro Windows ─────────────────────────────────────────
# Her saatin :50'sinde başlar, bir sonraki saatin :10'unda biter.
# Örn: 09:50 - 10:10, 10:50 - 11:10 ...

def is_in_macro(dt: datetime.datetime | None = None) -> bool:
    """Verilen NY zamanı bir Makro penceresinde mi?"""
    t = to_ny(dt) if dt else ny_now()
    minute = t.minute
    return minute >= 50 or minute <= 10


def current_macro_window(dt: datetime.datetime | None = None) -> dict | None:
    """Eğer Makro aktifse, başlangıç/bitiş zamanlarını döndürür."""
    t = to_ny(dt) if dt else ny_now()
    minute = t.minute

    if minute >= 50:
        start = t.replace(minute=50, second=0, microsecond=0)
        end = (t + datetime.timedelta(hours=1)).replace(minute=10, second=0, microsecond=0)
        return {"start": start, "end": end, "label": f"Macro {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"}
    elif minute <= 10:
        start = (t - datetime.timedelta(hours=1)).replace(minute=50, second=0, microsecond=0)
        end = t.replace(minute=10, second=0, microsecond=0)
        return {"start": start, "end": end, "label": f"Macro {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"}
    return None


# ─── Opening Range ──────────────────────────────────────────
# 09:30 - 10:00 EST

def is_in_opening_range(dt: datetime.datetime | None = None) -> bool:
    t = to_ny(dt) if dt else ny_now()
    return t.hour == 9 and 30 <= t.minute < 60


def opening_range_times(dt: datetime.datetime | None = None) -> dict:
    """Bugünün Opening Range zaman aralığını döndürür."""
    t = to_ny(dt) if dt else ny_now()
    start = t.replace(hour=9, minute=30, second=0, microsecond=0)
    end = t.replace(hour=10, minute=0, second=0, microsecond=0)
    return {"start": start, "end": end}


# ─── Kill Zones (Referans) ──────────────────────────────────
# London: 02:00 - 05:00, NY AM: 09:30 - 12:00, NY PM: 13:30 - 16:00

KILL_ZONES = {
    "London": (2, 0, 5, 0),
    "NY_AM": (9, 30, 12, 0),
    "NY_PM": (13, 30, 16, 0),
    "Asian": (20, 0, 0, 0),
}


def get_active_session(dt: datetime.datetime | None = None) -> str:
    t = to_ny(dt) if dt else ny_now()
    h, m = t.hour, t.minute
    val = h * 60 + m

    if 2 * 60 <= val < 5 * 60:
        return "London"
    if 9 * 60 + 30 <= val < 12 * 60:
        return "NY_AM"
    if 13 * 60 + 30 <= val < 16 * 60:
        return "NY_PM"
    if val >= 20 * 60 or val < 0 * 60:
        return "Asian"
    return "Off-Hours"


# ─── Signal eligibility ────────────────────────────────────
# 09:31+ veya Makro pencereleri

def is_signal_eligible(dt: datetime.datetime | None = None) -> bool:
    t = to_ny(dt) if dt else ny_now()
    h, m = t.hour, t.minute
    after_open = (h == 9 and m >= 31) or h > 9
    return after_open or is_in_macro(t)


# ─── News proximity check ──────────────────────────────────

def is_near_news(dt: datetime.datetime | None = None, news_hours: list[int] | None = None, minutes_before: int = 15) -> bool:
    """Yüksek etkili haber saatine yakın mı? (varsayılan 15 dakika)"""
    from app.config import settings
    t = to_ny(dt) if dt else ny_now()
    hours = news_hours or settings.high_impact_news_hours
    for nh in hours:
        news_time = t.replace(hour=nh, minute=0, second=0, microsecond=0)
        diff = (news_time - t).total_seconds()
        if 0 <= diff <= minutes_before * 60:
            return True
    return False
