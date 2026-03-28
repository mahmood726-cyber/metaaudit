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

    For each iteration, add one event to the arm with fewer events in the
    study that has the smallest event count in the fewer-events arm.
    Continue until pooled p >= 0.05.
    """
    e_cases = study_data["Experimental.cases"].values.astype(float).copy()
    e_n = study_data["Experimental.N"].values.astype(float).copy()
    c_cases = study_data["Control.cases"].values.astype(float).copy()
    c_n = study_data["Control.N"].values.astype(float).copy()

    mafi = 0
    max_iter = 200  # guard against infinite loop

    for _ in range(max_iter):
        p = _compute_pooled_p(e_cases, e_n, c_cases, c_n)
        if p >= 0.05:
            break

        # Find study with fewest events in the experimental arm (fewer-events arm)
        # Per MAFI convention: modify arm with fewer events
        # Identify the arm with fewer events per study and pick study with fewest events
        exp_events = e_cases.copy()
        ctrl_events = c_cases.copy()

        # For each study, determine which arm has fewer events
        arm_fewer = np.where(exp_events <= ctrl_events, "exp", "ctrl")

        # Among the fewer-events arm values, find the study with fewest
        fewer_vals = np.where(arm_fewer == "exp", exp_events, ctrl_events)
        study_idx = int(np.argmin(fewer_vals))

        # Add one event to that arm (cap at N)
        if arm_fewer[study_idx] == "exp":
            e_cases[study_idx] = min(e_cases[study_idx] + 1, e_n[study_idx])
        else:
            c_cases[study_idx] = min(c_cases[study_idx] + 1, c_n[study_idx])

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
