from __future__ import annotations

import logging

from gx_freshness.domain.models.freshness_config import FreshnessConfig
from gx_freshness.domain.models.freshness_run_result import FreshnessRunResult
from gx_freshness.domain.ports import FreshnessRepository, ValidationService

logger = logging.getLogger(__name__)


def run_freshness_checks(
    config: FreshnessConfig,
    freshness_repository: FreshnessRepository,
    validation_service: ValidationService,
) -> FreshnessRunResult:
    dataframe = freshness_repository.collect_freshness(config.schemas)

    logger.info("Running Great Expectations validation")
    validation = validation_service.validate(dataframe)
    success = validation.success and bool(dataframe["error"].isna().all())

    if success:
        logger.info("Freshness validation succeeded for %s table(s)", validation.checked_tables)
    else:
        logger.error("Freshness validation failed for %s table(s)", validation.checked_tables)

    return FreshnessRunResult(
        success=success,
        dataframe=dataframe,
        validation=validation,
    )
