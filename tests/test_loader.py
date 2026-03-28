import os
import pandas as pd
import pytest
from metaaudit.loader import (
    load_rda_file,
    detect_data_type,
    split_by_analysis,
    load_all_reviews,
    DataType,
)


PAIRWISE70_DIR = r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data"
SAMPLE_RDA = os.path.join(PAIRWISE70_DIR, "CD000028_pub4_data.rda")


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
    not os.path.exists(SAMPLE_RDA),
    reason="Pairwise70 data not available"
)
def test_load_real_rda():
    review = load_rda_file(SAMPLE_RDA)
    assert review.review_id == "CD000028_pub4_data"
    assert len(review.df) > 0
    assert "Study" in review.df.columns
    assert review.data_type in (DataType.BINARY, DataType.CONTINUOUS, DataType.GIV)


@pytest.mark.skipif(
    not os.path.exists(PAIRWISE70_DIR),
    reason="Pairwise70 data not available"
)
def test_load_all_reviews_sample():
    reviews = load_all_reviews(PAIRWISE70_DIR, max_reviews=5)
    assert len(reviews) == 5
    for r in reviews:
        assert r.review_id is not None
        assert len(r.df) > 0
