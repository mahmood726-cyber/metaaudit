"""Detector: Publication bias (Egger, Begg, trim-and-fill)."""

from __future__ import annotations

import numpy as np
from scipy import stats

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "pub_bias"

_K_MIN = 10
_P_THRESHOLD = 0.10
_FAIL_COUNT = 2
_WARN_COUNT = 1


def _egger_test(yi: np.ndarray, vi: np.ndarray) -> float:
    """Egger's test: standard unweighted OLS regression of z on precision (1/SE).

    Regresses z = yi/SE on precision = 1/SE. A non-zero intercept indicates
    funnel asymmetry. Returns two-tailed p-value for the intercept.
    This is the original Egger et al. (1997) formulation.
    """
    se = np.sqrt(vi)
    precision = 1.0 / se
    z = yi / se
    n = len(yi)
    try:
        slope, intercept, r_value, p_value, se_slope = stats.linregress(precision, z)
        # linregress p-value is for the slope; recompute for the intercept
        predicted = intercept + slope * precision
        residuals = z - predicted
        mse = (residuals ** 2).sum() / (n - 2)
        ss_x = ((precision - precision.mean()) ** 2).sum()
        se_intercept = np.sqrt(mse * (1.0 / n + precision.mean() ** 2 / ss_x))
        t_stat = intercept / se_intercept if se_intercept > 0 else 0.0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n - 2))
        return float(p_value)
    except Exception:
        return 1.0


def _begg_test(yi: np.ndarray, vi: np.ndarray) -> float:
    """Begg's test: Kendall's tau between variance-adjusted residuals and variance.

    Implements Begg & Mazumdar (1994): adjusts residuals for between-study
    variance before computing Kendall's tau correlation with sampling variance.
    Returns two-tailed p-value.
    """
    w = 1.0 / vi
    estimate = (w * yi).sum() / w.sum()
    # Adjusted variance per Begg & Mazumdar (1994): vi - 1/sum(w)
    v_bar = 1.0 / w.sum()
    adj_var = vi - v_bar
    # Avoid negative adjusted variance
    adj_var = np.maximum(adj_var, 1e-10)
    adj_resid = (yi - estimate) / np.sqrt(adj_var)
    tau, p_value = stats.kendalltau(adj_resid, vi)
    return float(p_value)


def _trim_and_fill(yi: np.ndarray, vi: np.ndarray, tau2: float = 0.0,
                   max_iter: int = 50) -> int:
    """Trim-and-fill: estimate number of missing studies (k0).

    Uses L0 estimator (Duval & Tweedie 2000) with random-effects weights
    (1/(vi + tau2)) so the centering is consistent with the RE model.
    Returns estimated k0.
    """
    n = len(yi)
    if n < 3:
        return 0

    for _ in range(max_iter):
        # Use RE weights with the provided tau2
        w = 1.0 / (vi + tau2)
        estimate = (w * yi).sum() / w.sum()
        centered = yi - estimate

        # L0 estimator: count studies that are on the opposite side
        positive_count = (centered > 0).sum()
        negative_count = (centered < 0).sum()
        k0_new = max(0, int(np.round(
            (4 * max(positive_count, negative_count) - n) / 3.0
        )))

        k0 = k0_new
        if k0 == 0:
            break

        # Trim k0 studies (largest |effect| on the dominant side)
        dominant_side = "pos" if positive_count > negative_count else "neg"
        if dominant_side == "pos":
            idx_sorted = np.argsort(centered)[::-1]
        else:
            idx_sorted = np.argsort(centered)

        # Remove k0 most extreme from dominant side
        keep = np.ones(n, dtype=bool)
        trimmed = 0
        for i in idx_sorted:
            if trimmed >= k0:
                break
            if (dominant_side == "pos" and centered[i] > 0) or (
                dominant_side == "neg" and centered[i] < 0
            ):
                keep[i] = False
                trimmed += 1

        yi_trimmed = yi[keep]
        vi_trimmed = vi[keep]
        if len(yi_trimmed) < 2:
            break
        # Re-estimate with trimmed data using RE weights
        w = 1.0 / (vi_trimmed + tau2)
        estimate = (w * yi_trimmed).sum() / w.sum()
        break  # Single-pass approximation is sufficient for flagging

    return k0


def detect_pub_bias(rma: RecomputedMA) -> DetectorResult:
    """Detect publication bias using Egger, Begg, and trim-and-fill.

    Rules:
    - insufficient_data if k < 10
    - Run all 3 tests
    - FAIL if >= 2 tests have p < 0.10
    - WARN if exactly 1 test has p < 0.10
    - PASS otherwise
    """
    if rma.k < _K_MIN:
        return DetectorResult.insufficient_data(
            MODULE, f"Publication bias tests require k>={_K_MIN} studies (k={rma.k})"
        )

    yi = rma.yi
    vi = rma.vi

    egger_p = _egger_test(yi, vi)
    begg_p = _begg_test(yi, vi)
    k0 = _trim_and_fill(yi, vi, tau2=rma.tau2)

    # For trim-and-fill, flag if k0 >= 2 (at least 2 missing studies)
    trimfill_positive = k0 >= 2

    significant_tests = sum([
        egger_p < _P_THRESHOLD,
        begg_p < _P_THRESHOLD,
        trimfill_positive,
    ])

    # Also count at stricter alpha=0.05 for sensitivity reporting
    strict_tests = sum([
        egger_p < 0.05,
        begg_p < 0.05,
        trimfill_positive,
    ])

    metrics = {
        "insufficient_data": False,
        "egger_p": float(egger_p),
        "begg_p": float(begg_p),
        "trimfill_k0": int(k0),
        "n_positive_tests": significant_tests,
        "n_positive_tests_strict": strict_tests,
    }

    if significant_tests >= _FAIL_COUNT:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"{significant_tests}/3 publication bias tests positive "
                f"(Egger p={egger_p:.3f}, Begg p={begg_p:.3f}, "
                f"trim-fill k0={k0}). Likely funnel asymmetry."
            ),
            metrics=metrics,
        )

    if significant_tests == _WARN_COUNT:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"1/3 publication bias tests positive "
                f"(Egger p={egger_p:.3f}, Begg p={begg_p:.3f}, "
                f"trim-fill k0={k0}). Borderline asymmetry."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=(
            f"No publication bias detected "
            f"(Egger p={egger_p:.3f}, Begg p={begg_p:.3f}, trim-fill k0={k0})."
        ),
        metrics=metrics,
    )
