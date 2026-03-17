import datetime
from sqlalchemy import String, Float, DateTime, Integer, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", name="uq_symbol_timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    timestamp: Mapped[int] = mapped_column(BigInteger, index=True)  # Unix ms
    dt_utc: Mapped[datetime.datetime] = mapped_column(DateTime)
    dt_ny: Mapped[str] = mapped_column(String(32))  # NY local time string
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
