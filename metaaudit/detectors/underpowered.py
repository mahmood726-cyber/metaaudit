"""Detector: Under-powered meta-analysis (k and OIS)."""

from __future__ import annotations

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import DetectorResult, Severity

MODULE = "underpowered"

_K_FAIL = 3      # k < 3 and significant → FAIL
_K_WARN = 5      # k < 5 → WARN
_OIS_MIN = 1600  # Optimal information size threshold (events or participants)


def detect_underpowered(rma: RecomputedMA, total_n: int) -> DetectorResult:
    """Detect underpowered meta-analyses.

    Rules:
    - FAIL if k < 3 and significant (strong claim from very few studies)
    - WARN if k < 5 (including k<3 non-significant)
    - WARN if total_n < OIS (1600) and significant
    - PASS otherwise
    """
    metrics = {
        "insufficient_data": False,
        "k": rma.k,
        "total_n": total_n,
        "significant": rma.significant,
    }

    # k-based check
    if rma.k < _K_FAIL:
        if rma.significant:
            return DetectorResult(
                module=MODULE,
                severity=Severity.FAIL,
                detail=(
                    f"Only k={rma.k} studies but result is significant. "
                    "Pooled estimates from <3 studies are highly unreliable."
                ),
                metrics=metrics,
            )
        else:
            return DetectorResult(
                module=MODULE,
                severity=Severity.WARN,
                detail=(
                    f"Only k={rma.k} studies. "
                    "Very few studies; conclusions must be treated with caution."
                ),
                metrics=metrics,
            )

    if rma.k < _K_WARN:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"k={rma.k} studies — below recommended minimum of {_K_WARN}. "
                "Heterogeneity estimates may be unstable."
            ),
            metrics=metrics,
        )

    # OIS check
    if total_n < _OIS_MIN and rma.significant:
        return DetectorResult(
            module=MODULE,
            severity=Severity.WARN,
            detail=(
                f"Total N={total_n} is below the optimal information size ({_OIS_MIN}). "
                "Result may be false-positive due to insufficient cumulative information."
            ),
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE,
        severity=Severity.PASS,
        detail=(
            f"k={rma.k} studies, total N={total_n} — adequate power indicators."
        ),
        metrics=metrics,
    )
