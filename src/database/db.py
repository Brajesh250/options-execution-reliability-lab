from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "lab.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    from src.database import tables  # noqa: F401
    from src.database.tables import BasketOrder, StrategyBuild

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        missing = session.scalars(select(BasketOrder).where(BasketOrder.build_id.is_(None))).all()
        for order in missing:
            build_id = f"build-{order.order_id}"
            if session.get(StrategyBuild, build_id) is None:
                session.add(
                    StrategyBuild(
                        build_id=build_id,
                        session_id=order.session_id,
                        timestamp=order.created_at,
                        strategy=order.strategy,
                        underlying=order.underlying,
                        reviewed=True,
                        submitted=True,
                    )
                )
            order.build_id = build_id
        session.commit()


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
