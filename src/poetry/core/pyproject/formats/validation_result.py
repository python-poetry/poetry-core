from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
