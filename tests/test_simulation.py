import pytest

from src.domain.models import Scenario
from src.simulation.engine import simulate


def test_deterministic_with_fixed_seed(request_factory):
    a = simulate(request_factory())
    b = simulate(request_factory())
    assert a.model_dump() == b.model_dump()


def test_successful_basket(request_factory):
    result = simulate(request_factory())
    assert result.final_status == "COMPLETED" and all(x.status == "FILLED" for x in result.legs)


def test_margin_boundary_allows_exact_funds(request_factory):
    base = request_factory()
    needed = simulate(base).margin_required
    assert simulate(request_factory(available_margin=needed)).final_status == "COMPLETED"


def test_margin_shortfall_rejects(request_factory):
    result = simulate(request_factory(available_margin=0, scenario=Scenario.NORMAL))
    assert result.final_status == "REJECTED"
    assert {x.rejection_reason for x in result.legs} == {"INSUFFICIENT_MARGIN"}


@pytest.mark.parametrize(
    "scenario,reason", [(Scenario.STALE, "STALE_QUOTE"), (Scenario.TIMEOUT, "EXCHANGE_TIMEOUT")]
)
def test_forced_rejection_scenarios(request_factory, scenario, reason):
    result = simulate(request_factory(scenario=scenario))
    assert all(x.rejection_reason == reason for x in result.legs)


def test_one_leg_rejection(request_factory):
    result = simulate(request_factory(scenario=Scenario.REJECT))
    assert result.legs[-1].status == "REJECTED"
    assert result.legs[0].status == "FILLED"


def test_partial_fill_exposes_risk(request_factory):
    result = simulate(request_factory(scenario=Scenario.PARTIAL))
    assert result.final_status == "PARTIALLY_FILLED"
    assert result.legs[0].filled_quantity < request_factory().legs[0].quantity


def test_buy_and_sell_slippage_are_adverse(request_factory):
    result = simulate(request_factory())
    assert all(x.slippage_rupees >= 0 for x in result.legs)


def test_market_faster_but_more_slippage(request_factory):
    market = simulate(request_factory(order_type="MARKET"))
    limit = simulate(request_factory(order_type="LIMIT"))
    assert market.total_latency_ms < limit.total_latency_ms
    assert sum(x.slippage_rupees for x in market.legs) > sum(x.slippage_rupees for x in limit.legs)


def test_low_liquidity_increases_latency(request_factory):
    assert (
        simulate(request_factory(liquidity="Low")).total_latency_ms
        > simulate(request_factory(liquidity="High")).total_latency_ms
    )


def test_rapid_movement_increases_slippage(request_factory):
    fast = simulate(request_factory(scenario=Scenario.MOVEMENT))
    normal = simulate(request_factory())
    assert sum(x.slippage_rupees for x in fast.legs) > sum(x.slippage_rupees for x in normal.legs)


def test_events_have_required_taxonomy(request_factory):
    events = simulate(request_factory()).legs[0].events
    assert [x.event_name for x in events[:4]] == ["Created", "Validated", "Sent", "Acknowledged"]
    assert all(x.event_id and x.timestamp and x.order_id for x in events)
