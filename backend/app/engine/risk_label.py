"""
Risk Etiketleme Modülü.
Sinyal üretilirken piyasa koşuluna göre LRLR/HRLR/Haber etiketi vurulur.
"""
import logging
from app.engine.time_engine import is_near_news, ny_now

logger = logging.getLogger("risk_label")


def classify_market_condition(candles: list[dict]) -> str:
    """
    Son mumları analiz ederek piyasa koşulunu belirler.
    - LRLR (Low Resistance Liquidity Run): Fiyat temiz ilerliyor, FVG'ler açık kalıyor.
    - HRLR (High Resistance Liquidity Run): Fiyat sürekli önceki mumu ihlal ediyor.
    """
    if len(candles) < 5:
        return "UNKNOWN"

    recent = candles[-5:]
    violations = 0

    for i in range(1, len(recent)):
        prev = recent[i - 1]
        curr = recent[i]

        # Bir önceki mumun body'sini ihlal ediyor mu?
        prev_body_high = max(prev["open"], prev["close"])
        prev_body_low = min(prev["open"], prev["close"])

        if curr["low"] < prev_body_low and curr["high"] > prev_body_high:
            violations += 1
        elif curr["close"] < prev_body_low and recent[i - 1]["close"] > prev_body_high:
            violations += 1

    # 3+ ihlal = HRLR, aksi halde LRLR
    if violations >= 3:
        return "HRLR"
    return "LRLR"


def check_open_fvgs_filled(candles: list[dict], fvgs: list[dict]) -> int:
    """Açık kalan FVG sayısını kontrol eder. LRLR'de FVG'ler açık kalır."""
    filled = 0
    if not fvgs:
        return 0
    for fvg in fvgs:
        for c in candles:
            if fvg["direction"] == "BULLISH":
                if c["low"] <= fvg["low"]:
                    filled += 1
                    break
            else:
                if c["high"] >= fvg["high"]:
                    filled += 1
                    break
    return len(fvgs) - filled  # Açık kalan FVG sayısı


def get_risk_label(candles: list[dict], dt=None) -> dict:
    """
    Tam risk etiketi döndürür.
    """
    condition = classify_market_condition(candles)
    near_news = is_near_news(dt)

    labels = []
    if near_news:
        labels.append("Yüksek Risk: Haber")
    labels.append(condition)

    return {
        "market_condition": condition,
        "risk_label": " | ".join(labels) if labels else condition,
        "near_news": near_news,
    }
