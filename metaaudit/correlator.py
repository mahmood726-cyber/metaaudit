"""Correlator — flaw co-occurrence, prevalence, severity scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd

from metaaudit.severity import Severity, DetectorResult


def build_flaw_matrix(
    results: dict[str, list[DetectorResult]],
) -> pd.DataFrame:
    rows = {}
    for ma_id, detections in results.items():
        row = {}
        for d in detections:
            if not d.metrics.get("insufficient_data", False):
                row[d.module] = 1 if d.severity >= Severity.FAIL else 0
            else:
                row[d.module] = np.nan
        rows[ma_id] = row
    df = pd.DataFrame.from_dict(rows, orient="index")
    return df


def compute_prevalence(matrix: pd.DataFrame) -> dict[str, float]:
    result = {}
    for col in matrix.columns:
        valid = matrix[col].dropna()
        if len(valid) > 0:
            result[col] = float(valid.mean())
        else:
            result[col] = float("nan")
    return result


def compute_cooccurrence(matrix: pd.DataFrame) -> pd.DataFrame:
    cols = matrix.columns.tolist()
    n = len(cols)
    phi = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i == j:
                phi.iloc[i, j] = 1.0
                continue
            valid = matrix[[c1, c2]].dropna()
            if len(valid) < 5:
                phi.iloc[i, j] = np.nan
                continue
            a = valid[c1].values
            b = valid[c2].values
            if a.std() == 0 or b.std() == 0:
                phi.iloc[i, j] = 0.0
            else:
                phi.iloc[i, j] = float(np.corrcoef(a, b)[0, 1])
    return phi


def compute_severity_scores(
    results: dict[str, list[DetectorResult]],
) -> dict[str, float]:
    weights = {Severity.PASS: 0, Severity.WARN: 1, Severity.FAIL: 2, Severity.CRITICAL: 3}
    scores = {}
    for ma_id, detections in results.items():
        score = sum(
            weights.get(d.severity, 0) for d in detections
            if not d.metrics.get("insufficient_data", False)
        )
        scores[ma_id] = score
    return scores
