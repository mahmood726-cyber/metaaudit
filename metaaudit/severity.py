"""Severity classification and detector result dataclass."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class Severity(enum.IntEnum):
    PASS = 0
    WARN = 1
    FAIL = 2
    CRITICAL = 3

    @classmethod
    def from_string(cls, s: str) -> Severity:
        return cls[s.upper()]


@dataclass
class DetectorResult:
    module: str
    severity: Severity
    detail: str
    metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def insufficient_data(cls, module: str, reason: str) -> DetectorResult:
        return cls(
            module=module,
            severity=Severity.PASS,
            detail=f"Insufficient data: {reason}",
            metrics={"insufficient_data": True},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "severity": self.severity.name,
            "detail": self.detail,
            "metrics": self.metrics,
        }
