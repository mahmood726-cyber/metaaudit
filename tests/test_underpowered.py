"""Tests for underpowered detector."""

import numpy as np
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.underpowered import detect_underpowered


def _make_rma(k, significant=True):
    return RecomputedMA(
        k=k,
        yi=np.array([-0.5] * k),
        vi=np.array([0.04] * k),
        estimate=-0.5,
        se=0.1,
        se_hksj=0.1,
        ci_lower=-0.7,
        ci_upper=-0.3,
        p_value=0.01 if significant else 0.5,
        tau2=0.02,
        I2=25.0,
        Q=float(k),
        significant=significant,
        pi_lower=-1.0,
        pi_upper=0.0,
        pi_computable=k >= 3,
        data_type=DataType.BINARY,
        measure="logOR",
    )


def test_pass_k10_large_n():
    """k=10, N=2000 — PASS."""
    rma = _make_rma(k=10)
    result = detect_underpowered(rma, total_n=2000)
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_warn_k4():
    """k=4 — WARN (< 5 studies)."""
    rma = _make_rma(k=4)
    result = detect_underpowered(rma, total_n=2000)
    assert result.severity == Severity.WARN


def test_fail_k2_significant():
    """k=2, significant — FAIL."""
    rma = _make_rma(k=2, significant=True)
    result = detect_underpowered(rma, total_n=2000)
    assert result.severity == Severity.FAIL


def test_warn_k2_not_significant():
    """k=2, not significant — WARN (not FAIL, since not claiming effect)."""
    rma = _make_rma(k=2, significant=False)
    result = detect_underpowered(rma, total_n=2000)
    assert result.severity == Severity.WARN


def test_warn_small_n_significant():
    """k=10 but N=800 and significant — WARN (below OIS)."""
    rma = _make_rma(k=10, significant=True)
    result = detect_underpowered(rma, total_n=800)
    assert result.severity == Severity.WARN


def test_pass_small_n_not_significant():
    """k=10, N=800, not significant — PASS (OIS only matters when claiming effect)."""
    rma = _make_rma(k=10, significant=False)
    result = detect_underpowered(rma, total_n=800)
    assert result.severity == Severity.PASS
