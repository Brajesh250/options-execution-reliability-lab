from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.db import Base


class StrategyBuild(Base):
    __tablename__ = "strategy_builds"
    build_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str]
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    strategy: Mapped[str]
    underlying: Mapped[str]
    reviewed: Mapped[bool]
    submitted: Mapped[bool]


class BasketOrder(Base):
    __tablename__ = "basket_orders"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    build_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_builds.build_id"))
    session_id: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    strategy: Mapped[str]
    underlying: Mapped[str]
    liquidity: Mapped[str]
    order_type: Mapped[str]
    scenario: Mapped[str]
    final_status: Mapped[str]
    margin_required: Mapped[float]
    margin_utilization: Mapped[float]
    latency_ms: Mapped[float]
    avg_slippage: Mapped[float]
    partial_fill_exposure: Mapped[float]
    recommendation: Mapped[str]


class OrderLeg(Base):
    __tablename__ = "order_legs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("basket_orders.order_id"), index=True)
    leg_id: Mapped[str]
    status: Mapped[str]
    requested_price: Mapped[float]
    fill_price: Mapped[float | None]
    filled_quantity: Mapped[int]
    slippage_rupees: Mapped[float | None]
    slippage_bps: Mapped[float | None]
    latency_ms: Mapped[float]
    rejection_reason: Mapped[str | None]


class ExecutionEventRow(Base):
    __tablename__ = "execution_events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    session_id: Mapped[str]
    order_id: Mapped[str] = mapped_column(ForeignKey("basket_orders.order_id"), index=True)
    leg_id: Mapped[str | None]
    event_name: Mapped[str]
    status: Mapped[str]
    latency_ms: Mapped[float | None]
    metadata_json: Mapped[dict] = mapped_column(JSON)


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"
    snapshot_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("basket_orders.order_id"))
    timestamp: Mapped[datetime]
    available_margin: Mapped[float]
    pledged_collateral: Mapped[float]
    margin_consumed: Mapped[float]
