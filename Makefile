.PHONY: setup data train test api web dev docker clean lint format check-drift check-colors e2e

PYTHON = python

setup:
	$(PYTHON) -m pip install -r requirements.txt
	cd web && npm install

data:
	$(PYTHON) scripts/make_data.py

train:
	$(PYTHON) scripts/train.py

test:
	$(PYTHON) -m pytest tests/ --cov=src/nutri --cov-report=term-missing --cov-report=html

api:
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

web:
	cd web && npm run dev

dev:
	@echo "Starting backend API on port 8000 and frontend on port 5173..."
	@echo "Run 'make api' in one terminal and 'make web' in another terminal."

docker:
	docker-compose up --build

check-colors:
	$(PYTHON) scripts/check_colors.py

e2e:
	$(PYTHON) scripts/run_e2e_tests.py

lint:
	$(PYTHON) -m ruff check src/ api/ tests/ scripts/
	$(PYTHON) -m mypy src/ api/

format:
	$(PYTHON) -m ruff format src/ api/ tests/ scripts/

check-drift:
	$(PYTHON) scripts/check_drift.py
