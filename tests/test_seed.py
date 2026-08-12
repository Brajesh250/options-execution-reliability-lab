from concurrent.futures import ThreadPoolExecutor
from time import sleep

from src.database import seed


def test_concurrent_seed_calls_are_serialized(monkeypatch):
    active = 0
    max_active = 0

    def fake_seed(_count, _seed):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        sleep(0.02)
        active -= 1

    monkeypatch.setattr(seed, "_seed_database", fake_seed)
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: seed.seed_database(10, 1), range(2)))

    assert max_active == 1
