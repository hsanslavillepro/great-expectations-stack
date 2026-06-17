import logging

import pytest

from gx_freshness.adapters.outbound.logging import LoggingConfigurator


def test_logging_configurator_sets_app_logger_level() -> None:
    LoggingConfigurator().configure("DEBUG")

    assert logging.getLogger("gx_freshness").level == logging.DEBUG
    assert logging.getLogger("great_expectations").propagate is False


def test_logging_configurator_uses_env_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GX_FRESHNESS_LOG_LEVEL", "ERROR")

    LoggingConfigurator().configure()

    assert logging.getLogger("gx_freshness").level == logging.ERROR


def test_logging_configurator_prefers_explicit_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GX_FRESHNESS_LOG_LEVEL", "ERROR")

    LoggingConfigurator().configure("DEBUG")

    assert logging.getLogger("gx_freshness").level == logging.DEBUG


def test_logging_configurator_rejects_invalid_env_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GX_FRESHNESS_LOG_LEVEL", "LOUD")

    with pytest.raises(ValueError, match="Invalid log level"):
        LoggingConfigurator().configure()
