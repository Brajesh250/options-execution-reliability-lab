# Testing and QA

## Automated

`pytest --cov --cov-report=term-missing` runs 30 tests covering template/risk math, margin boundaries, request validation, fixed-seed determinism, successful execution, buy/sell slippage, market-vs-limit behavior, liquidity and rapid movement, stale quotes, one-leg rejection, partial fills, timeouts, event taxonomy, KPI/funnel arithmetic, filters, empty data, database schema, and API contracts.

The verified local result is **30 passed** with **89.7% core coverage**. Coverage is measured over `src/domain`, `src/simulation`, and `src/analytics`, with an 80% gate. `ruff check .` passes. CI repeats both checks on Python 3.11.

## Manual checklist

- Simulator: switch templates/underlyings; edit legs; trigger success, margin, stale, partial, reject, and timeout states
- Analytics: confirm every filter updates KPI cohort and charts; check empty filter state
- Explorer: search ID/strategy, filter status, download CSV, inspect legs and ordered events
- Methodology: verify computed insights render with non-empty seed data
- Responsive: desktop and narrow viewport; readable controls, no horizontal page overflow
- API: `/health`, `/docs`, simulation, orders, details, summary, funnel

## Seed integrity

The checked local dataset contains 1,601 baskets (1 test-created plus 1,600 seed), 4,006 legs, 20,030 events, and 1,920 builds across 90 days. The database is ignored and reproducible.
