from pathlib import Path

from run_audit import resolve_paths


def test_resolve_paths_prefers_repo_relative_pairwise70(tmp_path):
    projects_root = tmp_path / "workspace"
    project_root = projects_root / "MetaAudit"
    pairwise_dir = projects_root / "Projects" / "Pairwise70" / "data"
    pairwise_dir.mkdir(parents=True)

    paths = resolve_paths(project_root=project_root, projects_root=projects_root)

    assert paths["data_dir"] == pairwise_dir.resolve()
    assert paths["output_dir"] == (project_root / "results").resolve()
    assert paths["grade_file"] == (project_root / "data" / "grade_certainty.json").resolve()
