"""Tests for prediction_gap detector."""

import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.prediction_gap import detect_prediction_gap


def _make_rma(estimate, ci_lower, ci_upper, pi_lower, pi_upper,
              pi_computable=True, significant=True, k=10):
    """Helper to build a minimal RecomputedMA."""
    return RecomputedMA(
        k=k,
        yi=np.array([estimate] * k),
        vi=np.array([0.01] * k),
        estimate=estimate,
        se=0.1,
        se_hksj=0.1,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=0.01 if significant else 0.5,
        tau2=0.05,
        I2=30.0,
        Q=10.0,
        significant=significant,
        pi_lower=pi_lower,
        pi_upper=pi_upper,
        pi_computable=pi_computable,
        data_type=DataType.BINARY,
        measure="logOR",
    )


def test_pass_both_exclude_null():
    """CI and PI both exclude null — PASS."""
    rma = _make_rma(
        estimate=-0.5,
        ci_lower=-0.8, ci_upper=-0.2,
        pi_lower=-1.0, pi_upper=-0.1,
    )
    result = detect_prediction_gap(rma)
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_fail_ci_excludes_pi_includes():
    """CI excludes null but PI just crosses null (small opposite extent) — FAIL."""
    rma = _make_rma(
        estimate=-0.5,
        ci_lower=-0.9, ci_upper=-0.1,
        pi_lower=-1.2, pi_upper=0.05,  # crosses null but opposite_extent <= 0.1
    )
    result = detect_prediction_gap(rma)
    assert result.severity == Severity.FAIL


def test_critical_pi_opposite_direction():
    """PI extends substantially into opposite direction — CRITICAL."""
    rma = _make_rma(
        estimate=-0.5,
        ci_lower=-0.9, ci_upper=-0.1,
        pi_lower=-1.2, pi_upper=0.8,  # 0.8 > 0.1 threshold into positive direction
    )
    result = detect_prediction_gap(rma)
    assert result.severity == Severity.CRITICAL


def test_pass_not_significant():
    """Not significant — PASS regardless of PI."""
    rma = _make_rma(
        estimate=-0.1,
        ci_lower=-0.25, ci_upper=0.05,
        pi_lower=-0.5, pi_upper=0.4,
        significant=False,
    )
    result = detect_prediction_gap(rma)
    assert result.severity == Severity.PASS


def test_insufficient_data_pi_not_computable():
    """PI not computable (k<3) — insufficient_data."""
    rma = _make_rma(
        estimate=-0.5,
        ci_lower=-0.9, ci_upper=-0.1,
        pi_lower=float("-inf"), pi_upper=float("inf"),
        pi_computable=False,
        k=2,
    )
    result = detect_prediction_gap(rma)
    assert result.metrics.get("insufficient_data") is True
