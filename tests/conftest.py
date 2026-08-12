from datetime import date, timedelta

import pytest

from src.domain.models import Scenario, SimulationRequest
from src.domain.strategies import strategy_legs


@pytest.fixture
def request_factory():
    def make(**kwargs):
        data = dict(
            session_id="test",
            strategy="Bull Call Spread",
            underlying="NIFTY",
            spot_price=24500,
            expiry=date.today() + timedelta(days=7),
            order_type="LIMIT",
            available_margin=500000,
            pledged_collateral=0,
            volatility=0.2,
            liquidity="High",
            scenario=Scenario.NORMAL,
            seed=42,
            legs=strategy_legs("Bull Call Spread", 24500),
        )
        data.update(kwargs)
        return SimulationRequest(**data)

    return make
