UV := uv run
APP := src.main:app
COMPOSE := docker compose

.PHONY: help install run ruff-check ruff-format test test-unit test-integration \
test-api test-e2e test-cov migrate up down


help:
	@echo "Доступные команды:"
	@printf "  make install            - Установить зависимости\n"
	@printf "  make up                 - Поднять Docker-контейнеры\n"
	@printf "  make down               - Остановить Docker-контейнеры\n"
	@printf "  make run                - Запустить приложение\n"
	@printf "  make ruff-check         - Проверить код линтером\n"
	@printf "  make ruff-format        - Отформатировать код\n"
	@printf "  make test               - Запустить все тесты\n"
	@printf "  make test-unit          - Запустить юнит-тесты\n"
	@printf "  make test-integration   - Запустить интеграционные тесты без API\n"
	@printf "  make test-api           - Запустить тесты API\n"
	@printf "  make test-e2e           - Запустить тесты end-2-end\n"
	@printf "  make test-cov           - Запустить вычисление покрытия тестов\n"
	@printf "  make migrate            - Применить миграции Piccolo\n"

install:
	uv sync

up:
	$(COMPOSE) up -d --wait postgres neo4j

down:
	$(COMPOSE) down

run: up
	$(UV) uvicorn $(APP)

ruff-check:
	$(UV) ruff check .
	$(UV) ruff format --check .

ruff-format:
	$(UV) ruff format .
	$(UV) ruff check --fix .

test:
	$(UV) pytest -v

test-unit:
	$(UV) pytest tests/unit

test-integration:
	$(UV) pytest tests/integration --ignore=tests/integration/api

test-api:
	$(UV) pytest tests/integration/api

test-e2e:
	@echo "e2e tests not found"

test-cov:
	$(UV) pytest --cov=src --cov-report=term-missing --cov-report=html:cov_html

migrate: up
	$(UV) piccolo migrations forwards tables

