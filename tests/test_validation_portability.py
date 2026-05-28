from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "validation" / "cross_validate.py"
SPEC = importlib.util.spec_from_file_location("metaaudit_cross_validate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_resolve_rscript_path_prefers_env_override(monkeypatch, tmp_path) -> None:
    fake_rscript = tmp_path / "Rscript.exe"
    fake_rscript.write_text("", encoding="utf-8")
    monkeypatch.setenv("RSCRIPT_PATH", str(fake_rscript))
    monkeypatch.delenv("RSCRIPT", raising=False)
    monkeypatch.setattr(MODULE.shutil, "which", lambda _: None)
    assert MODULE.resolve_rscript_path() == fake_rscript.resolve()


def test_resolve_rscript_path_uses_path_lookup(monkeypatch, tmp_path) -> None:
    fake_rscript = tmp_path / "Rscript.exe"
    fake_rscript.write_text("", encoding="utf-8")
    monkeypatch.delenv("RSCRIPT_PATH", raising=False)
    monkeypatch.delenv("RSCRIPT", raising=False)
    monkeypatch.setattr(MODULE.shutil, "which", lambda _: str(fake_rscript))
    assert MODULE.resolve_rscript_path() == fake_rscript.resolve()
