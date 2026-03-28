"""Detector: Prediction Interval vs Confidence Interval gap."""

from __future__ import annotations

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "prediction_gap"


def detect_prediction_gap(rma: RecomputedMA) -> DetectorResult:
    """Detect gap between CI (precision) and PI (generalisability).

    Rules:
    - insufficient_data if PI not computable (k<3)
    - PASS if not significant
    - PASS if significant and PI also excludes null
    - FAIL if CI excludes null but PI includes null (opposite_extent <= 0.1)
    - CRITICAL if PI extends substantially (>0.1) into the opposite direction
    """
    if not rma.pi_computable:
        return DetectorResult.insufficient_data(MODULE, "PI requires k>=3 studies")

    if not rma.significant:
        return DetectorResult(
            module=MODULE,
            severity=Severity.PASS,
            detail="Not significant; PI vs CI gap not applicable.",
            metrics={"insufficient_data": False},
        )

    estimate = rma.estimate
    # Determine null direction
    ci_excludes_null = (rma.ci_lower > 0 and rma.ci_upper > 0) or (
        rma.ci_lower < 0 and rma.ci_upper < 0
    )

    if not ci_excludes_null:
        return DetectorResult(
            module=MODULE,
            severity=Severity.PASS,
            detail="CI does not exclude null; PI gap not relevant.",
            metrics={"insufficient_data": False},
        )

    # CI excludes null — check PI
    if estimate > 0:
        # Positive direction: does PI go negative?
        opposite_extent = max(0.0, -rma.pi_lower)
        pi_includes_null = rma.pi_lower <= 0
    else:
        # Negative direction: does PI go positive?
        opposite_extent = max(0.0, rma.pi_upper)
        pi_includes_null = rma.pi_upper >= 0

    metrics = {
        "insufficient_data": False,
        "ci_lower": rma.ci_lower,
        "ci_upper": rma.ci_upper,
        "pi_lower": rma.pi_lower,
        "pi_upper": rma.pi_upper,
        "opposite_extent": opposite_extent,
    }

    if not pi_includes_null:
        return DetectorResult(
            module=MODULE,
            severity=Severity.PASS,
            detail="Both CI and PI exclude the null — effect likely generalisable.",
            metrics=metrics,
        )

    if opposite_extent > 0.1:
        return DetectorResult(
            module=MODULE,
            severity=Severity.CRITICAL,
            detail=(
                f"PI extends {opposite_extent:.3f} units into opposite direction. "
                "Effect may reverse in some settings."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.FAIL,
        detail=(
            f"CI excludes null but PI includes it "
            f"(PI [{rma.pi_lower:.3f}, {rma.pi_upper:.3f}]). "
            "Substantial between-study heterogeneity limits generalisability."
        ),
        metrics=metrics,
    )
