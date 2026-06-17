from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from gx_freshness.adapters.inbound.config import load_config
from gx_freshness.adapters.outbound.database import SqlFreshnessRepository
from gx_freshness.adapters.outbound.great_expectations import GreatExpectationsValidationService
from gx_freshness.adapters.outbound.logging import LoggingConfigurator
from gx_freshness.adapters.outbound.output import FreshnessResultRenderer
from gx_freshness.application import run_freshness_checks
from gx_freshness.adapters.inbound.cli.database_url_resolver import resolve_database_url

logger = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    LoggingConfigurator().configure(args.log_level)

    if args.command == "run":
        return _run(args)

    parser.print_help()
    return 2


def _run(args: argparse.Namespace) -> int:
    logger.info("Loading config from %s", args.config)
    try:
        config = load_config(args.config)
    except Exception as exc:
        logger.error("Failed to load config from %s: %s", args.config, exc)
        logger.debug("Config loading traceback", exc_info=True)
        return 2

    try:
        database_url = resolve_database_url(config, args.database_url)
        result = run_freshness_checks(
            config,
            freshness_repository=SqlFreshnessRepository(database_url),
            validation_service=GreatExpectationsValidationService(),
        )
    except ValueError as exc:
        logger.error("%s", exc)
        logger.debug("Freshness configuration traceback", exc_info=True)
        return 2
    except Exception as exc:
        logger.error("Freshness execution failed: %s", exc)
        logger.debug("Freshness execution traceback", exc_info=True)
        return 1

    FreshnessResultRenderer().render(result, json_output=args.json)

    return 0 if result.success else 1


def _build_parser() -> argparse.ArgumentParser:
    log_parser = argparse.ArgumentParser(add_help=False)
    log_parser.add_argument(
        "--log-level",
        default=None,
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Set log verbosity. Overrides GX_FRESHNESS_LOG_LEVEL.",
    )

    parser = argparse.ArgumentParser(prog="gx-freshness")
    parser.set_defaults(log_level=None)
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser(
        "run",
        help="Run YAML-driven freshness checks.",
        parents=[log_parser],
    )
    run.add_argument("--config", required=True, type=Path, help="Path to freshness YAML.")
    run.add_argument("--database-url", help="SQLAlchemy database URL. Overrides database_url_env.")
    run.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
