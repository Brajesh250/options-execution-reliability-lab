import streamlit as st

from src.analytics.metrics import orders_frame, summary
from src.ui.theme import header


def render():
    header(
        "PRODUCT MEMO",
        "Methodology & Product Insights",
        "Assumptions, event taxonomy, metric definitions, and decisions behind the lab.",
    )
    df = orders_frame()
    k = summary()
    st.markdown("""
### Product problem
Multi-leg orders can appear as one customer action while failing across several exchange and risk-control steps. This lab gives product, operations, and learning users a safe way to diagnose that hidden lifecycle.

### Users and use cases
Product managers monitor basket reliability; trading operations reconstruct failures; retail options learners explore execution mechanics without placing real trades.

### System architecture
Streamlit and FastAPI call the same Pydantic domain models, simulation engine, service layer, and SQLite repository. Analytics read normalized event and order tables; an idempotent seed command rebuilds the demo dataset.

### Event taxonomy
Each leg emits `Created → Validated → Sent → Acknowledged → Filled / Partially Filled / Rejected / Cancelled`, with session, basket, leg, timestamp, status, latency, and reason metadata.

### Metric definitions
- Basket completion = completed baskets ÷ submitted baskets.
- Abandonment = unsubmitted builds ÷ builds started.
- Leg fill rate = fully filled legs ÷ submitted legs.
- Partial-fill and rejection rates use submitted baskets as denominator.
- Buy slippage = fill − reference; sell slippage = reference − fill.
- P95 latency is the 95th percentile of basket execution latency. Zero denominators return 0.

### Simulation assumptions
Quotes are synthetic. Pledged collateral receives an 80% haircut. Option premiums use a simple intrinsic-plus-time-value heuristic. Low liquidity raises lognormal latency and slippage; limit orders reduce slippage but run slower. A basket completes only if every leg fills. Margin estimates are educational approximations—not broker SPAN calculations.

### Known limitations
No order book, Greeks, volatility surface, brokerage/tax model, real exchange calendar, or broker integration. Seeded causality is designed for product analysis and does not forecast markets.

### Testing strategy
Unit tests cover risk boundaries, deterministic execution, all forced scenarios, safe metrics, database setup, API contracts, and empty-data behavior. CI runs Ruff and Pytest with coverage enforcement.
""")
    st.markdown("### Five insights from the current synthetic dataset")
    if df.empty:
        st.warning("Seed data to generate insights.")
        return
    low = df[df.liquidity == "Low"]
    high = df[df.liquidity == "High"]
    limit = df[df.order_type == "LIMIT"]
    market = df[df.order_type == "MARKET"]
    st.markdown(f"""
1. Overall basket completion is **{k["basket_completion_rate"]:.1%}**, leaving a visible reliability opportunity between submission and completion.
2. Low-liquidity baskets complete at **{(low.final_status == "COMPLETED").mean():.1%}** versus **{(high.final_status == "COMPLETED").mean():.1%}** in high liquidity; pre-trade liquidity warnings should be contextual.
3. P95 basket latency is **{k["p95_latency_ms"]:,.0f} ms**, substantially above the **{k["median_latency_ms"]:,.0f} ms** median; operations alerts should use tail latency, not only averages.
4. Market orders average **₹{market.avg_slippage.mean():.2f}** adverse slippage versus **₹{limit.avg_slippage.mean():.2f}** for limits, supporting a price-certainty vs fill-certainty explainer.
5. Partial baskets occur in **{k["partial_fill_rate"]:.1%}** of submissions; the UI should expose residual delta and one-tap hedge/cancel actions.

### Recommended real-platform improvements
Add live margin preview, quote-age badges, per-leg retry guards, exchange reconciliation after timeout, residual-risk telemetry, and cohort alerts by strategy/liquidity. Instrument every transition with trace IDs and publish SLOs for completion, tail latency, and price quality.
""")
