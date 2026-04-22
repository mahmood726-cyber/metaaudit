"""Tests for metaaudit.config path constants."""

from pathlib import Path

import pytest


def test_config_importable():
    from metaaudit import config  # noqa: F401


def test_root_points_at_repo_root():
    from metaaudit.config import ROOT
    assert isinstance(ROOT, Path)
    assert ROOT.is_dir()
    assert (ROOT / "metaaudit").is_dir()
    assert (ROOT / "pytest.ini").is_file()


def test_derived_paths_live_under_root():
    from metaaudit.config import (
        ROOT,
        RESULTS_DIR,
        DASHBOARD_DIR,
        DASHBOARD_TEMPLATE,
        DASHBOARD_INDEX,
        DASHBOARD_DATA,
        WEBR_VERIFY_HTML,
        PROTOCOL_LOG,
    )
    for p in (
        RESULTS_DIR,
        DASHBOARD_DIR,
        DASHBOARD_TEMPLATE,
        DASHBOARD_INDEX,
        DASHBOARD_DATA,
        WEBR_VERIFY_HTML,
        PROTOCOL_LOG,
    ):
        assert isinstance(p, Path)
        assert ROOT in p.parents or p.parent == ROOT


def test_paths_are_absolute():
    from metaaudit.config import ROOT, RESULTS_DIR, DASHBOARD_DIR
    assert ROOT.is_absolute()
    assert RESULTS_DIR.is_absolute()
    assert DASHBOARD_DIR.is_absolute()


def test_config_has_no_hardcoded_drive_letter():
    """Regression guard: the config source itself must not hardcode C:\\ or
    similar, otherwise we've recreated the defect we're trying to fix."""
    from metaaudit import config
    source = Path(config.__file__).read_text(encoding="utf-8")
    # Allow references inside string *tests* (none expected), but reject
    # drive-letter-prefixed absolute paths in non-comment code.
    import re
    lines = [ln for ln in source.splitlines() if not ln.lstrip().startswith("#")]
    offenders = [ln for ln in lines if re.search(r"[A-Za-z]:[\\/]", ln)]
    assert not offenders, f"Hardcoded drive-letter path in config: {offenders}"
