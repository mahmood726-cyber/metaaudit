"""Detector: Excess significance (Ioannidis-Trikalinos test)."""

from __future__ import annotations

import numpy as np
from scipy import stats

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "excess_sig"

_K_MIN = 5
_OE_FAIL_THRESHOLD = 1.5
_P_FAIL_THRESHOLD = 0.10


def _power_study(effect: float, vi: float, alpha: float = 0.05) -> float:
    """Power to detect `effect` in a single study with sampling variance vi.

    Assumes two-tailed test, large-sample z approximation.
    """
    se = np.sqrt(vi)
    z_crit = stats.norm.ppf(1 - alpha / 2)  # 1.96 for alpha=0.05
    # Non-centrality parameter
    ncp = abs(effect) / se
    power = 1 - stats.norm.cdf(z_crit - ncp) + stats.norm.cdf(-z_crit - ncp)
    return float(power)


def detect_excess_sig(rma: RecomputedMA) -> DetectorResult:
    """Ioannidis-Trikalinos excess significance test.

    For each study, compute power to detect the pooled effect.
    Compare observed vs expected number of significant studies.
    FAIL if O/E > 1.5 AND binomial p < 0.10.

    Rules:
    - insufficient_data if k < 5
    """
    if rma.k < _K_MIN:
        return DetectorResult.insufficient_data(
            MODULE, f"Excess significance test requires k>={_K_MIN} studies (k={rma.k})"
        )

    yi = rma.yi
    vi = rma.vi
    k = rma.k
    pooled_effect = rma.estimate

    # Compute per-study power based on pooled effect
    powers = np.array([_power_study(pooled_effect, v) for v in vi])
    exp_sig = float(powers.sum())

    # Count observed significant studies (two-tailed p < 0.05)
    z_scores = np.abs(yi / np.sqrt(vi))
    obs_sig_mask = z_scores >= stats.norm.ppf(0.975)
    obs_sig = int(obs_sig_mask.sum())

    oe_ratio = obs_sig / max(exp_sig, 0.001)

    # Binomial test: H0 = each study has power probability of being significant
    # Use average power as the null probability
    avg_power = exp_sig / k
    avg_power = np.clip(avg_power, 1e-6, 1 - 1e-6)

    try:
        binom_result = stats.binomtest(obs_sig, k, avg_power, alternative="greater")
        p_excess = float(binom_result.pvalue)
    except Exception:
        p_excess = 1.0

    metrics = {
        "insufficient_data": False,
        "obs_sig": obs_sig,
        "exp_sig": float(exp_sig),
        "oe_ratio": float(oe_ratio),
        "p_excess": float(p_excess),
        "k": k,
    }

    if oe_ratio > _OE_FAIL_THRESHOLD and p_excess < _P_FAIL_THRESHOLD:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"Excess significance: {obs_sig} observed vs {exp_sig:.1f} expected "
                f"(O/E={oe_ratio:.2f}, p={p_excess:.3f}). "
                "Likely selective reporting or outcome reporting bias."
            ),
            metrics=metrics,
        )

    if oe_ratio > _OE_FAIL_THRESHOLD:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"Possible excess significance: {obs_sig} observed vs {exp_sig:.1f} expected "
                f"(O/E={oe_ratio:.2f}, p={p_excess:.3f})."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=(
            f"Observed significant studies ({obs_sig}) consistent with expected ({exp_sig:.1f})."
        ),
        metrics=metrics,
    )
