from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/ict_bot.db"

    # Bybit
    bybit_ws_url: str = "wss://stream.bybit.com/v5/public/linear"
    
    symbols: List[str] = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BCHUSDT", "AVAXUSDT", "ADAUSDT", 
        "XRPUSDT", "SUIUSDT", "LINKUSDT", "ETCUSDT", "LTCUSDT", "AAVEUSDT", 
        "SEIUSDT", "TRXUSDT", "ARBUSDT", "CHZUSDT", "OPUSDT", "TIAUSDT", 
        "APTUSDT", "DOTUSDT", "ASTRUSDT", "XTZUSDT", "TONUSDT", "STXUSDT", 
        "EGLDUSDT", "BNBUSDT", "CRVUSDT", "ALCHUSDT", "LDOUSDT", "UNIUSDT", 
        "PENDLEUSDT", "SUSHIUSDT", "COMPUSDT", "AUCTIONUSDT", "YFIUSDT", 
        "GRTUSDT", "ICPUSDT", "ARKMUSDT", "INJUSDT", "RENDERUSDT", "TAOUSDT", 
        "MAGICUSDT", "B3USDT", "NOTUSDT", "BOMEUSDT", "1000BONKUSDT", 
        "DOGEUSDT", "WIFUSDT", "MOODENGUSDT", "POPCATUSDT", "1000FLOKIUSDT", 
        "GOATUSDT", "PNUTUSDT", "MELANIAUSDT", "TRUMPUSDT"
    ]    
    
    kline_interval: str = "1"  # 1 minute

    # Time
    ny_timezone: str = "America/New_York"

    # Signal defaults
    equal_level_tolerance_pct: float = 0.08   # %0.08 tolerance for equal highs/lows
    fvg_min_size_pct: float = 0.02            # minimum FVG size as % of price
    lookback_candles: int = 50                # candles to check for equal levels
    displacement_min_pct: float = 0.10        # min displacement size as % of price
    opening_range_gap_wide_points: float = 40 # "wide" ORG threshold

    # News times (EST hours, approximate - can be extended)
    high_impact_news_hours: List[int] = [8, 10, 14]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

settings = Settings()