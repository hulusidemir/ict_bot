import datetime
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SimulatedTrade(Base):
    __tablename__ = "simulated_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[int] = mapped_column(Integer, ForeignKey("signals.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(5))  # LONG / SHORT
    entry_price: Mapped[float] = mapped_column(Float)  # Actual fill price (FVG midpoint)
    target_price: Mapped[float] = mapped_column(Float)
    stop_price: Mapped[float] = mapped_column(Float)
    entry_time: Mapped[datetime.datetime] = mapped_column(DateTime)
    entry_ny_time: Mapped[str] = mapped_column(String(32))
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)
    exit_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    exit_ny_time: Mapped[str] = mapped_column(String(32), nullable=True)
    result: Mapped[str] = mapped_column(String(10), nullable=True)  # TP / SL / None (open)
    pnl_r: Mapped[float] = mapped_column(Float, nullable=True)  # P&L in R units
    market_condition: Mapped[str] = mapped_column(String(20), nullable=True)
    risk_label: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN / CLOSED
