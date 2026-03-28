"""Tests for overclaiming detector (effect vs MCID)."""

import math
import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.overclaiming import detect_overclaiming


def _make_rma(estimate, measure="logOR", significant=True, data_type=DataType.BINARY, k=8):
    ci_low = estimate - 0.3
    ci_high = estimate + 0.3
    sig = significant and not (ci_low <= 0 <= ci_high)
    # For the test, force significance via p_value
    return RecomputedMA(
        k=k,
        yi=np.array([estimate] * k),
        vi=np.array([0.04] * k),
        estimate=estimate,
        se=0.1,
        se_hksj=0.1,
        ci_lower=ci_low,
        ci_upper=ci_high,
        p_value=0.01 if significant else 0.5,
        tau2=0.02,
        I2=20.0,
        Q=float(k),
        significant=significant,
        pi_lower=estimate - 0.8,
        pi_upper=estimate + 0.8,
        pi_computable=True,
        data_type=data_type,
        measure=measure,
    )


def test_pass_large_logOR():
    """logOR=-0.7 >> MCID(0.223) — PASS."""
    rma = _make_rma(estimate=-0.7, measure="logOR")
    result = detect_overclaiming(rma)
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_fail_trivial_logOR():
    """logOR=-0.05 < 50% of MCID — FAIL (trivially small)."""
    rma = _make_rma(estimate=-0.05, measure="logOR")
    result = detect_overclaiming(rma)
    assert result.severity == Severity.FAIL


def test_pass_not_significant():
    """Not significant — PASS (overclaiming not applicable)."""
    rma = _make_rma(estimate=-0.05, measure="logOR", significant=False)
    result = detect_overclaiming(rma)
    assert result.severity == Severity.PASS


def test_warn_borderline_logOR():
    """logOR=-0.15 < MCID(0.223) but >=50% — WARN."""
    rma = _make_rma(estimate=-0.15, measure="logOR")
    result = detect_overclaiming(rma)
    assert result.severity == Severity.WARN


def test_warn_small_smd():
    """SMD=-0.15 below MCID(0.2) — WARN."""
    rma = _make_rma(estimate=-0.15, measure="SMD",
                    data_type=DataType.CONTINUOUS)
    result = detect_overclaiming(rma)
    assert result.severity == Severity.WARN


def test_metrics_present():
    """Metrics include mcid, effect_abs, fraction_of_mcid."""
    rma = _make_rma(estimate=-0.5, measure="logOR")
    result = detect_overclaiming(rma)
    assert "mcid" in result.metrics
    assert "effect_abs" in result.metrics
    assert "fraction_of_mcid" in result.metrics
