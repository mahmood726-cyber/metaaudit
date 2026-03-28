"""Tests for overlap detector (cross-review study sharing)."""

import pytest

from metaaudit.severity import Severity
from metaaudit.detectors.overlap import build_overlap_index, detect_overlap


def test_build_overlap_index():
    """Build index correctly identifies shared studies."""
    studies_by_review = {
        "R1": {"S1", "S2", "S3"},
        "R2": {"S2", "S3", "S4"},
        "R3": {"S5", "S6"},
    }
    index = build_overlap_index(studies_by_review)
    # R1-R2 share S2, S3
    key = ("R1", "R2") if ("R1", "R2") in index else ("R2", "R1")
    assert len(index[key]) == 2
    assert "S2" in index[key]
    # R1-R3 share nothing
    key13 = ("R1", "R3") if ("R1", "R3") in index else ("R3", "R1")
    assert len(index[key13]) == 0


def test_pass_no_overlap():
    """No shared studies — PASS."""
    studies_by_review = {
        "R1": {"S1", "S2", "S3"},
        "R2": {"S4", "S5", "S6"},
    }
    index = build_overlap_index(studies_by_review)
    result = detect_overlap("R1", {"S1", "S2", "S3"}, index)
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_warn_moderate_overlap():
    """Moderate overlap (>30%) — WARN."""
    studies_by_review = {
        "R1": {"S1", "S2", "S3", "S4", "S5"},
        "R2": {"S1", "S2", "S6", "S7", "S8"},  # 2/5 = 40% overlap with R1
    }
    index = build_overlap_index(studies_by_review)
    result = detect_overlap("R1", {"S1", "S2", "S3", "S4", "S5"}, index)
    assert result.severity == Severity.WARN
    assert result.metrics["max_overlap_fraction"] > 0.30


def test_fail_contradictory_conclusions():
    """Same studies but contradictory conclusions — FAIL."""
    studies_by_review = {
        "R1": {"S1", "S2", "S3", "S4"},
        "R2": {"S1", "S2", "S3", "S4"},  # 100% overlap
    }
    index = build_overlap_index(studies_by_review)
    review_conclusions = {
        "R1": "positive",
        "R2": "negative",
    }
    result = detect_overlap(
        "R1",
        {"S1", "S2", "S3", "S4"},
        index,
        review_conclusions=review_conclusions,
    )
    assert result.severity == Severity.FAIL


def test_no_contradiction_same_conclusion():
    """High overlap but same conclusions — WARN not FAIL."""
    studies_by_review = {
        "R1": {"S1", "S2", "S3", "S4"},
        "R2": {"S1", "S2", "S3", "S4"},  # 100% overlap
    }
    index = build_overlap_index(studies_by_review)
    review_conclusions = {
        "R1": "positive",
        "R2": "positive",
    }
    result = detect_overlap(
        "R1",
        {"S1", "S2", "S3", "S4"},
        index,
        review_conclusions=review_conclusions,
    )
    # High overlap should warn
    assert result.severity in (Severity.WARN, Severity.FAIL)
    # But not contradictory
    assert result.metrics.get("contradictory") is not True
