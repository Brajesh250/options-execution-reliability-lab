import pandas as pd
import streamlit as st

from src.analytics.metrics import orders_frame
from src.services.orders import get_order
from src.ui.theme import header


def render():
    header(
        "OPERATIONS CONSOLE",
        "Order Explorer",
        "Search baskets, inspect leg outcomes, and reconstruct the execution timeline.",
    )
    df = orders_frame()
    if df.empty:
        st.warning("No orders available.")
        return
    a, b, c = st.columns([2, 1, 1])
    query = a.text_input("Search order ID, session, or strategy")
    status = b.multiselect("Status", sorted(df.final_status.unique()))
    underlying = c.multiselect("Underlying", sorted(df.underlying.unique()))
    view = df.copy()
    if query:
        view = view[
            view.astype(str).apply(lambda row: row.str.contains(query, case=False).any(), axis=1)
        ]
    if status:
        view = view[view.final_status.isin(status)]
    if underlying:
        view = view[view.underlying.isin(underlying)]
    st.download_button(
        "Download filtered CSV", view.to_csv(index=False), "filtered_orders.csv", "text/csv"
    )
    st.dataframe(
        view[
            [
                "created_at",
                "order_id",
                "strategy",
                "underlying",
                "liquidity",
                "order_type",
                "final_status",
                "latency_ms",
                "avg_slippage",
            ]
        ],
        hide_index=True,
        use_container_width=True,
        height=330,
    )
    if view.empty:
        return
    selected = st.selectbox(
        "Inspect basket",
        view.order_id.tolist(),
        format_func=lambda x: f"{x[:8]} · {view.loc[view.order_id == x, 'strategy'].iloc[0]}",
    )
    detail = get_order(selected)
    order = detail["order"]
    st.markdown(f"### {selected[:8]} · {order['final_status']}")
    a, b, c, d = st.columns(4)
    a.metric("Latency", f"{order['latency_ms']:,.0f} ms")
    b.metric("Slippage", f"₹{order['avg_slippage']:.2f}")
    c.metric("Margin util.", f"{order['margin_utilization']:.1%}")
    d.metric("Exposure", f"₹{order['partial_fill_exposure']:,.0f}")
    st.info(order["recommendation"])
    st.markdown("#### Leg outcomes")
    st.dataframe(pd.DataFrame(detail["legs"]), hide_index=True, use_container_width=True)
    st.markdown("#### Event history")
    events = pd.DataFrame(detail["events"])
    st.dataframe(
        events[["timestamp", "leg_id", "event_name", "status", "latency_ms", "metadata_json"]],
        hide_index=True,
        use_container_width=True,
    )
