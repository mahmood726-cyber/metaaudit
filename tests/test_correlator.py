import pytest
import numpy as np
from metaaudit.severity import Severity, DetectorResult
from metaaudit.correlator import (
    build_flaw_matrix,
    compute_prevalence,
    compute_cooccurrence,
    compute_severity_scores,
)


def _sample_results():
    return {
        "MA1": [
            DetectorResult("prediction_gap", Severity.FAIL, "", {}),
            DetectorResult("fragility", Severity.FAIL, "", {}),
            DetectorResult("pub_bias", Severity.PASS, "", {}),
        ],
        "MA2": [
            DetectorResult("prediction_gap", Severity.FAIL, "", {}),
            DetectorResult("fragility", Severity.PASS, "", {}),
            DetectorResult("pub_bias", Severity.FAIL, "", {}),
        ],
        "MA3": [
            DetectorResult("prediction_gap", Severity.PASS, "", {}),
            DetectorResult("fragility", Severity.PASS, "", {}),
            DetectorResult("pub_bias", Severity.PASS, "", {}),
        ],
    }


def test_build_flaw_matrix():
    matrix = build_flaw_matrix(_sample_results())
    assert matrix.shape == (3, 3)
    assert matrix.iloc[0, 0] == 1  # MA1, prediction_gap = FAIL
    assert matrix.iloc[2, 2] == 0  # MA3, pub_bias = PASS


def test_compute_prevalence():
    matrix = build_flaw_matrix(_sample_results())
    prev = compute_prevalence(matrix)
    assert prev["prediction_gap"] == pytest.approx(2/3, abs=0.01)
    assert prev["pub_bias"] == pytest.approx(1/3, abs=0.01)


def test_compute_cooccurrence():
    matrix = build_flaw_matrix(_sample_results())
    cooc = compute_cooccurrence(matrix)
    assert cooc.shape == (3, 3)
    for i in range(3):
        assert cooc.iloc[i, i] == pytest.approx(1.0, abs=0.01)


def test_severity_scores():
    scores = compute_severity_scores(_sample_results())
    assert scores["MA1"] > scores["MA3"]
    assert scores["MA2"] > scores["MA3"]
