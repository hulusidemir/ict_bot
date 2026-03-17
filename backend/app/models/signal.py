import datetime
from sqlalchemy import String, Float, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    ny_time: Mapped[str] = mapped_column(String(32))  # NY local time string
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(5))  # LONG or SHORT
    fvg_low: Mapped[float] = mapped_column(Float)  # FVG entry zone bottom
    fvg_high: Mapped[float] = mapped_column(Float)  # FVG entry zone top
    fvg_mid: Mapped[float] = mapped_column(Float)  # FVG midpoint (entry)
    target: Mapped[float] = mapped_column(Float)  # Draw on Liquidity target
    stop_loss: Mapped[float] = mapped_column(Float)  # Invalidation level
    risk_reward: Mapped[float] = mapped_column(Float, nullable=True)  # R:R ratio
    market_condition: Mapped[str] = mapped_column(String(20))  # LRLR / HRLR
    risk_label: Mapped[str] = mapped_column(String(50), nullable=True)  # "Yüksek Risk: Haber" etc.
    session_tag: Mapped[str] = mapped_column(String(30), nullable=True)  # Macro/OR/London etc.
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE / TRIGGERED / EXPIRED / INVALIDATED
    notes: Mapped[str] = mapped_column(Text, nullable=True)
