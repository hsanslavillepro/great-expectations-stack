from __future__ import annotations

import logging
import os
import sys


class LoggingConfigurator:
    env_var = "GX_FRESHNESS_LOG_LEVEL"
    default_level = "INFO"
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def __init__(self, app_logger_name: str = "gx_freshness") -> None:
        self.app_logger_name = app_logger_name

    def configure(self, log_level: str | None = None) -> None:
        resolved_level = self.resolve_level(log_level)
        logging.basicConfig(
            level=logging.WARNING,
            format="%(levelname)s %(name)s - %(message)s",
            stream=sys.stderr,
            force=True,
        )
        logging.getLogger(self.app_logger_name).setLevel(getattr(logging, resolved_level))
        self._quiet_great_expectations()

    def resolve_level(self, log_level: str | None = None) -> str:
        raw_level = log_level or os.getenv(self.env_var) or self.default_level
        resolved_level = raw_level.upper()
        if resolved_level not in self.valid_levels:
            raise ValueError(
                f"Invalid log level {raw_level!r}. Use one of: {', '.join(sorted(self.valid_levels))}."
            )
        return resolved_level

    def _quiet_great_expectations(self) -> None:
        gx_logger = logging.getLogger("great_expectations")
        gx_logger.handlers = [logging.NullHandler()]
        gx_logger.propagate = False
