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


def _fast_pooled_p(yi: np.ndarray, vi: np.ndarray) -> float:
    """Fast DL-based p-value for fragility inner loop."""
    k = len(yi)
    if k < 2:
        return 1.0
    wi = 1.0 / vi
    w_sum = wi.sum()
    theta = (wi * yi).sum() / w_sum
    Q = (wi * (yi - theta) ** 2).sum()
    c = w_sum - (wi ** 2).sum() / w_sum
    tau2 = max(0.0, (Q - (k - 1)) / c)
    w = 1.0 / (vi + tau2)
    w_sum = w.sum()
    est = (w * yi).sum() / w_sum
    se = 1.0 / np.sqrt(w_sum)
    if se <= 0:
        return 1.0
    z = abs(est / se)
    return float(2 * (1 - stats.norm.cdf(z)))


def _compute_mafi(study_data: pd.DataFrame) -> int:
    """Compute meta-analytic fragility index.

    Optimized: uses DL (not REML) for inner loop speed. Modifies the arm
    that moves the pooled effect toward null. Caps at _MAFI_WARN+1 since
    we only need to classify as <=2, <=5, or >5.
    """
    e_cases = study_data["Experimental.cases"].values.astype(float).copy()
    e_n = study_data["Experimental.N"].values.astype(float).copy()
    c_cases = study_data["Control.cases"].values.astype(float).copy()
    c_n = study_data["Control.N"].values.astype(float).copy()

    mafi = 0
    max_mafi = _MAFI_WARN + 1  # Only need to know if >5

    # Determine effect direction from initial pooling
    yi, vi = compute_log_or(e_cases, e_n, c_cases, c_n)
    mask = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
    if mask.sum() < 2:
        return max_mafi
    yi_m, vi_m = yi[mask], vi[mask]
    wi = 1.0 / vi_m
    initial_est = (wi * yi_m).sum() / wi.sum()
    # To move toward null: if effect < 0 (fewer exp events), add to exp arm
    # If effect > 0, add to control arm
    modify_exp = initial_est < 0

    for _ in range(max_mafi):
        yi, vi = compute_log_or(e_cases, e_n, c_cases, c_n)
        mask = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
        if mask.sum() < 2:
            break
        p = _fast_pooled_p(yi[mask], vi[mask])
        if p >= 0.05:
            break

        # Find the study where adding 1 event to the target arm
        # has the biggest effect-reducing impact (largest difference from arm ratio)
        if modify_exp:
            room = e_n - e_cases
            diffs = c_cases / np.maximum(c_n, 1) - e_cases / np.maximum(e_n, 1)
        else:
            room = c_n - c_cases
            diffs = e_cases / np.maximum(e_n, 1) - c_cases / np.maximum(c_n, 1)

        # Only consider studies with room to modify
        candidates = np.where(room > 0)[0]
        if len(candidates) == 0:
            break

        # Pick study with largest rate difference (most room to equalize)
        best_idx = candidates[np.argmax(diffs[candidates])]

        if modify_exp:
            e_cases[best_idx] += 1
        else:
            c_cases[best_idx] += 1
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
