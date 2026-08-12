from datetime import date, timedelta
from uuid import UUID, uuid5

import numpy as np
from sqlalchemy import func, select

from src.database.db import init_db, session_scope
from src.database.tables import BasketOrder, StrategyBuild
from src.domain.models import OrderType, Scenario, SimulationRequest
from src.domain.strategies import STRATEGIES, strategy_legs
from src.services.orders import save_simulation
from src.simulation.engine import simulate

NS = UUID("b41ab692-61cd-487c-a8c1-aa8f415a003b")


def seed_database(count=1600, seed=2026):
    init_db()
    with session_scope() as db:
        if db.scalar(select(func.count()).select_from(BasketOrder)) >= count:
            return
    rng = np.random.default_rng(seed)
    scenarios = [
        Scenario.NORMAL,
        Scenario.NORMAL,
        Scenario.NORMAL,
        Scenario.NORMAL,
        Scenario.RANDOM,
        Scenario.LIQUIDITY,
        Scenario.REJECT,
        Scenario.PARTIAL,
        Scenario.STALE,
        Scenario.MARGIN,
        Scenario.MOVEMENT,
        Scenario.TIMEOUT,
    ]
    today = date.today()
    for i in range(count):
        day = today - timedelta(days=int(rng.integers(0, 90)))
        underlying = "NIFTY" if rng.random() < 0.67 else "BANKNIFTY"
        spot = 24500 + rng.normal(0, 900) if underlying == "NIFTY" else 51500 + rng.normal(0, 2200)
        strategy = str(rng.choice(STRATEGIES[:-1]))
        liquidity = str(rng.choice(["High", "Medium", "Low"], p=[0.48, 0.36, 0.16]))
        scenario = rng.choice(scenarios)
        if liquidity == "Low" and rng.random() < 0.28:
            scenario = rng.choice([Scenario.LIQUIDITY, Scenario.PARTIAL, Scenario.STALE])
        order_type = OrderType.MARKET if rng.random() < 0.43 else OrderType.LIMIT
        legs = strategy_legs(strategy, spot)
        margin = float(rng.choice([50000, 100000, 200000, 400000]))
        req = SimulationRequest(
            session_id=f"seed-{i}",
            strategy=strategy,
            underlying=underlying,
            spot_price=round(spot, 2),
            expiry=today + timedelta(days=7),
            order_type=order_type,
            available_margin=margin,
            pledged_collateral=float(rng.choice([0, 25000, 50000])),
            volatility=float(rng.uniform(0.12, 0.38)),
            liquidity=liquidity,
            scenario=scenario,
            seed=seed + i,
            legs=legs,
        )
        result = simulate(req)
        result.created_at = result.created_at.replace(year=day.year, month=day.month, day=day.day)
        build_id = str(uuid5(NS, f"build-{i}"))
        with session_scope() as db:
            db.add(
                StrategyBuild(
                    build_id=build_id,
                    session_id=req.session_id,
                    timestamp=result.created_at.replace(tzinfo=None) - timedelta(minutes=2),
                    strategy=strategy,
                    underlying=underlying,
                    reviewed=True,
                    submitted=True,
                )
            )
        save_simulation(result, req, build_id)
    with session_scope() as db:
        for i in range(count // 5):
            reviewed = bool(rng.random() < 0.65)
            day = today - timedelta(days=int(rng.integers(0, 90)))
            db.add(
                StrategyBuild(
                    build_id=str(uuid5(NS, f"abandon-{i}")),
                    session_id=f"abandon-{i}",
                    timestamp=__import__("datetime").datetime.combine(
                        day, __import__("datetime").time(10)
                    ),
                    strategy=str(rng.choice(STRATEGIES[:-1])),
                    underlying=str(rng.choice(["NIFTY", "BANKNIFTY"])),
                    reviewed=reviewed,
                    submitted=False,
                )
            )


if __name__ == "__main__":
    seed_database()
    print("Seeded deterministic demo database.")
