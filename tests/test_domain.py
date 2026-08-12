import numpy as np
import pytest
from pydantic import ValidationError

from src.domain.models import LegRequest, SimulationRequest
from src.domain.risk import estimate_margin, net_premium, payoff, risk_summary
from src.domain.strategies import STRATEGIES, strategy_legs


def test_all_templates_have_two_to_four_legs():
    assert all(2 <= len(strategy_legs(s, 24500)) <= 4 for s in STRATEGIES)


def test_lot_size_switches_for_banknifty():
    assert strategy_legs("Long Straddle", 51000)[0].quantity == 15


def test_net_premium_and_margin_positive():
    legs = strategy_legs("Iron Condor", 24500)
    assert isinstance(net_premium(legs), float)
    assert estimate_margin(legs, 24500) > 0


def test_debit_strategy_margin_is_premium():
    legs = strategy_legs("Long Straddle", 24500)
    assert estimate_margin(legs, 24500) == sum(x.requested_price * x.quantity for x in legs)


def test_payoff_shape_and_risk_summary():
    legs = strategy_legs("Bull Call Spread", 24500)
    values = payoff(legs, np.array([20000.0, 24500.0, 30000.0]))
    assert len(values) == 3 and values[-1] > values[0]
    risk = risk_summary(legs, 24500)
    assert risk["max_profit"] is not None and risk["break_evens"]


def test_invalid_leg_quantity():
    with pytest.raises(ValidationError):
        LegRequest(
            leg_id="L1", option_type="CALL", side="BUY", strike=100, quantity=0, requested_price=2
        )


def test_invalid_underlying(request_factory):
    data = request_factory().model_dump()
    data["underlying"] = "SENSEX"
    with pytest.raises(ValidationError):
        SimulationRequest(**data)
