import pandas as pd

from src.analytics.metrics import apply_filters, safe_div, summary


def test_safe_zero_denominator():
    assert safe_div(10, 0) == 0


def test_empty_dataset_summary():
    orders = pd.DataFrame()
    legs = pd.DataFrame()
    result = summary(orders, legs, (0, 0))
    assert result["basket_completion_rate"] == 0 and result["p95_latency_ms"] == 0


def test_kpi_formulas():
    orders = pd.DataFrame(
        {
            "final_status": ["COMPLETED", "REJECTED", "PARTIALLY_FILLED", "COMPLETED"],
            "latency_ms": [100, 200, 300, 400],
            "avg_slippage": [1.0, 2.0, 3.0, 4.0],
        }
    )
    legs = pd.DataFrame({"status": ["FILLED", "FILLED", "REJECTED", "PARTIALLY_FILLED"]})
    k = summary(orders, legs, (5, 4))
    assert k["basket_completion_rate"] == 0.5
    assert k["abandonment_rate"] == 0.2
    assert k["leg_fill_rate"] == 0.5
    assert k["partial_fill_rate"] == 0.25
    assert k["rejection_rate"] == 0.25
    assert k["median_latency_ms"] == 250
    assert k["average_slippage"] == 2.5


def test_filters():
    df = pd.DataFrame(
        {
            "created_at": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "underlying": ["NIFTY", "BANKNIFTY"],
        }
    )
    out = apply_filters(df, start=pd.Timestamp("2026-01-02").date(), underlying=["BANKNIFTY"])
    assert len(out) == 1


def test_empty_filters():
    assert apply_filters(pd.DataFrame()).empty
