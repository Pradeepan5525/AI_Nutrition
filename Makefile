.PHONY: setup data train test api app docker clean lint format check-drift

PYTHON = python

setup:
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) scripts/make_data.py

train:
	$(PYTHON) scripts/train.py

test:
	$(PYTHON) -m pytest tests/ --cov=src/nutri --cov-report=term-missing --cov-report=html

api:
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

app:
	$(PYTHON) -m streamlit run app/Home.py --server.port 8501 --server.address 0.0.0.0

docker:
	docker-compose up --build

lint:
	$(PYTHON) -m ruff check src/ api/ app/ tests/ scripts/
	$(PYTHON) -m mypy src/ api/

format:
	$(PYTHON) -m ruff format src/ api/ app/ tests/ scripts/

check-drift:
	$(PYTHON) scripts/check_drift.py
