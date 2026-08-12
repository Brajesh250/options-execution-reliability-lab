from src.domain.models import LegRequest, OptionType, Side


def strategy_legs(name: str, spot: float, lots: int = 1) -> list[LegRequest]:
    step = 100 if spot < 30000 else 500
    atm = round(spot / step) * step
    qty = lots * (25 if spot < 30000 else 15)
    specs = {
        "Iron Condor": [
            ("PUT", "BUY", -2),
            ("PUT", "SELL", -1),
            ("CALL", "SELL", 1),
            ("CALL", "BUY", 2),
        ],
        "Bull Call Spread": [("CALL", "BUY", 0), ("CALL", "SELL", 1)],
        "Bear Put Spread": [("PUT", "BUY", 0), ("PUT", "SELL", -1)],
        "Long Straddle": [("CALL", "BUY", 0), ("PUT", "BUY", 0)],
        "Custom 2–4 leg strategy": [("CALL", "BUY", 0), ("CALL", "SELL", 1)],
    }[name]
    legs = []
    for i, (kind, side, offset) in enumerate(specs, 1):
        strike = atm + offset * step
        intrinsic = max(spot - strike, 0) if kind == "CALL" else max(strike - spot, 0)
        # Time value falls as a strike moves away from ATM; intrinsic value is additive.
        time_value = spot * 0.006 / (1 + abs(offset) * 0.55)
        premium = round(max(8, intrinsic + time_value), 2)
        legs.append(
            LegRequest(
                leg_id=f"L{i}",
                option_type=OptionType(kind),
                side=Side(side),
                strike=strike,
                quantity=qty,
                requested_price=premium,
            )
        )
    return legs


STRATEGIES = [
    "Iron Condor",
    "Bull Call Spread",
    "Bear Put Spread",
    "Long Straddle",
    "Custom 2–4 leg strategy",
]
