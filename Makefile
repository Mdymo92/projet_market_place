COMPOSE := docker compose
ALL := --profile data --profile obs

.PHONY: help env up up-core down clean ps logs seed test test-unit lint fmt backup restore

help: ## List commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

env: ## Create .env from the example (first run only)
	@test -f .env || (cp .env.example .env && echo ".env created: change the passwords")

up: env ## Start everything (core + data + obs)
	$(COMPOSE) $(ALL) up -d --build
	@echo "Gateway http://localhost:8000 | Kafka UI :8080 | MinIO :9001 | Grafana :3000 | Jaeger :16686"

up-core: env ## Start databases, Kafka, gateway and services only
	$(COMPOSE) up -d --build

down: ## Stop all containers (keeps data)
	$(COMPOSE) $(ALL) down

clean: ## Stop and delete all data volumes
	$(COMPOSE) $(ALL) down -v

ps: ## Container status
	$(COMPOSE) $(ALL) ps

logs: ## Follow logs (make logs s=orders)
	$(COMPOSE) $(ALL) logs -f $(s)

seed: ## Create one test user per role
	$(COMPOSE) exec auth python -m app.seed_users

test: test-unit ## Run all local tests

test-unit: ## Unit tests (no Docker needed)
	python -m pytest tests/unit -q

lint: ## Lint Python code
	ruff check .

fmt: ## Format Python code
	ruff format .

backup: ## Dump PostgreSQL and MongoDB into ./backups
	./scripts/backup.sh

restore: ## Restore the latest dumps from ./backups
	./scripts/restore.sh
