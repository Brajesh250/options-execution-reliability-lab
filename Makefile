.PHONY: install seed test lint app api
install:
	pip install -e ".[dev]"
seed:
	python -m src.database.seed
test:
	pytest --cov --cov-report=term-missing
lint:
	ruff check .
app:
	streamlit run streamlit_app.py
api:
	uvicorn src.api.main:app --reload
