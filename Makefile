.PHONY: help install dev test lint run docker

help:
	@echo "Available commands:"
	@echo "  make install    Install dependencies"
	@echo "  make dev        Install dev dependencies"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linters"
	@echo "  make run        Start development server"
	@echo "  make docker     Build and run Docker containers"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=wallet_intelligence --cov-report=term-missing

lint:
	ruff check src/ tests/
	mypy src/wallet_intelligence

run:
	wallet-intel serve --reload --port 8080

docker:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

db-init:
	wallet-intel init-db

format:
	ruff format src/ tests/
