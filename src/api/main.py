from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from src.analytics.metrics import funnel, summary
from src.database.db import init_db
from src.database.seed import seed_database
from src.domain.models import SimulationRequest
from src.domain.strategies import STRATEGIES
from src.services.orders import get_order, list_orders, save_simulation
from src.simulation.engine import simulate


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Options Execution & Reliability Lab API", version="1.0.0", lifespan=lifespan
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "execution-lab-api"}


@app.get("/strategies")
def strategies():
    return {"strategies": STRATEGIES}


@app.post("/simulations")
def simulations(request: SimulationRequest):
    result = simulate(request)
    save_simulation(result, request)
    return result


@app.get("/orders")
def orders(limit: int = 100):
    return list_orders(min(limit, 5000))


@app.get("/orders/{order_id}")
def order(order_id: str):
    found = get_order(order_id)
    if not found:
        raise HTTPException(404, "Order not found")
    return found


@app.get("/analytics/summary")
def analytics_summary():
    return summary()


@app.get("/analytics/funnel")
def analytics_funnel():
    return funnel()


@app.post("/admin/seed", include_in_schema=False)
def seed():
    seed_database()
    return {"status": "seeded"}
