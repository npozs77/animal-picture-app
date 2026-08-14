.PHONY: dev build test lint fmt-check quality docker-build docker-run clean

dev:
	uv run uvicorn app.main:app --reload --port 8000

build:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

fmt-check:
	uv run ruff format --check .

quality: lint fmt-check test

docker-build:
	docker buildx build -t animal-picture-app .

docker-run:
	docker run --rm -p 8000:8000 animal-picture-app

clean:
	rm -f animals.db
	rm -rf __pycache__ app/__pycache__ tests/__pycache__
	rm -rf .venv .pytest_cache .ruff_cache
