from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationSummary:
    success: bool
    checked_tables: int
    unexpected_count: int
    raw_result: Any
