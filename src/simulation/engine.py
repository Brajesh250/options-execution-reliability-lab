from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid5

import numpy as np

from src.domain.models import (
    ExecutionEvent,
    LegResult,
    OrderType,
    Scenario,
    Side,
    SimulationRequest,
    SimulationResult,
)
from src.domain.risk import estimate_margin

NAMESPACE = UUID("6f42e5b1-a412-4d20-8e36-6d72ef606840")


def _event(req, order_id, leg_id, name, status, ts, latency=None, **meta):
    key = f"{order_id}:{leg_id}:{name}:{ts.isoformat()}"
    return ExecutionEvent(
        event_id=str(uuid5(NAMESPACE, key)),
        timestamp=ts,
        session_id=req.session_id,
        order_id=order_id,
        leg_id=leg_id,
        event_name=name,
        status=status,
        latency_ms=latency,
        metadata=meta,
    )


def _recommend(status: str, reason: str | None) -> str:
    if reason == "INSUFFICIENT_MARGIN":
        return "Reduce quantity, add funds, or show margin impact before submission."
    if reason == "STALE_QUOTE":
        return "Refresh quotes and require explicit reconfirmation before resubmitting."
    if reason == "EXCHANGE_TIMEOUT":
        return "Show a pending state and reconcile with the exchange before allowing retry."
    if status == "PARTIALLY_FILLED":
        return "Surface live delta exposure and offer hedge or cancel actions."
    if status == "COMPLETED":
        return "Execution completed; retain the latency and price-quality receipt."
    return "Explain the failed leg inline and preserve the basket for a safe retry."


def simulate(req: SimulationRequest) -> SimulationResult:
    rng = np.random.default_rng(req.seed)
    order_id = str(
        uuid5(
            NAMESPACE, f"{req.session_id}:{req.seed}:{req.strategy}:{req.spot_price}:{req.scenario}"
        )
    )
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(seconds=req.seed % 10000)
    required = estimate_margin(req.legs, req.spot_price)
    funds = req.available_margin + req.pledged_collateral * 0.8
    forced_margin = req.scenario == Scenario.MARGIN or (required > funds)
    leg_results = []
    exposure = 0.0
    for index, leg in enumerate(req.legs):
        liquidity_factor = {"High": 1.0, "Medium": 1.6, "Low": 3.0}[req.liquidity]
        if req.scenario == Scenario.LIQUIDITY:
            liquidity_factor = max(liquidity_factor, 3.5)
        market_factor = 0.7 if req.order_type == OrderType.MARKET else 1.15
        latency = round(max(35, rng.lognormal(5.45, 0.35) * liquidity_factor * market_factor), 1)
        events = []
        ts = base + timedelta(milliseconds=index * 20)
        for name in ["Created", "Validated", "Sent", "Acknowledged"]:
            ts += timedelta(milliseconds=latency / 6)
            events.append(_event(req, order_id, leg.leg_id, name, name.upper(), ts, latency / 6))
        reason = None
        status = "FILLED"
        fraction = 1.0
        if forced_margin:
            reason, status = "INSUFFICIENT_MARGIN", "REJECTED"
        elif req.scenario == Scenario.STALE:
            reason, status = "STALE_QUOTE", "REJECTED"
        elif req.scenario == Scenario.TIMEOUT:
            reason, status = "EXCHANGE_TIMEOUT", "CANCELLED"
        elif req.scenario == Scenario.REJECT and index == len(req.legs) - 1:
            reason, status = "LEG_RISK_CHECK_FAILED", "REJECTED"
        elif req.scenario == Scenario.PARTIAL and index == 0:
            status, fraction = "PARTIALLY_FILLED", 0.5
        elif req.scenario == Scenario.RANDOM:
            x = rng.random()
            if x < 0.06:
                reason, status = "STALE_QUOTE", "REJECTED"
            elif x < 0.11:
                status, fraction = "PARTIALLY_FILLED", 0.5
            elif x < 0.14:
                reason, status = "EXCHANGE_TIMEOUT", "CANCELLED"
        move = abs(rng.normal(0.0008, 0.0005)) * liquidity_factor
        if req.order_type == OrderType.LIMIT:
            move *= 0.35
        if req.scenario == Scenario.MOVEMENT:
            move *= 5
        signed = move * leg.requested_price
        fill = (
            None
            if status in {"REJECTED", "CANCELLED"}
            else round(leg.requested_price + (signed if leg.side == Side.BUY else -signed), 2)
        )
        slip = (
            None
            if fill is None
            else round(
                (fill - leg.requested_price)
                if leg.side == Side.BUY
                else (leg.requested_price - fill),
                2,
            )
        )
        filled_qty = int(leg.quantity * fraction) if fill is not None else 0
        if fraction < 1:
            exposure += abs((leg.strike - req.spot_price) * (leg.quantity - filled_qty))
        ts += timedelta(milliseconds=latency / 3)
        events.append(
            _event(
                req,
                order_id,
                leg.leg_id,
                "Partially Filled" if status == "PARTIALLY_FILLED" else status.title(),
                status,
                ts,
                latency / 3,
                reason=reason,
            )
        )
        leg_results.append(
            LegResult(
                leg_id=leg.leg_id,
                status=status,
                requested_price=leg.requested_price,
                fill_price=fill,
                filled_quantity=filled_qty,
                slippage_rupees=slip,
                slippage_bps=None
                if slip is None or leg.requested_price == 0
                else round(slip / leg.requested_price * 10000, 2),
                latency_ms=latency,
                rejection_reason=reason,
                events=events,
            )
        )
    statuses = {x.status for x in leg_results}
    final = (
        "COMPLETED"
        if statuses == {"FILLED"}
        else ("PARTIALLY_FILLED" if any(x.filled_quantity for x in leg_results) else "REJECTED")
    )
    reason = next((x.rejection_reason for x in leg_results if x.rejection_reason), None)
    return SimulationResult(
        order_id=order_id,
        created_at=base,
        final_status=final,
        strategy=req.strategy,
        underlying=req.underlying,
        scenario=req.scenario,
        liquidity=req.liquidity,
        order_type=req.order_type,
        margin_required=required,
        margin_consumed=required
        if final == "COMPLETED"
        else round(
            required
            * sum(x.filled_quantity for x in leg_results)
            / max(1, sum(x.quantity for x in req.legs)),
            2,
        ),
        total_latency_ms=max(x.latency_ms for x in leg_results),
        partial_fill_exposure=round(exposure, 2),
        recommendation=_recommend(final, reason),
        legs=leg_results,
    )
