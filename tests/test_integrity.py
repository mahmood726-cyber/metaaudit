"""Tests for integrity detector (impossible values, GRIM, duplicates)."""

import numpy as np
import pandas as pd
import pytest

from metaaudit.loader import DataType
from metaaudit.severity import Severity
from metaaudit.detectors.integrity import detect_integrity


def _binary_df(e_cases, e_n, c_cases, c_n):
    return pd.DataFrame({
        "Experimental.cases": e_cases,
        "Experimental.N": e_n,
        "Control.cases": c_cases,
        "Control.N": c_n,
    })


def _continuous_df(e_mean, e_sd, e_n, c_mean, c_sd, c_n):
    return pd.DataFrame({
        "Experimental.mean": e_mean,
        "Experimental.SD": e_sd,
        "Experimental.N": e_n,
        "Control.mean": c_mean,
        "Control.SD": c_sd,
        "Control.N": c_n,
    })


def test_pass_clean_binary():
    """Clean binary data — PASS."""
    df = _binary_df(
        e_cases=[10, 15, 8],
        e_n=[100, 120, 80],
        c_cases=[20, 25, 15],
        c_n=[100, 120, 80],
    )
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_fail_events_exceed_n():
    """Events > N — impossible value — FAIL."""
    df = _binary_df(
        e_cases=[10, 130, 8],  # 130 > 120
        e_n=[100, 120, 80],
        c_cases=[20, 25, 15],
        c_n=[100, 120, 80],
    )
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.FAIL
    assert result.metrics["n_impossible"] > 0


def test_warn_duplicates():
    """More than 50% duplicate rows — WARN."""
    df = _binary_df(
        e_cases=[10, 10, 10, 15],   # 3/4 identical rows -> 75%
        e_n=[100, 100, 100, 120],
        c_cases=[20, 20, 20, 25],
        c_n=[100, 100, 100, 120],
    )
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.WARN


def test_fail_negative_values_binary():
    """Negative cases — impossible — FAIL."""
    df = _binary_df(
        e_cases=[-1, 15, 8],
        e_n=[100, 120, 80],
        c_cases=[20, 25, 15],
        c_n=[100, 120, 80],
    )
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.FAIL


def test_pass_clean_continuous():
    """Clean continuous data — PASS."""
    df = _continuous_df(
        e_mean=[120.0, 118.5],
        e_sd=[15.0, 12.0],
        e_n=[50, 60],
        c_mean=[130.0, 128.0],
        c_sd=[16.0, 13.0],
        c_n=[50, 60],
    )
    result = detect_integrity(df, DataType.CONTINUOUS)
    assert result.severity == Severity.PASS


def test_fail_negative_sd():
    """Negative SD — impossible — FAIL."""
    df = _continuous_df(
        e_mean=[120.0, 118.5],
        e_sd=[-15.0, 12.0],  # negative SD
        e_n=[50, 60],
        c_mean=[130.0, 128.0],
        c_sd=[16.0, 13.0],
        c_n=[50, 60],
    )
    result = detect_integrity(df, DataType.CONTINUOUS)
    assert result.severity == Severity.FAIL
    assert result.metrics["n_impossible"] > 0
