UV_CACHE_DIR ?= .uv-cache
LOCAL_CONFIG ?= configs/freshness.local-postgres.yml
ENV_FILE ?= .env
ENV_SOURCE := $(if $(findstring /,$(ENV_FILE)),$(ENV_FILE),./$(ENV_FILE))

.DEFAULT_GOAL := help

.PHONY: help deps lock test docker-up run-local-postgres run-local-postgres-json

help:
	@printf "%s\n" "Available targets:"
	@printf "  %-24s %s\n" "make deps" "Install locked dependencies with uv"
	@printf "  %-24s %s\n" "make lock" "Refresh uv.lock and requirements.txt"
	@printf "  %-24s %s\n" "make test" "Run tests with uv"
	@printf "  %-24s %s\n" "make docker-up" "Start local Postgres and Flyway"
	@printf "  %-24s %s\n" "make run-local-postgres" "Run freshness checks with local Postgres config"
	@printf "  %-24s %s\n" "make run-local-postgres-json" "Run local freshness checks with JSON output"

deps:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --extra postgres --group dev

lock:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv lock
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv pip compile pyproject.toml --extra postgres --group dev --output-file requirements.txt

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pytest

docker-up:
	docker compose up -d

run-local-postgres:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "Missing $(ENV_FILE). Create it with: cp .env.example $(ENV_FILE)"; \
		exit 2; \
	fi
	set -a; . "$(ENV_SOURCE)"; set +a; UV_CACHE_DIR=$(UV_CACHE_DIR) uv run gx-freshness run --config "$(LOCAL_CONFIG)"

run-local-postgres-json:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "Missing $(ENV_FILE). Create it with: cp .env.example $(ENV_FILE)"; \
		exit 2; \
	fi
	set -a; . "$(ENV_SOURCE)"; set +a; UV_CACHE_DIR=$(UV_CACHE_DIR) uv run gx-freshness run --config "$(LOCAL_CONFIG)" --json
