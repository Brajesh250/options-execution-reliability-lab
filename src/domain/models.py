from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OptionType(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class Scenario(StrEnum):
    NORMAL = "Normal execution"
    MARGIN = "Insufficient margin"
    STALE = "Stale quote"
    LIQUIDITY = "Low liquidity"
    REJECT = "One leg rejected"
    PARTIAL = "Partial fill"
    MOVEMENT = "Rapid market movement"
    TIMEOUT = "Exchange timeout"
    RANDOM = "Random realistic simulation"


class LegRequest(BaseModel):
    leg_id: str
    option_type: OptionType
    side: Side
    strike: float = Field(gt=0)
    quantity: int = Field(gt=0)
    requested_price: float = Field(ge=0)


class SimulationRequest(BaseModel):
    session_id: str = "demo"
    strategy: str
    underlying: str = "NIFTY"
    spot_price: float = Field(gt=0)
    expiry: date
    order_type: OrderType = OrderType.LIMIT
    available_margin: float = Field(ge=0)
    pledged_collateral: float = Field(ge=0, default=0)
    volatility: float = Field(ge=0.05, le=1.5, default=0.2)
    liquidity: str = "High"
    scenario: Scenario = Scenario.NORMAL
    seed: int = 42
    legs: list[LegRequest] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def validate_underlying(self):
        if self.underlying not in {"NIFTY", "BANKNIFTY"}:
            raise ValueError("underlying must be NIFTY or BANKNIFTY")
        return self


class ExecutionEvent(BaseModel):
    event_id: str
    timestamp: datetime
    session_id: str
    order_id: str
    leg_id: str | None = None
    event_name: str
    status: str
    latency_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LegResult(BaseModel):
    leg_id: str
    status: str
    requested_price: float
    fill_price: float | None = None
    filled_quantity: int = 0
    slippage_rupees: float | None = None
    slippage_bps: float | None = None
    latency_ms: float
    rejection_reason: str | None = None
    events: list[ExecutionEvent]


class SimulationResult(BaseModel):
    order_id: str
    created_at: datetime
    final_status: str
    strategy: str
    underlying: str
    scenario: str
    liquidity: str
    order_type: str
    margin_required: float
    margin_consumed: float
    total_latency_ms: float
    partial_fill_exposure: float
    recommendation: str
    legs: list[LegResult]


LOT_SIZES = {"NIFTY": 25, "BANKNIFTY": 15}
