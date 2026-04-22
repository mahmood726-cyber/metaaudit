"""Path constants for MetaAudit scripts and library code.

All paths are anchored to the repository root via ``ROOT``, so scripts can be
run from any clone location without editing source. Import these constants
instead of hardcoding absolute drive-prefixed paths.
"""

from __future__ import annotations

from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]

RESULTS_DIR: Path = ROOT / "results"
DASHBOARD_DIR: Path = ROOT / "dashboard"

DASHBOARD_TEMPLATE: Path = DASHBOARD_DIR / "index.template.html"
DASHBOARD_INDEX: Path = DASHBOARD_DIR / "index.html"
DASHBOARD_DATA: Path = RESULTS_DIR / "dashboard_data.json"
WEBR_VERIFY_HTML: Path = DASHBOARD_DIR / "webr-verify.html"

PROTOCOL_LOG: Path = ROOT / "protocol-registration-log.md"

__all__ = [
    "ROOT",
    "RESULTS_DIR",
    "DASHBOARD_DIR",
    "DASHBOARD_TEMPLATE",
    "DASHBOARD_INDEX",
    "DASHBOARD_DATA",
    "WEBR_VERIFY_HTML",
    "PROTOCOL_LOG",
]
