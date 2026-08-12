import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.metrics import apply_filters, funnel, legs_frame, orders_frame, summary
from src.ui.theme import header


def render():
    header(
        "PRODUCT INTELLIGENCE",
        "Execution Analytics",
        "Reliability, latency, price quality, and funnel health across synthetic sessions.",
    )
    df = orders_frame()
    if df.empty:
        st.warning("No orders available. Seed or simulate an order first.")
        return
    with st.expander("Filters", expanded=True):
        a, b, c = st.columns(3)
        dates = a.date_input("Date range", (df.created_at.min().date(), df.created_at.max().date()))
        underlying = b.multiselect("Underlying", sorted(df.underlying.unique()))
        strategy = c.multiselect("Strategy", sorted(df.strategy.unique()))
        d, e, f = st.columns(3)
        liquidity = d.multiselect("Liquidity", sorted(df.liquidity.unique()))
        order_type = e.multiselect("Order type", sorted(df.order_type.unique()))
        final_status = f.multiselect("Final status", sorted(df.final_status.unique()))
    start, end = dates if isinstance(dates, tuple) and len(dates) == 2 else (None, None)
    filtered = apply_filters(
        df,
        start,
        end,
        underlying=underlying,
        strategy=strategy,
        liquidity=liquidity,
        order_type=order_type,
        final_status=final_status,
    )
    global_k = summary()
    submitted_builds = round(
        global_k["strategy_builds_started"] * (1 - global_k["abandonment_rate"])
    )
    all_legs = legs_frame()
    filtered_legs = all_legs[all_legs.order_id.isin(filtered.order_id)]
    k = summary(
        filtered,
        filtered_legs,
        (global_k["strategy_builds_started"], submitted_builds),
    )
    cards = [
        ("Builds", k["strategy_builds_started"], None),
        ("Submitted", k["orders_submitted"], None),
        ("Completed", k["completed_orders"], None),
        ("Completion", k["basket_completion_rate"], "pct"),
        ("Abandonment", k["abandonment_rate"], "pct"),
        ("Partial fill", k["partial_fill_rate"], "pct"),
        ("Rejection", k["rejection_rate"], "pct"),
        ("Median latency", k["median_latency_ms"], "ms"),
        ("P95 latency", k["p95_latency_ms"], "ms"),
        ("Avg slippage", k["average_slippage"], "rupee"),
    ]
    cols = st.columns(5)
    for i, (label, value, fmt) in enumerate(cards):
        cols[i % 5].metric(
            label,
            f"{value:.1%}"
            if fmt == "pct"
            else f"{value:,.0f} ms"
            if fmt == "ms"
            else f"₹{value:.2f}"
            if fmt == "rupee"
            else f"{value:,}",
        )
    if filtered.empty:
        st.warning("No orders match these filters.")
        return
    dark = dict(
        template="plotly_dark",
        paper_bgcolor="#0d1a2c",
        plot_bgcolor="#0d1a2c",
        margin=dict(l=10, r=10, t=45, b=10),
        height=330,
    )
    left, right = st.columns(2)
    fun = pd.DataFrame(funnel())
    fig = px.funnel(
        fun, x="count", y="stage", title="Product funnel", color_discrete_sequence=["#47d7ac"]
    )
    fig.update_layout(**dark)
    left.plotly_chart(fig, use_container_width=True)
    rate = (
        filtered.groupby("strategy")
        .final_status.apply(lambda s: (s == "COMPLETED").mean())
        .reset_index(name="completion_rate")
    )
    fig = px.bar(
        rate,
        x="strategy",
        y="completion_rate",
        title="Completion rate by strategy",
        color_discrete_sequence=["#78d9ff"],
    )
    fig.update_layout(**dark, yaxis_tickformat=".0%")
    right.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    fails = filtered[filtered.final_status != "COMPLETED"].scenario.value_counts().reset_index()
    fig = px.bar(
        fails,
        x="count",
        y="scenario",
        orientation="h",
        title="Failure reasons",
        color_discrete_sequence=["#ff6b79"],
    )
    fig.update_layout(**dark)
    left.plotly_chart(fig, use_container_width=True)
    fig = px.histogram(
        filtered,
        x="latency_ms",
        nbins=35,
        title="Latency distribution",
        color_discrete_sequence=["#f5b942"],
    )
    fig.update_layout(**dark)
    right.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    fig = px.histogram(
        filtered,
        x="avg_slippage",
        nbins=35,
        title="Slippage distribution",
        color_discrete_sequence=["#47d7ac"],
    )
    fig.update_layout(**dark)
    left.plotly_chart(fig, use_container_width=True)
    daily = (
        filtered.assign(day=filtered.created_at.dt.date)
        .groupby("day")
        .agg(
            volume=("order_id", "size"),
            completion=("final_status", lambda s: (s == "COMPLETED").mean()),
        )
        .reset_index()
    )
    fig = px.line(
        daily, x="day", y=["volume", "completion"], title="Daily volume and completion trend"
    )
    fig.update_layout(**dark)
    right.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    liq = (
        filtered.groupby("liquidity")
        .final_status.apply(lambda s: (s == "COMPLETED").mean())
        .reset_index(name="success_rate")
    )
    fig = px.bar(
        liq, x="liquidity", y="success_rate", title="Success rate by liquidity", color="liquidity"
    )
    fig.update_layout(**dark, yaxis_tickformat=".0%", showlegend=False)
    left.plotly_chart(fig, use_container_width=True)
    bins = pd.cut(
        filtered.margin_utilization,
        [0, 0.5, 0.8, 1, 10],
        labels=["0–50%", "50–80%", "80–100%", ">100%"],
    )
    band = (
        filtered.assign(band=bins)
        .groupby("band", observed=False)
        .scenario.apply(lambda s: (s == "Insufficient margin").sum())
        .reset_index(name="failures")
    )
    fig = px.bar(
        band,
        x="band",
        y="failures",
        title="Margin failures by utilization band",
        color_discrete_sequence=["#ff6b79"],
    )
    fig.update_layout(**dark)
    right.plotly_chart(fig, use_container_width=True)
