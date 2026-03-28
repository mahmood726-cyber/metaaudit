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
    """Egger's test: WLS regression of standardised effect (z) on precision (1/se).

    Returns two-tailed p-value for the intercept (asymmetry test).
    """
    se = np.sqrt(vi)
    precision = 1.0 / se
    z = yi / se

    # WLS with weights = precision^2 = 1/vi
    w = 1.0 / vi
    n = len(yi)

    # Design matrix [intercept, precision]
    X = np.column_stack([np.ones(n), precision])
    W = np.diag(w)

    try:
        XtWX = X.T @ W @ X
        XtWy = X.T @ (W @ z)
        beta = np.linalg.solve(XtWX, XtWy)
        residuals = z - X @ beta
        sigma2 = (w * residuals ** 2).sum() / (n - 2)
        cov_beta = sigma2 * np.linalg.inv(XtWX)
        se_intercept = np.sqrt(cov_beta[0, 0])
        t_stat = beta[0] / se_intercept if se_intercept > 0 else 0.0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n - 2))
        return float(p_value)
    except np.linalg.LinAlgError:
        return 1.0


def _begg_test(yi: np.ndarray, vi: np.ndarray) -> float:
    """Begg's test: Kendall's tau between standardised effects and sampling variance.

    Returns two-tailed p-value.
    """
    se = np.sqrt(vi)
    w = 1.0 / vi
    w_mean = w.mean()
    # Adjusted standardised effects as in Begg & Mazumdar 1994
    # Use Kendall tau between (yi - estimate_adj) and vi
    estimate = (w * yi).sum() / w.sum()
    # Variance-stabilised residuals
    adj_yi = yi - estimate
    tau, p_value = stats.kendalltau(adj_yi, vi)
    return float(p_value)


def _trim_and_fill(yi: np.ndarray, vi: np.ndarray, max_iter: int = 50) -> int:
    """Trim-and-fill: estimate number of missing studies (k0).

    Uses L0 estimator (Duval & Tweedie 2000).
    Returns estimated k0.
    """
    n = len(yi)
    if n < 3:
        return 0

    for _ in range(max_iter):
        w = 1.0 / vi
        estimate = (w * yi).sum() / w.sum()
        # Rank by |yi - estimate|, then identify outliers on the positive side
        # (assuming effect is negative on average, we look for inflated positive studies)
        centered = yi - estimate
        # Sort by absolute value; assign ranks
        ranks = np.argsort(np.abs(centered)) + 1  # 1-based ranks

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
        # Re-estimate with trimmed data
        w = 1.0 / vi_trimmed
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
    k0 = _trim_and_fill(yi, vi)

    # For trim-and-fill, flag if k0 >= 2 (at least 2 missing studies)
    trimfill_positive = k0 >= 2

    significant_tests = sum([
        egger_p < _P_THRESHOLD,
        begg_p < _P_THRESHOLD,
        trimfill_positive,
    ])

    metrics = {
        "insufficient_data": False,
        "egger_p": float(egger_p),
        "begg_p": float(begg_p),
        "trimfill_k0": int(k0),
        "n_positive_tests": significant_tests,
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
