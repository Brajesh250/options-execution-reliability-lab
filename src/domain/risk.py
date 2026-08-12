import numpy as np

from src.domain.models import LegRequest, Side


def net_premium(legs: list[LegRequest]) -> float:
    return round(
        sum((1 if x.side == Side.SELL else -1) * x.requested_price * x.quantity for x in legs), 2
    )


def estimate_margin(legs: list[LegRequest], spot: float) -> float:
    naked = sum(spot * x.quantity * 0.12 for x in legs if x.side == Side.SELL)
    debit = sum(x.requested_price * x.quantity for x in legs if x.side == Side.BUY)
    hedges = sum(1 for x in legs if x.side == Side.BUY)
    return round(max(debit, naked * max(0.35, 1 - 0.2 * hedges)), 2)


def payoff(legs: list[LegRequest], prices: np.ndarray) -> np.ndarray:
    result = np.zeros_like(prices, dtype=float)
    for leg in legs:
        intrinsic = (
            np.maximum(prices - leg.strike, 0)
            if leg.option_type == "CALL"
            else np.maximum(leg.strike - prices, 0)
        )
        pnl = intrinsic - leg.requested_price
        result += pnl * leg.quantity * (1 if leg.side == Side.BUY else -1)
    return result


def risk_summary(legs: list[LegRequest], spot: float) -> dict:
    prices = np.linspace(max(1, spot * 0.5), spot * 1.5, 2001)
    pnl = payoff(legs, prices)
    crossings = []
    for a, b, y1, y2 in zip(prices[:-1], prices[1:], pnl[:-1], pnl[1:]):
        if y1 == 0 or y1 * y2 < 0:
            crossings.append(round(float(a if y1 == 0 else a - y1 * (b - a) / (y2 - y1)), 2))
    max_profit = None if pnl[-1] > pnl[-2] else round(float(pnl.max()), 2)
    max_loss = None if pnl[0] < pnl[1] or pnl[-1] < pnl[-2] else round(float(-pnl.min()), 2)
    return {
        "prices": prices,
        "payoff": pnl,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "break_evens": sorted(set(crossings)),
    }
