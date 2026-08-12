from fastapi.testclient import TestClient
from sqlalchemy import inspect

from src.api.main import app
from src.database.db import engine, init_db
from src.domain.models import Scenario


def test_database_initialization():
    init_db()
    names = set(inspect(engine).get_table_names())
    assert {
        "strategy_builds",
        "basket_orders",
        "order_legs",
        "execution_events",
        "account_snapshots",
    } <= names


def test_api_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200 and response.json()["status"] == "ok"


def test_api_strategies():
    assert len(TestClient(app).get("/strategies").json()["strategies"]) == 5


def test_api_simulation(request_factory):
    req = request_factory(scenario=Scenario.NORMAL)
    response = TestClient(app).post("/simulations", json=req.model_dump(mode="json"))
    assert response.status_code == 200 and response.json()["final_status"] == "COMPLETED"


def test_missing_order_404():
    assert TestClient(app).get("/orders/not-real").status_code == 404
