"""Tests for certainty_mismatch detector (GRADE vs automated severity)."""

import pytest

from metaaudit.severity import Severity, DetectorResult
from metaaudit.detectors.certainty_mismatch import detect_certainty_mismatch


def _make_fail_results(n: int) -> list[DetectorResult]:
    """Create n FAIL results."""
    return [
        DetectorResult(
            module=f"module_{i}",
            severity=Severity.FAIL,
            detail="Fail",
            metrics={},
        )
        for i in range(n)
    ]


def _make_pass_results(n: int) -> list[DetectorResult]:
    """Create n PASS results."""
    return [
        DetectorResult(
            module=f"module_{i}",
            severity=Severity.PASS,
            detail="Pass",
            metrics={},
        )
        for i in range(n)
    ]


def test_no_grade_insufficient_data():
    """No GRADE certainty — insufficient_data."""
    result = detect_certainty_mismatch(
        grade_certainty=None,
        other_results=_make_fail_results(3),
    )
    assert result.metrics.get("insufficient_data") is True


def test_pass_high_grade_no_fails():
    """High certainty, no FAIL results — PASS."""
    result = detect_certainty_mismatch(
        grade_certainty="High",
        other_results=_make_pass_results(5),
    )
    assert result.severity == Severity.PASS
    assert result.metrics["insufficient_data"] is False


def test_critical_high_grade_3_fails():
    """High certainty + 3 FAILs — CRITICAL."""
    results = _make_fail_results(3) + _make_pass_results(3)
    result = detect_certainty_mismatch(
        grade_certainty="High",
        other_results=results,
    )
    assert result.severity == Severity.CRITICAL
    assert result.metrics["n_fails"] == 3


def test_fail_moderate_grade_4_fails():
    """Moderate certainty + 4 FAILs — FAIL."""
    results = _make_fail_results(4) + _make_pass_results(2)
    result = detect_certainty_mismatch(
        grade_certainty="Moderate",
        other_results=results,
    )
    assert result.severity == Severity.FAIL


def test_warn_high_grade_2_fails():
    """High certainty + 2 FAILs — WARN."""
    results = _make_fail_results(2) + _make_pass_results(4)
    result = detect_certainty_mismatch(
        grade_certainty="High",
        other_results=results,
    )
    assert result.severity == Severity.WARN


def test_pass_low_grade_with_fails():
    """Low certainty with FAILs — PASS (already discounted)."""
    results = _make_fail_results(5)
    result = detect_certainty_mismatch(
        grade_certainty="Low",
        other_results=results,
    )
    assert result.severity == Severity.PASS


def test_pass_very_low_grade_with_fails():
    """Very low certainty with FAILs — PASS (already discounted)."""
    results = _make_fail_results(5)
    result = detect_certainty_mismatch(
        grade_certainty="Very low",
        other_results=results,
    )
    assert result.severity == Severity.PASS


def test_case_insensitive_grade():
    """Grade certainty matching is case-insensitive."""
    results = _make_fail_results(3)
    result = detect_certainty_mismatch(
        grade_certainty="HIGH",  # uppercase
        other_results=results,
    )
    assert result.severity == Severity.CRITICAL
