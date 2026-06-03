# ============================================
# AI Traffic Cop System - Makefile
# ============================================

.PHONY: help install dev test lint run docker clean models

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# -------- Setup --------

install: ## Install all dependencies
	pip install -r requirements.txt

dev: ## Install dev dependencies (testing, linting)
	pip install -r requirements.txt
	pip install ruff pytest-cov

# -------- Running --------

run: ## Run the backend API server
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend: ## Run the React frontend
	cd frontend && npm install && npm start

run-all: ## Run both backend and frontend (requires tmux)
	tmux new-session -d -s traffic-cop 'make run'
	tmux split-window -h 'make run-frontend'
	tmux attach-session -t traffic-cop

# -------- Testing --------

test: ## Run all tests
	pytest tests/ -v

test-cov: ## Run tests with coverage report
	pytest tests/ -v --cov=backend --cov=ai_engine --cov-report=term-missing --cov-report=html

# -------- Linting --------

lint: ## Run linter (ruff)
	ruff check . --ignore E501

lint-fix: ## Fix linting errors automatically
	ruff check . --fix --ignore E501

# -------- Docker --------

docker-build: ## Build Docker image
	docker build -f docker/Dockerfile -t ai-traffic-cop .

docker-run: ## Run with Docker Compose
	cd docker && docker-compose up --build

docker-stop: ## Stop Docker Compose
	cd docker && docker-compose down

# -------- AI Models --------

models: ## Download YOLOv8 model weights
	python scripts/download_models.py --model yolov8n

models-all: ## Download all model variants
	python scripts/download_models.py --all

train: ## Train custom model (requires dataset in data/annotations/)
	python scripts/train_model.py

# -------- Database --------

db-reset: ## Reset the database (delete and recreate)
	rm -f data/traffic_cop.db
	python -c "import asyncio; from backend.app.services.db_service import init_db; asyncio.run(init_db())"

# -------- Cleanup --------

clean: ## Remove generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf frontend/node_modules frontend/build
	rm -rf models/training
