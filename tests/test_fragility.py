"""Tests for fragility detector (MAFI)."""

import numpy as np
import pandas as pd
import pytest

from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.fragility import detect_fragility


def _make_rma(significant=True, data_type=DataType.BINARY, k=5):
    return RecomputedMA(
        k=k,
        yi=np.array([-0.5] * k),
        vi=np.array([0.05] * k),
        estimate=-0.5,
        se=0.1,
        se_hksj=0.1,
        ci_lower=-0.7,
        ci_upper=-0.3,
        p_value=0.01 if significant else 0.5,
        tau2=0.02,
        I2=20.0,
        Q=5.0,
        significant=significant,
        pi_lower=-1.0,
        pi_upper=0.0,
        pi_computable=True,
        data_type=data_type,
        measure="logOR",
    )


def _fragile_data():
    """Very small binary study data — easily fragile."""
    return pd.DataFrame({
        "Experimental.cases": [1, 2, 1],
        "Experimental.N": [20, 20, 20],
        "Control.cases": [5, 6, 5],
        "Control.N": [20, 20, 20],
    })


def _robust_data():
    """Large binary study data — robust."""
    return pd.DataFrame({
        "Experimental.cases": [50, 60, 55, 65, 58],
        "Experimental.N": [200, 200, 200, 200, 200],
        "Control.cases": [100, 110, 105, 115, 108],
        "Control.N": [200, 200, 200, 200, 200],
    })


def test_fragile_mafi_le2():
    """Fragile data: MAFI should be <=2 — FAIL."""
    rma = _make_rma(k=3)
    result = detect_fragility(rma, study_data=_fragile_data())
    assert result.severity == Severity.FAIL
    assert result.metrics["mafi"] <= 2


def test_robust_mafi_gt5():
    """Robust data: MAFI should be >5 — PASS."""
    rma = _make_rma(k=5)
    result = detect_fragility(rma, study_data=_robust_data())
    assert result.severity == Severity.PASS
    assert result.metrics["mafi"] > 5


def test_not_significant_skip():
    """Not significant — PASS (skip fragility check)."""
    rma = _make_rma(significant=False, k=3)
    result = detect_fragility(rma, study_data=_fragile_data())
    assert result.severity == Severity.PASS


def test_continuous_insufficient():
    """Continuous data — insufficient_data."""
    rma = _make_rma(data_type=DataType.CONTINUOUS, k=4)
    result = detect_fragility(rma, study_data=None)
    assert result.metrics.get("insufficient_data") is True


def test_no_study_data_insufficient():
    """No study_data provided — insufficient_data."""
    rma = _make_rma(k=4)
    result = detect_fragility(rma, study_data=None)
    assert result.metrics.get("insufficient_data") is True
