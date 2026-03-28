"""Tests for model_misspec detector."""

import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.model_misspec import detect_model_misspec


def _make_rma(I2, k=10, significant=True, measure="logOR", data_type=DataType.BINARY):
    yi = np.zeros(k)
    vi = np.ones(k) * 0.01
    return RecomputedMA(
        k=k,
        yi=yi,
        vi=vi,
        estimate=-0.5,
        se=0.1,
        se_hksj=0.1,
        ci_lower=-0.7,
        ci_upper=-0.3,
        p_value=0.01 if significant else 0.5,
        tau2=0.1,
        I2=I2,
        Q=float(k),
        significant=significant,
        pi_lower=-1.0,
        pi_upper=0.0,
        pi_computable=True,
        data_type=data_type,
        measure=measure,
    )


def test_pass_low_heterogeneity():
    """I2=20% — PASS."""
    rma = _make_rma(I2=20.0)
    result = detect_model_misspec(rma, context={})
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_fail_high_heterogeneity():
    """I2=75% — FAIL."""
    rma = _make_rma(I2=75.0)
    result = detect_model_misspec(rma, context={})
    assert result.severity == Severity.FAIL
    assert result.metrics["I2"] == pytest.approx(75.0)


def test_warn_or_common_outcome():
    """OR with high event rate (>0.20) — WARN."""
    rma = _make_rma(I2=20.0, measure="logOR")
    result = detect_model_misspec(rma, context={"event_rate": 0.35})
    assert result.severity == Severity.WARN


def test_pass_or_rare_outcome():
    """OR with rare event rate (<0.20) — PASS."""
    rma = _make_rma(I2=20.0, measure="logOR")
    result = detect_model_misspec(rma, context={"event_rate": 0.10})
    assert result.severity == Severity.PASS


def test_insufficient_data_k1():
    """k=1 — insufficient_data."""
    rma = _make_rma(I2=0.0, k=1, significant=False)
    result = detect_model_misspec(rma, context={})
    assert result.metrics.get("insufficient_data") is True


def test_fail_trumps_warn():
    """High I2 AND common outcome — FAIL (not just WARN)."""
    rma = _make_rma(I2=65.0, measure="logOR")
    result = detect_model_misspec(rma, context={"event_rate": 0.30})
    assert result.severity == Severity.FAIL
