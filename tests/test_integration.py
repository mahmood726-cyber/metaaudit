# tests/test_integration.py
"""Integration test: full pipeline on synthetic + real data."""

import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from metaaudit.loader import DataType, AnalysisGroup
from metaaudit.recompute import recompute_ma
from metaaudit.detectors.prediction_gap import detect_prediction_gap
from metaaudit.detectors.model_misspec import detect_model_misspec
from metaaudit.detectors.fragility import detect_fragility
from metaaudit.detectors.underpowered import detect_underpowered
from metaaudit.detectors.pub_bias import detect_pub_bias
from metaaudit.detectors.small_study import detect_small_study
from metaaudit.detectors.excess_sig import detect_excess_sig
from metaaudit.detectors.integrity import detect_integrity
from metaaudit.detectors.overlap import detect_overlap, build_overlap_index
from metaaudit.detectors.overclaiming import detect_overclaiming
from metaaudit.detectors.certainty_mismatch import detect_certainty_mismatch
from metaaudit.correlator import build_flaw_matrix, compute_prevalence
from metaaudit.export import export_json, export_csv
from metaaudit.severity import Severity


def _run_all_detectors(df, data_type, review_id="TEST"):
    """Run full pipeline on one synthetic MA."""
    ma = recompute_ma(df, data_type)
    results = []
    results.append(detect_prediction_gap(ma))
    ctx = {}
    if data_type == DataType.BINARY:
        total_e = df["Experimental.cases"].sum() + df["Control.cases"].sum()
        total_n = df["Experimental.N"].sum() + df["Control.N"].sum()
        ctx["event_rate"] = total_e / total_n if total_n > 0 else 0
    results.append(detect_model_misspec(ma, ctx))
    study_data = df if data_type == DataType.BINARY else None
    results.append(detect_fragility(ma, study_data))
    total_n = int(df["Experimental.N"].sum() + df.get("Control.N", pd.Series([0])).sum())
    results.append(detect_underpowered(ma, total_n))
    results.append(detect_pub_bias(ma))
    results.append(detect_small_study(ma))
    results.append(detect_excess_sig(ma))
    results.append(detect_integrity(df, data_type))
    results.append(detect_overlap(review_id, set(), {}))
    results.append(detect_overclaiming(ma))
    results.append(detect_certainty_mismatch(None, results[:10]))
    return results


def test_clean_large_binary_ma():
    """A well-behaved MA with 12 studies, clear effect, low heterogeneity."""
    rng = np.random.default_rng(42)
    k = 12
    df = pd.DataFrame({
        "Study": [f"Study_{i}" for i in range(k)],
        "Study.year": list(range(2010, 2010 + k)),
        "Experimental.cases": rng.integers(5, 15, k),
        "Experimental.N": rng.integers(80, 150, k),
        "Control.cases": rng.integers(20, 35, k),
        "Control.N": rng.integers(80, 150, k),
    })
    results = _run_all_detectors(df, DataType.BINARY)
    assert len(results) == 11
    fail_count = sum(1 for r in results if r.severity >= Severity.FAIL)
    assert fail_count <= 3


def test_problematic_binary_ma():
    """A highly heterogeneous, small MA with suspicious patterns."""
    df = pd.DataFrame({
        "Study": ["A", "B", "C"],
        "Study.year": [2015, 2016, 2017],
        "Experimental.cases": [1, 40, 2],
        "Experimental.N": [100, 50, 100],
        "Control.cases": [2, 5, 3],
        "Control.N": [100, 50, 100],
    })
    results = _run_all_detectors(df, DataType.BINARY)
    assert len(results) == 11
    severities = [r.severity for r in results]
    assert Severity.WARN in severities or Severity.FAIL in severities


def test_full_pipeline_export():
    """Run pipeline, export, verify JSON structure."""
    rng = np.random.default_rng(99)
    k = 8
    df = pd.DataFrame({
        "Study": [f"S{i}" for i in range(k)],
        "Study.year": list(range(2012, 2012 + k)),
        "Experimental.cases": rng.integers(5, 20, k),
        "Experimental.N": rng.integers(80, 120, k),
        "Control.cases": rng.integers(15, 30, k),
        "Control.N": rng.integers(80, 120, k),
    })
    results = _run_all_detectors(df, DataType.BINARY, review_id="INTEG_TEST")
    all_results = {"INTEG_TEST__A1": results}

    with tempfile.TemporaryDirectory() as tmp:
        json_path = os.path.join(tmp, "test.json")
        csv_path = os.path.join(tmp, "test.csv")
        export_json(all_results, json_path)
        export_csv(all_results, csv_path)

        with open(json_path) as f:
            data = json.load(f)
        assert "INTEG_TEST__A1" in data
        assert len(data["INTEG_TEST__A1"]) == 11

        matrix = build_flaw_matrix(all_results)
        prev = compute_prevalence(matrix)
        assert len(prev) > 0


def _pairwise70_dir():
    env_data = os.getenv("METAAUDIT_DATA_DIR") or os.getenv("PAIRWISE70_DATA_DIR")
    candidates = []
    if env_data:
        candidates.append(Path(env_data).expanduser())
    project_root = Path(__file__).resolve().parents[1]
    candidates.extend([
        project_root.parent / "Projects" / "Pairwise70" / "data",
        project_root.parent / "Models" / "Pairwise70" / "data",
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


PAIRWISE70_DIR = _pairwise70_dir()


@pytest.mark.skipif(
    PAIRWISE70_DIR is None or not PAIRWISE70_DIR.exists(),
    reason="Pairwise70 data not available"
)
def test_real_review_cd000028():
    """Run full pipeline on a real Cochrane review."""
    from metaaudit.loader import load_rda_file
    path = PAIRWISE70_DIR / "CD000028_pub4_data.rda"
    review = load_rda_file(path)
    assert len(review.analyses) > 0
    ag = review.analyses[0]
    results = _run_all_detectors(ag.df, ag.data_type, review_id=review.review_id)
    assert len(results) == 11
    for r in results:
        assert r.module is not None
        assert r.severity is not None
