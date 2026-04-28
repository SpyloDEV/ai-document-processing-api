.PHONY: dev test lint format migrate

dev:
	docker compose up --build

test:
	pytest

lint:
	ruff check .
	black --check .

format:
	ruff check . --fix
	black .

migrate:
	alembic upgrade head
