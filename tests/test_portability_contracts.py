from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "e156-submission" / "config.json"
README_PATH = REPO_ROOT / "README.md"
VALIDATION_PY = REPO_ROOT / "validation" / "cross_validate.py"
VALIDATION_R = REPO_ROOT / "validation" / "r_cross_validation.R"


def test_submission_config_uses_repo_relative_root() -> None:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert payload["path"] == ".."
    assert (CONFIG_PATH.parent / payload["path"]).resolve() == REPO_ROOT.resolve()


def test_release_surface_has_no_hardcoded_metaaudit_root() -> None:
    for path in (CONFIG_PATH, README_PATH, VALIDATION_PY, VALIDATION_R):
        text = path.read_text(encoding="utf-8")
        assert r"C:\MetaAudit" not in text, path
        assert "C:/MetaAudit" not in text, path


def test_validation_surface_has_no_pinned_rscript_install() -> None:
    text = VALIDATION_PY.read_text(encoding="utf-8")
    assert r'RSCRIPT = r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"' not in text
