"""Detector: Meta-Analytic Fragility Index (MAFI)."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from metaaudit.loader import DataType
from metaaudit.recompute import RecomputedMA, compute_log_or, pool_effects_reml
from metaaudit.severity import DetectorResult, Severity

MODULE = "fragility"

_MAFI_FAIL = 2
_MAFI_WARN = 5


def _compute_pooled_p(e_cases: np.ndarray, e_n: np.ndarray,
                      c_cases: np.ndarray, c_n: np.ndarray) -> float:
    """Compute p-value for pooled meta-analysis."""
    try:
        yi, vi = compute_log_or(e_cases, e_n, c_cases, c_n)
        mask = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
        yi = yi[mask]
        vi = vi[mask]
        if len(yi) < 2:
            return 1.0
        pooled = pool_effects_reml(yi, vi)
        return pooled["p_value"]
    except Exception:
        return 1.0


def _compute_mafi(study_data: pd.DataFrame) -> int:
    """Compute meta-analytic fragility index.

    For each iteration, try adding 1 event to EACH arm of EACH study and pick
    the single modification that most efficiently moves the pooled p-value
    toward non-significance (maximises p). Continue until pooled p >= 0.05.
    """
    e_cases = study_data["Experimental.cases"].values.astype(float).copy()
    e_n = study_data["Experimental.N"].values.astype(float).copy()
    c_cases = study_data["Control.cases"].values.astype(float).copy()
    c_n = study_data["Control.N"].values.astype(float).copy()

    mafi = 0
    max_iter = 200

    for _ in range(max_iter):
        p = _compute_pooled_p(e_cases, e_n, c_cases, c_n)
        if p >= 0.05:
            break

        # Try adding 1 event to each arm of each study; pick the modification
        # that produces the highest p-value (most efficient path to non-significance)
        best_p = -1.0
        best_study = -1
        best_arm = ""
        k = len(e_cases)

        for i in range(k):
            # Try adding to experimental arm
            if e_cases[i] < e_n[i]:
                e_cases[i] += 1
                trial_p = _compute_pooled_p(e_cases, e_n, c_cases, c_n)
                if trial_p > best_p:
                    best_p = trial_p
                    best_study = i
                    best_arm = "exp"
                e_cases[i] -= 1  # undo

            # Try adding to control arm
            if c_cases[i] < c_n[i]:
                c_cases[i] += 1
                trial_p = _compute_pooled_p(e_cases, e_n, c_cases, c_n)
                if trial_p > best_p:
                    best_p = trial_p
                    best_study = i
                    best_arm = "ctrl"
                c_cases[i] -= 1  # undo

        if best_study == -1:
            break  # All cells at cap

        # Apply the best modification
        if best_arm == "exp":
            e_cases[best_study] += 1
        else:
            c_cases[best_study] += 1
        mafi += 1

    return mafi


def detect_fragility(
    rma: RecomputedMA,
    study_data: Optional[pd.DataFrame],
) -> DetectorResult:
    """Compute Meta-Analytic Fragility Index (MAFI).

    Rules:
    - insufficient_data for non-binary data or missing study_data
    - PASS if not significant (fragility irrelevant)
    - FAIL if MAFI <= 2
    - WARN if 3 <= MAFI <= 5
    - PASS if MAFI > 5
    """
    if rma.data_type != DataType.BINARY or study_data is None:
        return DetectorResult.insufficient_data(
            MODULE, "MAFI requires binary study-level data"
        )

    if not rma.significant:
        return DetectorResult(
            module=MODULE,
            severity=Severity.PASS,
            detail="Not significant; fragility index not applicable.",
            metrics={"insufficient_data": False},
        )

    required_cols = {"Experimental.cases", "Experimental.N", "Control.cases", "Control.N"}
    if not required_cols.issubset(study_data.columns):
        return DetectorResult.insufficient_data(
            MODULE, "study_data missing required binary columns"
        )

    mafi = _compute_mafi(study_data)

    metrics = {
        "insufficient_data": False,
        "mafi": mafi,
        "k": rma.k,
    }

    if mafi <= _MAFI_FAIL:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"MAFI = {mafi}: significance lost after only {mafi} event(s) changed. "
                "Result is fragile."
            ),
            metrics=metrics,
        )

    if mafi <= _MAFI_WARN:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"MAFI = {mafi}: significance requires {mafi} event changes — borderline robust."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=f"MAFI = {mafi}: result is robust (>{_MAFI_WARN} event changes needed).",
        metrics=metrics,
    )
