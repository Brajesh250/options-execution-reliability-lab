from sqlalchemy import select

from src.database.db import session_scope
from src.database.tables import (
    AccountSnapshot,
    BasketOrder,
    ExecutionEventRow,
    OrderLeg,
    StrategyBuild,
)


def save_simulation(result, request, build_id=None):
    slips = [x.slippage_rupees for x in result.legs if x.slippage_rupees is not None]
    with session_scope() as db:
        if db.get(BasketOrder, result.order_id):
            return result.order_id
        if build_id is None:
            build_id = f"build-{result.order_id}"
            db.add(
                StrategyBuild(
                    build_id=build_id,
                    session_id=request.session_id,
                    timestamp=result.created_at.replace(tzinfo=None),
                    strategy=result.strategy,
                    underlying=result.underlying,
                    reviewed=True,
                    submitted=True,
                )
            )
        funds = request.available_margin + request.pledged_collateral * 0.8
        db.add(
            BasketOrder(
                order_id=result.order_id,
                build_id=build_id,
                session_id=request.session_id,
                created_at=result.created_at.replace(tzinfo=None),
                strategy=result.strategy,
                underlying=result.underlying,
                liquidity=result.liquidity,
                order_type=result.order_type,
                scenario=result.scenario,
                final_status=result.final_status,
                margin_required=result.margin_required,
                margin_utilization=result.margin_required / max(funds, 1),
                latency_ms=result.total_latency_ms,
                avg_slippage=sum(slips) / len(slips) if slips else 0,
                partial_fill_exposure=result.partial_fill_exposure,
                recommendation=result.recommendation,
            )
        )
        for leg in result.legs:
            db.add(
                OrderLeg(
                    order_id=result.order_id,
                    leg_id=leg.leg_id,
                    status=leg.status,
                    requested_price=leg.requested_price,
                    fill_price=leg.fill_price,
                    filled_quantity=leg.filled_quantity,
                    slippage_rupees=leg.slippage_rupees,
                    slippage_bps=leg.slippage_bps,
                    latency_ms=leg.latency_ms,
                    rejection_reason=leg.rejection_reason,
                )
            )
            for e in leg.events:
                db.add(
                    ExecutionEventRow(
                        event_id=e.event_id,
                        timestamp=e.timestamp.replace(tzinfo=None),
                        session_id=e.session_id,
                        order_id=e.order_id,
                        leg_id=e.leg_id,
                        event_name=e.event_name,
                        status=e.status,
                        latency_ms=e.latency_ms,
                        metadata_json=e.metadata,
                    )
                )
        db.add(
            AccountSnapshot(
                snapshot_id=f"snap-{result.order_id}",
                order_id=result.order_id,
                timestamp=result.created_at.replace(tzinfo=None),
                available_margin=request.available_margin,
                pledged_collateral=request.pledged_collateral,
                margin_consumed=result.margin_consumed,
            )
        )
    return result.order_id


def list_orders(limit=5000):
    with session_scope() as db:
        rows = db.scalars(
            select(BasketOrder).order_by(BasketOrder.created_at.desc()).limit(limit)
        ).all()
        return [{c.name: getattr(x, c.name) for c in BasketOrder.__table__.columns} for x in rows]


def get_order(order_id):
    with session_scope() as db:
        order = db.get(BasketOrder, order_id)
        if not order:
            return None
        legs = db.scalars(select(OrderLeg).where(OrderLeg.order_id == order_id)).all()
        events = db.scalars(
            select(ExecutionEventRow)
            .where(ExecutionEventRow.order_id == order_id)
            .order_by(ExecutionEventRow.timestamp)
        ).all()
        return {
            "order": {c.name: getattr(order, c.name) for c in BasketOrder.__table__.columns},
            "legs": [
                {c.name: getattr(x, c.name) for c in OrderLeg.__table__.columns} for x in legs
            ],
            "events": [
                {c.name: getattr(x, c.name) for c in ExecutionEventRow.__table__.columns}
                for x in events
            ],
        }
