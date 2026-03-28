"""Detector: GRADE certainty vs automated severity mismatch."""

from __future__ import annotations

from typing import Optional

from metaaudit.severity import DetectorResult, Severity

MODULE = "certainty_mismatch"

# GRADE levels where mismatch is meaningful (authors claimed quality)
_HIGH_QUALITY_GRADES = {"high"}
_MODERATE_QUALITY_GRADES = {"moderate"}
_DISCOUNTED_GRADES = {"low", "very low", "very-low", "verylow"}

# Thresholds: number of FAIL results that trigger each alarm per GRADE level
_HIGH_CRITICAL_FAILS = 3    # High + 3 FAILs → CRITICAL
_HIGH_WARN_FAILS = 2        # High + 2 FAILs → WARN
_MODERATE_FAIL_FAILS = 4    # Moderate + 4 FAILs → FAIL


def detect_certainty_mismatch(
    grade_certainty: Optional[str],
    other_results: list[DetectorResult],
) -> DetectorResult:
    """Detect mismatch between claimed GRADE certainty and automated flaws.

    Rules:
    - insufficient_data if grade_certainty is None
    - PASS for Low/Very low regardless (already discounted)
    - CRITICAL if High + >= 3 FAILs
    - WARN if High + >= 2 FAILs
    - FAIL if Moderate + >= 4 FAILs
    - PASS otherwise
    """
    if grade_certainty is None:
        return DetectorResult.insufficient_data(MODULE, "No GRADE certainty rating provided")

    grade_norm = grade_certainty.lower().strip()

    # Count fails (and criticals count as fails)
    n_fails = sum(
        1 for r in other_results
        if r.severity in (Severity.FAIL, Severity.CRITICAL)
        and not r.metrics.get("insufficient_data", False)
    )

    metrics = {
        "insufficient_data": False,
        "grade_certainty": grade_certainty,
        "n_fails": n_fails,
        "n_results": len(other_results),
    }

    # Low/Very low: authors already discounted quality — mismatch not meaningful
    if grade_norm in _DISCOUNTED_GRADES:
        return DetectorResult(
            module=MODULE,
            severity=Severity.PASS,
            detail=(
                f"GRADE certainty is '{grade_certainty}' — "
                "quality limitations already acknowledged."
            ),
            metrics=metrics,
        )

    is_high = grade_norm in _HIGH_QUALITY_GRADES
    is_moderate = grade_norm in _MODERATE_QUALITY_GRADES

    if is_high:
        if n_fails >= _HIGH_CRITICAL_FAILS:
            return DetectorResult(
                module=MODULE,
                severity=Severity.CRITICAL,
                detail=(
                    f"High GRADE certainty claimed but {n_fails} FAIL-level flaws detected. "
                    "Severe overclaiming of evidence quality."
                ),
                metrics=metrics,
            )
        if n_fails >= _HIGH_WARN_FAILS:
            return DetectorResult(
                module=MODULE,
                severity=Severity.WARN,
                detail=(
                    f"High GRADE certainty claimed but {n_fails} FAIL-level flaws detected. "
                    "Quality rating may be overestimated."
                ),
                metrics=metrics,
            )

    if is_moderate and n_fails >= _MODERATE_FAIL_FAILS:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"Moderate GRADE certainty claimed but {n_fails} FAIL-level flaws detected. "
                "Certainty should likely be downgraded."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=(
            f"GRADE certainty '{grade_certainty}' is consistent "
            f"with {n_fails} automated FAIL(s) detected."
        ),
        metrics=metrics,
    )
