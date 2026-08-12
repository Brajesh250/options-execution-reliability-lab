import streamlit as st

from src.database.db import init_db
from src.database.seed import seed_database
from src.ui import analytics_page, explorer, methodology, simulator
from src.ui.theme import disclaimer, inject_theme

st.set_page_config(
    page_title="Options Execution Lab",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="auto",
)
init_db()
seed_database()
inject_theme()
with st.sidebar:
    st.markdown("## OERL")
    st.caption("OPTIONS EXECUTION & RELIABILITY LAB")
    page = st.radio(
        "Navigate",
        [
            "Strategy Simulator",
            "Execution Analytics",
            "Order Explorer",
            "Methodology & Product Insights",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("SYNTHETIC MARKET · INDIA")
    st.markdown("🟢 Simulation engine online")
{
    "Strategy Simulator": simulator.render,
    "Execution Analytics": analytics_page.render,
    "Order Explorer": explorer.render,
    "Methodology & Product Insights": methodology.render,
}[page]()
disclaimer()
