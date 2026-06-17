from __future__ import annotations

import os

from gx_freshness.domain.models.freshness_config import FreshnessConfig


def resolve_database_url(config: FreshnessConfig, database_url: str | None = None) -> str:
    resolved_url = database_url or os.getenv(config.database_url_env)
    if not resolved_url:
        raise ValueError(
            f"Database URL not provided. Set {config.database_url_env} or pass --database-url."
        )
    return resolved_url
