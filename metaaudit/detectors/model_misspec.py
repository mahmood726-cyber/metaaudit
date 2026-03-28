"""Detector: Model misspecification (FE/RE appropriateness)."""

from __future__ import annotations

from typing import Any

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "model_misspec"

_I2_FAIL_THRESHOLD = 50.0
_EVENT_RATE_WARN_THRESHOLD = 0.20


def detect_model_misspec(
    rma: RecomputedMA, context: dict[str, Any] | None = None
) -> DetectorResult:
    """Detect model misspecification issues.

    Rules:
    - insufficient_data if k<2
    - FAIL if I2 > 50% (substantial heterogeneity makes FE inappropriate)
    - WARN if OR/RR measure used with event_rate > 0.20 (common outcome)
    - PASS otherwise
    """
    if context is None:
        context = {}

    if rma.k < 2:
        return DetectorResult.insufficient_data(MODULE, "k<2 — heterogeneity not estimable")

    metrics: dict[str, Any] = {
        "insufficient_data": False,
        "I2": rma.I2,
        "k": rma.k,
        "measure": rma.measure,
    }

    event_rate = context.get("event_rate")
    if event_rate is not None:
        metrics["event_rate"] = event_rate

    # FAIL check: high heterogeneity
    if rma.I2 > _I2_FAIL_THRESHOLD:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"I² = {rma.I2:.1f}% exceeds 50% threshold. "
                "Random-effects model required; fixed-effect pooling is inappropriate."
            ),
            metrics=metrics,
        )

    # WARN check: OR/RR with common outcome
    is_ratio_measure = rma.measure in ("logOR", "logRR", "OR", "RR")
    if is_ratio_measure and event_rate is not None and event_rate > _EVENT_RATE_WARN_THRESHOLD:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"Odds/risk ratio used with event rate {event_rate:.0%} > 20%. "
                "OR overestimates RR for common outcomes; consider risk ratio or risk difference."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=f"I² = {rma.I2:.1f}% — no model misspecification detected.",
        metrics=metrics,
    )
