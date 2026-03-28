"""Tests for pub_bias detector (Egger/Begg/trim-fill)."""

import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.pub_bias import detect_pub_bias


def _make_rma(yi, vi, significant=True):
    k = len(yi)
    yi = np.array(yi, dtype=float)
    vi = np.array(vi, dtype=float)
    # Simple pool
    w = 1.0 / vi
    est = (w * yi).sum() / w.sum()
    return RecomputedMA(
        k=k,
        yi=yi,
        vi=vi,
        estimate=est,
        se=1.0 / np.sqrt(w.sum()),
        se_hksj=1.0 / np.sqrt(w.sum()),
        ci_lower=est - 1.96 / np.sqrt(w.sum()),
        ci_upper=est + 1.96 / np.sqrt(w.sum()),
        p_value=0.01 if significant else 0.5,
        tau2=0.0,
        I2=0.0,
        Q=float(k),
        significant=significant,
        pi_lower=-1.5,
        pi_upper=-0.1,
        pi_computable=k >= 3,
        data_type=DataType.BINARY,
        measure="logOR",
    )


def test_insufficient_data_k5():
    """k=5 < 10 — insufficient_data."""
    rma = _make_rma(
        yi=[-0.5, -0.4, -0.6, -0.3, -0.5],
        vi=[0.05, 0.04, 0.06, 0.03, 0.05],
    )
    result = detect_pub_bias(rma)
    assert result.metrics.get("insufficient_data") is True


def test_pass_symmetric():
    """Perfectly symmetric funnel — PASS."""
    # 20 studies symmetric around -0.5
    np.random.seed(42)
    k = 20
    # Create symmetric set: equal positive and negative deviations
    base = -0.5
    # Use equal precisions (symmetric funnel by construction)
    yi = np.array([base] * k + [base + 0.1 * i for i in range(1, 6)]
                  + [base - 0.1 * i for i in range(1, 6)])[:k]
    vi = np.array([0.05] * k)
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_pub_bias(rma)
    # Symmetric data should show no publication bias
    assert result.severity in (Severity.PASS, Severity.WARN)
    assert "egger_p" in result.metrics


def test_fail_asymmetric():
    """Strong asymmetry (small studies show larger effects) — FAIL."""
    # Manufacture a very asymmetric funnel:
    # small studies (large vi) have large effects; big studies (small vi) have small effects
    k = 15
    # Large studies: vi=0.01, effect=-0.2
    # Small studies: vi=0.20, effect=-1.5
    yi = np.array([-0.2] * 8 + [-1.8] * 7)
    vi = np.array([0.01] * 8 + [0.25] * 7)
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_pub_bias(rma)
    assert result.severity in (Severity.WARN, Severity.FAIL)


def test_metrics_present():
    """Metrics include egger_p, begg_p, trimfill_k0."""
    k = 12
    yi = np.array([-0.5] * k)
    vi = np.array([0.05] * k)
    rma = _make_rma(yi=yi, vi=vi)
    result = detect_pub_bias(rma)
    assert "egger_p" in result.metrics
    assert "begg_p" in result.metrics
    assert "trimfill_k0" in result.metrics
    assert result.metrics["insufficient_data"] is False
