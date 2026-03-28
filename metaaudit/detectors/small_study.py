"""Detector: Small-study effects (Peters' test + Spearman correlation)."""

from __future__ import annotations

import numpy as np
from scipy import stats

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "small_study"

_K_MIN = 10
_P_THRESHOLD = 0.10
_SPEARMAN_THRESHOLD = 0.40


def _egger_precision_test(yi: np.ndarray, vi: np.ndarray) -> float:
    """Regression of effect on precision (1/SE). Variant of Egger's test.

    OLS regression of yi on 1/SE. A significant slope indicates that
    larger-precision (bigger) studies have systematically different effects
    from smaller-precision studies — a small-study effect pattern.
    Returns two-tailed p-value for the slope coefficient.
    Uses scipy linregress for numerical stability.

    Note: True Peters' test (Peters et al. 2006) regresses on 1/N, which
    requires study N not available in this context. This precision-based
    variant is used instead.
    """
    precision = 1.0 / np.sqrt(vi)   # 1/SE: larger for big studies
    try:
        slope, intercept, r_value, p_value, se_slope = stats.linregress(precision, yi)
        return float(p_value)
    except Exception:
        return 1.0


def _spearman_abs_effect_vs_variance(yi: np.ndarray, vi: np.ndarray) -> tuple[float, float]:
    """Spearman correlation between |effect| and variance.

    Returns (rho, p_value). Positive rho indicates small studies (high vi)
    have larger absolute effects — classic small-study pattern.
    """
    rho, p_value = stats.spearmanr(np.abs(yi), vi)
    return float(rho), float(p_value)


def detect_small_study(rma: RecomputedMA) -> DetectorResult:
    """Detect small-study effects using precision-regression test and Spearman correlation.

    Rules:
    - insufficient_data if k < 10
    - FAIL if precision-regression p < 0.10 AND Spearman rho > 0.40 AND small studies larger
    - WARN if either precision-regression or Spearman indicates asymmetry
    - PASS otherwise
    """
    if rma.k < _K_MIN:
        return DetectorResult.insufficient_data(
            MODULE, f"Small-study tests require k>={_K_MIN} studies (k={rma.k})"
        )

    yi = rma.yi
    vi = rma.vi

    precision_p = _egger_precision_test(yi, vi)
    spearman_rho, spearman_p = _spearman_abs_effect_vs_variance(yi, vi)

    # Guard against NaN (e.g. constant input)
    if not np.isfinite(spearman_rho):
        spearman_rho = 0.0
    if not np.isfinite(spearman_p):
        spearman_p = 1.0
    if not np.isfinite(precision_p):
        precision_p = 1.0

    # "Small studies larger" means high vi (small studies) correlate with large |effect|
    small_studies_larger = spearman_rho > 0

    metrics = {
        "insufficient_data": False,
        "peters_p": float(precision_p),  # keep key name for backward compat
        "spearman_rho": float(spearman_rho),
        "spearman_p": float(spearman_p),
        "small_studies_larger": small_studies_larger,
    }

    precision_positive = precision_p < _P_THRESHOLD
    spearman_positive = (spearman_p < _P_THRESHOLD) and small_studies_larger

    if precision_positive and spearman_rho > _SPEARMAN_THRESHOLD:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"Strong small-study effect: precision-regression p={precision_p:.3f}, "
                f"Spearman rho={spearman_rho:.3f}. "
                "Small studies show larger effects — possible reporting/publication bias."
            ),
            metrics=metrics,
        )

    if precision_positive or spearman_positive:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"Possible small-study effect: precision-regression p={precision_p:.3f}, "
                f"Spearman rho={spearman_rho:.3f}. Consider funnel plot."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=(
            f"No small-study effect detected "
            f"(precision-regression p={precision_p:.3f}, Spearman rho={spearman_rho:.3f})."
        ),
        metrics=metrics,
    )
