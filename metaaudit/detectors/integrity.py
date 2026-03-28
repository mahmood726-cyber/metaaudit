"""Detector: Data integrity (impossible values, GRIM, duplicates)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from metaaudit.loader import DataType
from metaaudit.severity import DetectorResult, Severity

MODULE = "integrity"

_DUPLICATE_THRESHOLD = 0.50  # >50% duplicate rows triggers WARN
_GRIM_N_MAX = 100             # Only check GRIM for N <= 100


def _check_grim(mean: float, n: int) -> bool:
    """GRIM (Granularity-Related Inconsistency of Means) check.

    Returns True if mean is consistent with sample size n
    (i.e. mean * n rounds to an integer).
    """
    if n <= 0 or not np.isfinite(mean):
        return True  # can't check
    product = mean * n
    return abs(product - round(product)) < 0.01


def _check_binary(df: pd.DataFrame) -> tuple[int, list[str]]:
    """Check binary data for impossible values. Returns (n_impossible, issues)."""
    issues = []
    n_impossible = 0

    for col in ["Experimental.cases", "Control.cases"]:
        if col in df.columns:
            neg = (df[col] < 0).sum()
            if neg > 0:
                n_impossible += int(neg)
                issues.append(f"{col}: {neg} negative value(s)")

    for col in ["Experimental.N", "Control.N"]:
        if col in df.columns:
            non_pos = (df[col] <= 0).sum()
            if non_pos > 0:
                n_impossible += int(non_pos)
                issues.append(f"{col}: {non_pos} non-positive N value(s)")

    # Events exceed N
    if all(c in df.columns for c in ["Experimental.cases", "Experimental.N"]):
        exceed = (df["Experimental.cases"] > df["Experimental.N"]).sum()
        if exceed > 0:
            n_impossible += int(exceed)
            issues.append(f"Experimental.cases > Experimental.N in {exceed} study/studies")

    if all(c in df.columns for c in ["Control.cases", "Control.N"]):
        exceed = (df["Control.cases"] > df["Control.N"]).sum()
        if exceed > 0:
            n_impossible += int(exceed)
            issues.append(f"Control.cases > Control.N in {exceed} study/studies")

    return n_impossible, issues


def _check_continuous(df: pd.DataFrame) -> tuple[int, list[str]]:
    """Check continuous data for impossible values. Returns (n_impossible, issues)."""
    issues = []
    n_impossible = 0

    for col in ["Experimental.SD", "Control.SD"]:
        if col in df.columns:
            neg = (df[col] < 0).sum()
            if neg > 0:
                n_impossible += int(neg)
                issues.append(f"{col}: {neg} negative SD value(s)")

    for col in ["Experimental.N", "Control.N"]:
        if col in df.columns:
            non_pos = (df[col] <= 0).sum()
            if non_pos > 0:
                n_impossible += int(non_pos)
                issues.append(f"{col}: {non_pos} non-positive N value(s)")

    # GRIM check for small N
    for arm, mean_col, n_col in [
        ("Experimental", "Experimental.mean", "Experimental.N"),
        ("Control", "Control.mean", "Control.N"),
    ]:
        if mean_col in df.columns and n_col in df.columns:
            for i, row in df.iterrows():
                n = int(row[n_col]) if pd.notna(row[n_col]) else 0
                mean = float(row[mean_col]) if pd.notna(row[mean_col]) else float("nan")
                if 0 < n <= _GRIM_N_MAX and not _check_grim(mean, n):
                    issues.append(
                        f"GRIM fail: study {i} {arm} mean={mean:.3f}, N={n}"
                    )

    return n_impossible, issues


def _check_duplicates(df: pd.DataFrame) -> float:
    """Return fraction of rows that are duplicates."""
    n = len(df)
    if n < 2:
        return 0.0
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return 0.0
    dup_mask = df[numeric_cols].duplicated(keep="first")
    return float(dup_mask.sum()) / n


def detect_integrity(df: pd.DataFrame, data_type: DataType) -> DetectorResult:
    """Check data integrity: impossible values, GRIM, duplicates.

    Rules:
    - FAIL for impossible values (events>N, negative cases, negative SD)
    - WARN for >50% duplicate rows
    - PASS otherwise
    """
    if data_type == DataType.BINARY:
        n_impossible, issues = _check_binary(df)
    elif data_type == DataType.CONTINUOUS:
        n_impossible, issues = _check_continuous(df)
    else:
        # GIV: just check for NaN/infinite
        n_impossible = 0
        issues = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                n_inf = (~np.isfinite(df[col].values.astype(float))).sum()
                if n_inf > 0:
                    issues.append(f"{col}: {n_inf} non-finite value(s)")

    dup_fraction = _check_duplicates(df)
    metrics: dict[str, Any] = {
        "insufficient_data": False,
        "n_impossible": n_impossible,
        "duplicate_fraction": float(dup_fraction),
        "issues": issues,
        "data_type": data_type.value,
    }

    if n_impossible > 0:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=f"{n_impossible} impossible value(s): {'; '.join(issues[:3])}",
            metrics=metrics,
        )

    if dup_fraction >= _DUPLICATE_THRESHOLD:
        pct = dup_fraction * 100
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"{pct:.0f}% of study rows are duplicates. "
                "Possible copy-paste error or data entry issue."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail="No data integrity issues detected.",
        metrics=metrics,
    )
