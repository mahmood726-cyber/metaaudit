"""Detector: Overclaiming (effect size vs MCID)."""

from __future__ import annotations

import math

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "overclaiming"

# Minimum clinically important differences by measure
_MCID = {
    "logOR": math.log(1.25),   # log(1.25) ≈ 0.223
    "logRR": math.log(1.25),   # same threshold
    "OR": 1.25,
    "RR": 1.25,
    "SMD": 0.2,                # Cohen's d small effect
    "MD": None,                # MD is outcome-specific; use generic
}
_MCID_GENERIC = 0.1

_TRIVIAL_FRACTION = 0.50  # |effect| < 50% of MCID → trivial (FAIL)


def _get_mcid(measure: str) -> float:
    """Return MCID for a given measure, or generic fallback."""
    mcid = _MCID.get(measure)
    if mcid is None:
        return _MCID_GENERIC
    return mcid


def detect_overclaiming(rma: RecomputedMA) -> DetectorResult:
    """Detect claims of statistical significance for trivially small effects.

    Rules:
    - PASS if not significant
    - FAIL if |effect| < 50% of MCID (trivial)
    - WARN if |effect| < MCID (below minimal clinical importance)
    - PASS if |effect| >= MCID
    """
    if not rma.significant:
        return DetectorResult(
            module=MODULE,
            severity=Severity.PASS,
            detail="Not significant; overclaiming check not applicable.",
            metrics={"insufficient_data": False},
        )

    mcid = _get_mcid(rma.measure)
    effect_abs = abs(rma.estimate)
    fraction_of_mcid = effect_abs / mcid if mcid > 0 else float("inf")

    metrics = {
        "insufficient_data": False,
        "effect_abs": float(effect_abs),
        "mcid": float(mcid),
        "fraction_of_mcid": float(fraction_of_mcid),
        "measure": rma.measure,
    }

    if fraction_of_mcid < _TRIVIAL_FRACTION:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"Effect ({rma.measure}={rma.estimate:.3f}, |effect|={effect_abs:.3f}) "
                f"is only {fraction_of_mcid:.0%} of the MCID ({mcid:.3f}). "
                "Statistically significant but clinically trivial."
            ),
            metrics=metrics,
        )

    if fraction_of_mcid < 1.0:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"Effect ({rma.measure}={rma.estimate:.3f}) is below MCID ({mcid:.3f}). "
                f"|effect|={effect_abs:.3f} = {fraction_of_mcid:.0%} of MCID. "
                "Clinical importance uncertain."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=(
            f"Effect ({rma.measure}={rma.estimate:.3f}) exceeds MCID ({mcid:.3f}). "
            f"|effect|={effect_abs:.3f} = {fraction_of_mcid:.0%} of MCID."
        ),
        metrics=metrics,
    )
