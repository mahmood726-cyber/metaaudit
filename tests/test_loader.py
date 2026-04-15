import os
import pandas as pd
import pytest
from pathlib import Path
from metaaudit.loader import (
    load_rda_file,
    detect_data_type,
    split_by_analysis,
    load_all_reviews,
    DataType,
)


def _pairwise70_dir():
    env_data = os.getenv("METAAUDIT_DATA_DIR") or os.getenv("PAIRWISE70_DATA_DIR")
    candidates = []
    if env_data:
        candidates.append(Path(env_data).expanduser())
    project_root = Path(__file__).resolve().parents[1]
    candidates.extend([
        project_root.parent / "Projects" / "Pairwise70" / "data",
        project_root.parent / "Models" / "Pairwise70" / "data",
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


PAIRWISE70_DIR = _pairwise70_dir()
SAMPLE_RDA = (PAIRWISE70_DIR / "CD000028_pub4_data.rda") if PAIRWISE70_DIR else None


def test_detect_binary(binary_study_data):
    assert detect_data_type(binary_study_data) == DataType.BINARY


def test_detect_continuous(continuous_study_data):
    assert detect_data_type(continuous_study_data) == DataType.CONTINUOUS


def test_split_by_analysis(multi_analysis_data):
    groups = split_by_analysis(multi_analysis_data)
    assert len(groups) == 2
    assert len(groups[0].df) == 5
    assert len(groups[1].df) == 3
    assert groups[0].analysis_number == 1
    assert groups[1].analysis_number == 2


@pytest.mark.skipif(
    SAMPLE_RDA is None or not SAMPLE_RDA.exists(),
    reason="Pairwise70 data not available"
)
def test_load_real_rda():
    review = load_rda_file(SAMPLE_RDA)
    assert review.review_id == "CD000028_pub4_data"
    assert len(review.df) > 0
    assert "Study" in review.df.columns
    assert review.data_type in (DataType.BINARY, DataType.CONTINUOUS, DataType.GIV)


@pytest.mark.skipif(
    PAIRWISE70_DIR is None or not PAIRWISE70_DIR.exists(),
    reason="Pairwise70 data not available"
)
def test_load_all_reviews_sample():
    reviews = load_all_reviews(PAIRWISE70_DIR, max_reviews=5)
    assert len(reviews) == 5
    for r in reviews:
        assert r.review_id is not None
        assert len(r.df) > 0
