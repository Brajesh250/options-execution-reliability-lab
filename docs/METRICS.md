# Metrics

| Metric | Formula | Notes |
|---|---|---|
| Basket completion rate | completed baskets / submitted baskets | Completion requires every required leg filled |
| Strategy abandonment | unsubmitted builds / builds started | Includes builds that never reached review |
| Leg fill rate | fully filled legs / submitted legs | Partial legs are not counted as filled |
| Partial-fill rate | partially filled baskets / submitted baskets | Captures temporary directional exposure |
| Rejection rate | rejected baskets / submitted baskets | Baskets with some fills appear partial, not rejected |
| Buy slippage | fill − reference | Positive is adverse |
| Sell slippage | reference − fill | Positive is adverse |
| Median latency | 50th percentile basket latency | Robust central measure |
| P95 latency | 95th percentile basket latency | Tail-reliability measure |

All ratios use safe division and return zero when the denominator is zero. Filters define the order cohort; funnel counts remain whole-product context so users do not mistake a sliced order cohort for historical build telemetry.
