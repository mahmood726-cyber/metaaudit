"""Detector: Cross-review study overlap."""

from __future__ import annotations

from typing import Any, Optional

from metaaudit.severity import DetectorResult, Severity

MODULE = "overlap"

_OVERLAP_WARN_THRESHOLD = 0.30
_CONTRADICTORY_CONCLUSIONS = {
    ("positive", "negative"),
    ("negative", "positive"),
    ("benefit", "harm"),
    ("harm", "benefit"),
    ("significant", "not_significant"),
    ("not_significant", "significant"),
}


def build_overlap_index(
    studies_by_review: dict[str, set[str]],
) -> dict[tuple[str, str], set[str]]:
    """Build an index of shared studies between all pairs of reviews.

    Returns a dict mapping (review_id_a, review_id_b) -> set of shared study IDs.
    Keys are always sorted so (A, B) always precedes (B, A).
    """
    review_ids = sorted(studies_by_review.keys())
    index: dict[tuple[str, str], set[str]] = {}

    for i, r1 in enumerate(review_ids):
        for r2 in review_ids[i + 1:]:
            shared = studies_by_review[r1] & studies_by_review[r2]
            index[(r1, r2)] = shared

    return index


def _get_shared(
    review_id: str,
    overlap_index: dict[tuple[str, str], set[str]],
) -> list[tuple[str, set[str]]]:
    """Find all other reviews that share studies with review_id."""
    results = []
    for (r1, r2), shared in overlap_index.items():
        if r1 == review_id:
            results.append((r2, shared))
        elif r2 == review_id:
            results.append((r1, shared))
    return results


def _is_contradictory(c1: str, c2: str) -> bool:
    """Check if two conclusion strings are contradictory."""
    c1 = c1.lower().strip()
    c2 = c2.lower().strip()
    return (c1, c2) in _CONTRADICTORY_CONCLUSIONS or (c2, c1) in _CONTRADICTORY_CONCLUSIONS


def detect_overlap(
    review_id: str,
    studies: set[str],
    overlap_index: dict[tuple[str, str], set[str]],
    review_conclusions: Optional[dict[str, str]] = None,
) -> DetectorResult:
    """Detect problematic study overlap with other reviews.

    Rules:
    - FAIL if contradictory conclusions with an overlapping review
    - WARN if max overlap > 30%
    - PASS otherwise
    """
    n_studies = len(studies)
    if n_studies == 0:
        return DetectorResult.insufficient_data(MODULE, "No studies in review")

    pairs = _get_shared(review_id, overlap_index)

    max_overlap_fraction = 0.0
    max_overlap_partner = None
    contradictory = False
    contradictory_partner = None

    for other_id, shared in pairs:
        if not shared:
            continue
        overlap_fraction = len(shared) / n_studies
        if overlap_fraction > max_overlap_fraction:
            max_overlap_fraction = overlap_fraction
            max_overlap_partner = other_id

        # Check for contradictory conclusions
        if review_conclusions and overlap_fraction > _OVERLAP_WARN_THRESHOLD:
            c1 = review_conclusions.get(review_id)
            c2 = review_conclusions.get(other_id)
            if c1 and c2 and _is_contradictory(c1, c2):
                contradictory = True
                contradictory_partner = other_id

    metrics: dict[str, Any] = {
        "insufficient_data": False,
        "max_overlap_fraction": float(max_overlap_fraction),
        "max_overlap_partner": max_overlap_partner,
        "contradictory": contradictory,
        "contradictory_partner": contradictory_partner,
        "n_reviews_with_overlap": sum(1 for _, s in pairs if s),
    }

    if contradictory:
        return DetectorResult(
            module=MODULE,
            severity=Severity.FAIL,
            detail=(
                f"Contradictory conclusions with {contradictory_partner} "
                f"despite {max_overlap_fraction:.0%} study overlap. "
                "Results cannot both be correct."
            ),
            metrics=metrics,
        )

    if max_overlap_fraction > _OVERLAP_WARN_THRESHOLD:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"{max_overlap_fraction:.0%} study overlap with {max_overlap_partner}. "
                "Double-counting may inflate certainty across reviews."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=f"No problematic study overlap detected (max {max_overlap_fraction:.0%}).",
        metrics=metrics,
    )
