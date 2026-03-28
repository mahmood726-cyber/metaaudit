"""Tests for small_study detector (Peters/funnel asymmetry)."""

import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.small_study import detect_small_study


def _make_rma(yi, vi, significant=True):
    k = len(yi)
    yi = np.array(yi, dtype=float)
    vi = np.array(vi, dtype=float)
    w = 1.0 / vi
    est = (w * yi).sum() / w.sum()
    return RecomputedMA(
        k=k,
        yi=yi,
        vi=vi,
        estimate=est,
        se=1.0 / np.sqrt(w.sum()),
        se_hksj=1.0 / np.sqrt(w.sum()),
        ci_lower=est - 0.5,
        ci_upper=est + 0.5,
        p_value=0.01 if significant else 0.5,
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
    """k=3 < 10 — insufficient_data."""
    rma = _make_rma(
        yi=[-0.5, -0.4, -0.6],
        vi=[0.05, 0.04, 0.06],
    )
    result = detect_small_study(rma)
    assert result.metrics.get("insufficient_data") is True


def test_pass_no_correlation():
    """No small-study effect — PASS.

    Studies have varying precision but effect is NOT related to study size;
    big studies and small studies show the same effect.
    """
    # 15 studies: vi varies but yi is sampled symmetrically around -0.5
    # regardless of study size — no small-study pattern
    np.random.seed(7)
    k = 15
    # Vary vi: mix of small and large studies
    vi = np.array([0.01, 0.01, 0.01, 0.01, 0.01,
                   0.05, 0.05, 0.05, 0.05, 0.05,
                   0.10, 0.10, 0.10, 0.10, 0.10])
    # yi close to -0.5 for all, no systematic small-study effect
    yi = np.array([-0.52, -0.48, -0.51, -0.49, -0.50,
                   -0.52, -0.48, -0.51, -0.49, -0.50,
                   -0.52, -0.48, -0.51, -0.49, -0.50])
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_small_study(rma)
    assert result.severity == Severity.PASS
    assert "peters_p" in result.metrics
    assert result.metrics["insufficient_data"] is False


def test_fail_small_larger_pattern():
    """Small studies (large vi) have systematically larger |effects| — FAIL."""
    # Large studies: vi=0.01, effect=-0.3
    # Small studies: vi=0.25, effect=-1.5
    k = 16
    yi = np.array([-0.3] * 8 + [-1.8] * 8)
    vi = np.array([0.01] * 8 + [0.25] * 8)
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_small_study(rma)
    # Should detect asymmetry
    assert result.severity in (Severity.WARN, Severity.FAIL)
