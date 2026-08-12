# Portfolio Case Study — Options Execution & Reliability Lab

## 1. Context

Options baskets compress several risk and exchange actions into one product gesture. The project was built as an independent fintech portfolio artifact for product-engineering and analytics roles.

## 2. Problem statement

Teams need to distinguish customer abandonment, validation failure, quote staleness, leg rejection, partial execution, slow acknowledgement, and poor price quality without exposing users to real trading risk.

## 3. User personas

Product managers own completion and reliability; trading operations investigate incidents; retail learners need an approachable execution model.

## 4. Product hypothesis

Combining a pre-trade risk preview, lifecycle simulator, event explorer, and cohort analytics will make multi-leg failure modes more legible and produce actionable product recommendations.

## 5. Solution

Four dark-terminal views cover strategy construction, scenario simulation, filtered product analytics, order/event drill-down, and transparent methodology. Nine scenarios encode coherent relationships between liquidity, order type, margin, movement, fills, slippage, and latency.

## 6. Technical architecture

Streamlit and FastAPI reuse Pydantic domain contracts, payoff/margin functions, a deterministic NumPy engine, SQLAlchemy services, and SQLite. The seeded DB is generated at runtime for ephemeral deployment.

## 7. Event taxonomy

Every leg transitions through Created, Validated, Sent, Acknowledged, then Filled, Partially Filled, Rejected, or Cancelled. Every record carries stable event/session/order/leg identity, timestamp, status, step latency, and metadata.

## 8. Metrics

Completion, abandonment, leg fill, partial-fill, rejection, median/P95 latency, and directionally adverse slippage use explicit safe formulas documented in `METRICS.md`.

## 9. Important edge cases

Exact-margin boundary, inadequate effective collateral, stale quotes, a single rejected leg after other fills, partial quantity, exchange timeout, rapid movement, low liquidity, zero-price slippage denominator, empty analytics cohorts, and repeat simulation IDs.

## 10. Testing and reliability

Thirty tests pass with 89.7% measured coverage of domain, simulation, and analytics. Ruff passes, CI gates both checks, transactions roll back on error, and fixed seeds reproduce complete event histories.

## 11. Insights from synthetic data

The methodology view computes live observations from the seeded cohort. Designed signal includes poorer low-liquidity completion and tail latency, higher market-order slippage, margin failures at high utilization, and residual risk after partial baskets.

## 12. Product recommendations

Show quote age and margin impact before submission; explain the failed leg inline; reconcile exchange timeouts before retries; surface residual delta with hedge/cancel actions; measure tail SLOs by strategy and liquidity.

## 13. Limitations

Synthetic premiums and educational margin are not tradable prices or SPAN. There is no order book, Greeks, tax/fee engine, live exchange calendar, identity system, or broker connection.

## 14. What I would build next

Calibrated historical replay, option-chain ingestion, Greeks and residual-delta controls, a Postgres event warehouse, OpenTelemetry traces, product experiment flags, and incident alerting.

## 15. Resume-ready bullets

- Built a Python/Streamlit/FastAPI multi-leg options reliability lab with **7 documented endpoints**, 4 product views, and one shared domain/service architecture.
- Generated a deterministic **1,600-order, 90-day** synthetic cohort with more than **20,000 leg lifecycle events** for funnel, latency, slippage, and failure analysis.
- Authored **30 passing automated tests** and enforced **89.7% core coverage** plus Ruff quality checks in GitHub Actions.
