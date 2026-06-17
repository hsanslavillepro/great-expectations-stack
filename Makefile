UV_CACHE_DIR ?= .uv-cache
VENV ?= .venv
PYTHON_VERSION ?= 3.12
BIN := $(VENV)/bin
LOCAL_CONFIG ?= configs/freshness.local-postgres.yml
ENV_FILE ?= .env
ENV_SOURCE := $(if $(findstring /,$(ENV_FILE)),$(ENV_FILE),./$(ENV_FILE))

.DEFAULT_GOAL := help

.PHONY: help deps deps-dev deps-tests deps-hive-tests lock test test-coverage test-hive docker-up run-local-postgres run-local-postgres-json

help:
	@printf "%s\n" "Available targets:"
	@printf "  %-24s %s\n" "make deps" "Install minimal app dependencies"
	@printf "  %-24s %s\n" "make deps-dev" "Install app, Postgres, and test dependencies"
	@printf "  %-24s %s\n" "make deps-tests" "Install app and test dependencies for CI"
	@printf "  %-24s %s\n" "make deps-hive-tests" "Install app, Hive, and test dependencies"
	@printf "  %-24s %s\n" "make lock" "Refresh uv.lock"
	@printf "  %-24s %s\n" "make test" "Run tests with uv"
	@printf "  %-24s %s\n" "make test-coverage" "Run tests with coverage"
	@printf "  %-24s %s\n" "make test-hive" "Run Hive Kerberos integration tests"
	@printf "  %-24s %s\n" "make docker-up" "Start local Postgres and Flyway"
	@printf "  %-24s %s\n" "make run-local-postgres" "Run freshness checks with local Postgres config"
	@printf "  %-24s %s\n" "make run-local-postgres-json" "Run local freshness checks with JSON output"

deps:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv venv --allow-existing --python $(PYTHON_VERSION) $(VENV)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python -r requirements/app.dependencies.txt -r requirements/postgres.dependencies.txt
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python --no-deps -e .

deps-dev:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv venv --allow-existing --python $(PYTHON_VERSION) $(VENV)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python -r requirements/app.dependencies.txt -r requirements/postgres.dependencies.txt -r requirements/test.dependencies.txt
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python --no-deps -e .

deps-tests:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv venv --allow-existing --python $(PYTHON_VERSION) $(VENV)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python -r requirements/app.dependencies.txt -r requirements/test.dependencies.txt
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python --no-deps -e .

deps-hive-tests:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv venv --allow-existing --python $(PYTHON_VERSION) $(VENV)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python -r requirements/app.dependencies.txt -r requirements/hive.dependencies.txt -r requirements/test.dependencies.txt
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip install --python $(BIN)/python --no-deps -e .

lock:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv lock

test:
	$(BIN)/pytest

test-coverage:
	$(BIN)/pytest --cov=gx_freshness --cov-report=term-missing --cov-report=xml --cov-report=html

test-hive:
	$(BIN)/pytest -m hive_integration tests/integration

docker-up:
	docker compose up -d

run-local-postgres:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "Missing $(ENV_FILE). Create it with: cp .env.example $(ENV_FILE)"; \
		exit 2; \
	fi
	set -a; . "$(ENV_SOURCE)"; set +a; $(BIN)/gx-freshness run --config "$(LOCAL_CONFIG)"

run-local-postgres-json:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "Missing $(ENV_FILE). Create it with: cp .env.example $(ENV_FILE)"; \
		exit 2; \
	fi
	set -a; . "$(ENV_SOURCE)"; set +a; $(BIN)/gx-freshness run --config "$(LOCAL_CONFIG)" --json
