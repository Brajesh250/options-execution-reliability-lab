from datetime import date, timedelta
from time import sleep

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.domain.models import LegRequest, Scenario, SimulationRequest
from src.domain.risk import estimate_margin, net_premium, risk_summary
from src.domain.strategies import STRATEGIES, strategy_legs
from src.services.orders import save_simulation
from src.simulation.engine import simulate
from src.ui.theme import header


def render():
    header(
        "LIVE LAB / SIMULATOR",
        "Strategy Simulator",
        "Configure a multi-leg basket, review risk, then observe its execution lifecycle.",
    )
    top = st.columns([1.3, 1, 1, 1])
    strategy = top[0].selectbox("Strategy template", STRATEGIES)
    underlying = top[1].selectbox("Underlying", ["NIFTY", "BANKNIFTY"])
    default_spot = 24500.0 if underlying == "NIFTY" else 51500.0
    spot = top[2].number_input("Spot price", min_value=1.0, value=default_spot, step=100.0)
    lots = top[3].number_input("Lots", 1, 10, 1)
    defaults = strategy_legs(strategy, spot, lots)
    frame = pd.DataFrame(
        [
            {
                "Leg": x.leg_id,
                "Type": x.option_type.value,
                "Side": x.side.value,
                "Strike": x.strike,
                "Quantity": x.quantity,
                "Price": x.requested_price,
            }
            for x in defaults
        ]
    )
    edited = st.data_editor(
        frame,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic" if strategy == "Custom 2–4 leg strategy" else "fixed",
        column_config={
            "Type": st.column_config.SelectboxColumn(options=["CALL", "PUT"]),
            "Side": st.column_config.SelectboxColumn(options=["BUY", "SELL"]),
            "Strike": st.column_config.NumberColumn(min_value=1),
            "Quantity": st.column_config.NumberColumn(min_value=1),
            "Price": st.column_config.NumberColumn(min_value=0.05, format="₹ %.2f"),
        },
    )
    try:
        legs = [
            LegRequest(
                leg_id=str(r.Leg),
                option_type=r.Type,
                side=r.Side,
                strike=r.Strike,
                quantity=int(r.Quantity),
                requested_price=r.Price,
            )
            for r in edited.itertuples()
        ]
        if strategy == "Custom 2–4 leg strategy" and not 2 <= len(legs) <= 4:
            st.error("Custom strategies require between 2 and 4 legs.")
            return
    except Exception as exc:
        st.error(f"Correct the leg table: {exc}")
        return
    with st.expander("Account, market & execution controls", expanded=True):
        a, b, c, d = st.columns(4)
        available = a.number_input("Available margin (₹)", 0.0, 5000000.0, 200000.0, 25000.0)
        pledged = b.number_input("Pledged collateral (₹)", 0.0, 5000000.0, 50000.0, 25000.0)
        order_type = c.selectbox("Order type", ["LIMIT", "MARKET"])
        liquidity = d.selectbox("Liquidity", ["High", "Medium", "Low"])
        e, f, g, h = st.columns(4)
        volatility = e.slider("Market volatility", 0.05, 0.80, 0.20, 0.01)
        expiry = f.date_input("Expiry", date.today() + timedelta(days=7), min_value=date.today())
        scenario = g.selectbox("Failure scenario", [x.value for x in Scenario])
        seed = h.number_input("Random seed", 0, 999999, 42)
    required = estimate_margin(legs, spot)
    funds = available + pledged * 0.8
    util = required / max(funds, 1)
    risk = risk_summary(legs, spot)
    premium = net_premium(legs)
    m = st.columns(5)
    m[0].metric("Net premium", f"₹{premium:,.0f}")
    m[1].metric("Margin required", f"₹{required:,.0f}")
    m[2].metric("Effective funds", f"₹{funds:,.0f}")
    m[3].metric("Margin utilization", f"{util:.1%}")
    m[4].metric("Break-evens", ", ".join(f"{x:,.0f}" for x in risk["break_evens"]) or "—")
    if util > 1:
        st.error("Insufficient effective funds: this basket will fail margin validation.")
    elif util > 0.8:
        st.warning("High margin utilization leaves little buffer for market movement.")
    chart = go.Figure(
        go.Scatter(x=risk["prices"], y=risk["payoff"], fill="tozeroy", line_color="#47d7ac")
    )
    chart.add_hline(y=0, line_color="#60758a")
    chart.add_vline(x=spot, line_dash="dot", line_color="#f5b942")
    chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1a2c",
        plot_bgcolor="#0d1a2c",
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        title=f"Expiry payoff · Max profit {risk['max_profit'] if risk['max_profit'] is not None else 'Unbounded'} · Max loss {risk['max_loss'] if risk['max_loss'] is not None else 'Unbounded'}",
        xaxis_title="Underlying at expiry",
        yaxis_title="P&L (₹)",
    )
    st.plotly_chart(chart, use_container_width=True)
    if st.button("Simulate Basket Order", type="primary", use_container_width=True):
        request = SimulationRequest(
            session_id=f"ui-{seed}",
            strategy=strategy,
            underlying=underlying,
            spot_price=spot,
            expiry=expiry,
            order_type=order_type,
            available_margin=available,
            pledged_collateral=pledged,
            volatility=volatility,
            liquidity=liquidity,
            scenario=scenario,
            seed=seed,
            legs=legs,
        )
        result = simulate(request)
        save_simulation(result, request)
        with st.status("Executing basket…", expanded=True) as execution_status:
            for leg in result.legs:
                for event in leg.events:
                    st.write(f"`{leg.leg_id}` · {event.event_name} · {event.status}")
                    sleep(0.04)
            execution_status.update(
                label=f"Basket {result.final_status}",
                state="complete" if result.final_status == "COMPLETED" else "error",
                expanded=False,
            )
        st.session_state.last_result = result
    result = st.session_state.get("last_result")
    if result:
        color = {"COMPLETED": "green", "PARTIALLY_FILLED": "amber"}.get(result.final_status, "red")
        st.markdown(
            f"### Basket result · <span class='{color}'>{result.final_status}</span>",
            unsafe_allow_html=True,
        )
        c = st.columns(4)
        c[0].metric("Latency", f"{result.total_latency_ms:,.0f} ms")
        c[1].metric("Margin consumed", f"₹{result.margin_consumed:,.0f}")
        c[2].metric("Partial exposure", f"₹{result.partial_fill_exposure:,.0f}")
        c[3].metric("Order", result.order_id[:8])
        rows = []
        for leg in result.legs:
            rows.append(
                {
                    "Leg": leg.leg_id,
                    "Status": leg.status,
                    "Requested": leg.requested_price,
                    "Fill": leg.fill_price,
                    "Slippage ₹": leg.slippage_rupees,
                    "Slippage bps": leg.slippage_bps,
                    "Latency ms": leg.latency_ms,
                    "Reason": leg.rejection_reason,
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.info(result.recommendation)
        for leg in result.legs:
            with st.expander(f"{leg.leg_id} event timeline · {leg.status}"):
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Time": e.timestamp.strftime("%H:%M:%S.%f")[:-3],
                                "Event": e.event_name,
                                "Status": e.status,
                                "Step latency (ms)": e.latency_ms,
                            }
                            for e in leg.events
                        ]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
