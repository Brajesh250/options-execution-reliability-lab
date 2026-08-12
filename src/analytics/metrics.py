import pandas as pd
from sqlalchemy import select

from src.database.db import session_scope
from src.database.tables import OrderLeg, StrategyBuild
from src.services.orders import list_orders


def safe_div(n, d):
    return float(n / d) if d else 0.0


def orders_frame():
    df = pd.DataFrame(list_orders())
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def legs_frame():
    with session_scope() as db:
        rows = db.scalars(select(OrderLeg)).all()
        return pd.DataFrame(
            [{c.name: getattr(x, c.name) for c in OrderLeg.__table__.columns} for x in rows]
        )


def apply_filters(df, start=None, end=None, **filters):
    if df.empty:
        return df
    out = df.copy()
    if start is not None:
        out = out[out.created_at.dt.date >= start]
    if end is not None:
        out = out[out.created_at.dt.date <= end]
    for col, values in filters.items():
        if values and col in out:
            out = out[out[col].isin(values)]
    return out


def summary(df=None, legs=None, build_counts=None):
    df = orders_frame() if df is None else df
    legs = legs_frame() if legs is None else legs
    if build_counts is None:
        with session_scope() as db:
            builds = db.scalars(select(StrategyBuild)).all()
            build_counts = (len(builds), sum(x.submitted for x in builds))
    submitted = len(df)
    completed = int((df.final_status == "COMPLETED").sum()) if submitted else 0
    partially = int((df.final_status == "PARTIALLY_FILLED").sum()) if submitted else 0
    rejected = int((df.final_status == "REJECTED").sum()) if submitted else 0
    filled_legs = int((legs.status == "FILLED").sum()) if not legs.empty else 0
    return {
        "strategy_builds_started": build_counts[0],
        "orders_submitted": submitted,
        "completed_orders": completed,
        "basket_completion_rate": safe_div(completed, submitted),
        "abandonment_rate": safe_div(build_counts[0] - build_counts[1], build_counts[0]),
        "leg_fill_rate": safe_div(filled_legs, len(legs)),
        "partial_fill_rate": safe_div(partially, submitted),
        "rejection_rate": safe_div(rejected, submitted),
        "median_latency_ms": float(df.latency_ms.median()) if submitted else 0,
        "p95_latency_ms": float(df.latency_ms.quantile(0.95)) if submitted else 0,
        "average_slippage": float(df.avg_slippage.mean()) if submitted else 0,
    }


def funnel():
    with session_scope() as db:
        builds = db.scalars(select(StrategyBuild)).all()
    started = len(builds)
    reviewed = sum(x.reviewed for x in builds)
    submitted = sum(x.submitted for x in builds)
    completed = summary()["completed_orders"]
    return [
        {"stage": x, "count": y}
        for x, y in [
            ("Build Started", started),
            ("Strategy Reviewed", reviewed),
            ("Order Submitted", submitted),
            ("Basket Completed", completed),
        ]
    ]
