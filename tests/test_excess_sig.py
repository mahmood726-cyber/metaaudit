"""Tests for excess_sig detector (Ioannidis-Trikalinos)."""

import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.excess_sig import detect_excess_sig


def _make_rma(yi, vi, significant=True):
    k = len(yi)
    yi = np.array(yi, dtype=float)
    vi = np.array(vi, dtype=float)
    w = 1.0 / vi
    est = (w * yi).sum() / w.sum()
    p_val = 0.01 if significant else 0.5
    return RecomputedMA(
        k=k,
        yi=yi,
        vi=vi,
        estimate=est,
        se=1.0 / np.sqrt(w.sum()),
        se_hksj=1.0 / np.sqrt(w.sum()),
        ci_lower=est - 0.5,
        ci_upper=est + 0.5,
        p_value=p_val,
        tau2=0.0,
        I2=0.0,
        Q=float(k),
        significant=significant,
        pi_lower=est - 1.0,
        pi_upper=est + 1.0,
        pi_computable=k >= 3,
        data_type=DataType.BINARY,
        measure="logOR",
    )


def test_insufficient_data_k3():
    """k=3 < 5 — insufficient_data."""
    rma = _make_rma(
        yi=[-0.5, -0.4, -0.6],
        vi=[0.05, 0.04, 0.06],
    )
    result = detect_excess_sig(rma)
    assert result.metrics.get("insufficient_data") is True


def test_pass_expected_matches_observed():
    """Expected ≈ observed significant studies — PASS."""
    # 10 studies, moderate effect, all have high power => most significant
    # With effect=-1.0 and vi=0.04, z = 1.0/0.2 = 5.0 for each study => all significant
    # O/E should be close to 1
    k = 10
    yi = np.array([-1.0] * k)
    vi = np.array([0.04] * k)  # se=0.2 => z=5 => all significant
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_excess_sig(rma)
    assert result.severity == Severity.PASS
    assert "obs_sig" in result.metrics
    assert "exp_sig" in result.metrics


def test_fail_too_many_significant():
    """Many more significant studies than expected — WARN or FAIL.

    All 10 studies are individually significant (z>1.96) but the pooled
    effect size implies only ~50% power per study. O/E = 10/5.16 ~ 1.94.
    """
    k = 10
    # yi=-2.0, vi=1.0 => z=2.0 => each individually significant
    # Pooled effect = -2.0, power per study ~ 0.52 => exp ~ 5.2
    # O/E ~ 1.94 > 1.5 and binomial p ~ 0.001 => FAIL
    yi = np.array([-2.0] * k)
    vi = np.array([1.0] * k)
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_excess_sig(rma)
    assert result.severity in (Severity.WARN, Severity.FAIL)
    assert result.metrics["obs_sig"] == k
    assert result.metrics["oe_ratio"] > 1.5


def test_metrics_present():
    """Metrics include obs_sig, exp_sig, ratio, p_excess."""
    k = 8
    yi = np.array([-0.5] * k)
    vi = np.array([0.04] * k)
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_excess_sig(rma)
    assert "obs_sig" in result.metrics
    assert "exp_sig" in result.metrics
    assert "oe_ratio" in result.metrics
    assert "p_excess" in result.metrics
    assert result.metrics["insufficient_data"] is False
