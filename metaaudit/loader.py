"""Load Pairwise70 .rda files into standardised DataFrames."""

from __future__ import annotations

import enum
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import pyreadr


class DataType(enum.Enum):
    BINARY = "binary"
    CONTINUOUS = "continuous"
    GIV = "giv"


BINARY_COLS = {"Experimental.cases", "Experimental.N", "Control.cases", "Control.N"}
CONTINUOUS_COLS = {
    "Experimental.mean", "Experimental.SD", "Experimental.N",
    "Control.mean", "Control.SD", "Control.N",
}
GIV_COLS = {"GIV.Mean", "GIV.SE"}


def detect_data_type(df: pd.DataFrame) -> DataType:
    cols = set(df.columns)
    has_binary = BINARY_COLS.issubset(cols) and df["Experimental.cases"].notna().any()
    has_continuous = CONTINUOUS_COLS.issubset(cols) and df["Experimental.mean"].notna().any()
    has_giv = GIV_COLS.issubset(cols) and df["GIV.Mean"].notna().any()
    if has_binary:
        return DataType.BINARY
    if has_continuous:
        return DataType.CONTINUOUS
    if has_giv:
        return DataType.GIV
    if BINARY_COLS.issubset(cols):
        return DataType.BINARY
    if CONTINUOUS_COLS.issubset(cols):
        return DataType.CONTINUOUS
    return DataType.GIV


@dataclass
class AnalysisGroup:
    """One meta-analysis within a review (one Analysis.number)."""
    df: pd.DataFrame
    analysis_number: int
    data_type: DataType
    review_id: str
    review_doi: Optional[str] = None
    review_title: Optional[str] = None
    outcome: Optional[str] = None
    comparison: Optional[str] = None

    @property
    def k(self) -> int:
        return len(self.df)

    @property
    def ma_id(self) -> str:
        return f"{self.review_id}__A{self.analysis_number}"


@dataclass
class ReviewData:
    """All data from one Cochrane review (.rda file)."""
    review_id: str
    df: pd.DataFrame
    data_type: DataType
    review_doi: Optional[str] = None
    review_title: Optional[str] = None
    analyses: list[AnalysisGroup] = field(default_factory=list)
    study_names: set = field(default_factory=set)


def split_by_analysis(df: pd.DataFrame, review_id: str = "",
                      review_doi: str | None = None,
                      review_title: str | None = None) -> list[AnalysisGroup]:
    groups = []
    if "Analysis.number" not in df.columns:
        dtype = detect_data_type(df)
        outcome = df["Outcome"].iloc[0] if "Outcome" in df.columns else None
        comparison = df["Comparison"].iloc[0] if "Comparison" in df.columns else None
        groups.append(AnalysisGroup(
            df=df, analysis_number=1, data_type=dtype,
            review_id=review_id, review_doi=review_doi,
            review_title=review_title, outcome=outcome,
            comparison=comparison,
        ))
        return groups

    for ana_num, sub_df in df.groupby("Analysis.number"):
        sub_df = sub_df.reset_index(drop=True)
        dtype = detect_data_type(sub_df)
        outcome = sub_df["Outcome"].iloc[0] if "Outcome" in sub_df.columns else None
        comparison = sub_df["Comparison"].iloc[0] if "Comparison" in sub_df.columns else None
        groups.append(AnalysisGroup(
            df=sub_df, analysis_number=int(ana_num), data_type=dtype,
            review_id=review_id, review_doi=review_doi,
            review_title=review_title, outcome=outcome,
            comparison=comparison,
        ))
    return sorted(groups, key=lambda g: g.analysis_number)


def load_rda_file(path: str | Path) -> ReviewData:
    path = Path(path)
    result = pyreadr.read_r(str(path))
    df = list(result.values())[0]
    review_id = path.stem
    data_type = detect_data_type(df)
    review_doi = df["review_doi"].iloc[0] if "review_doi" in df.columns else None
    review_title = df["review_title"].iloc[0] if "review_title" in df.columns else None
    analyses = split_by_analysis(df, review_id, review_doi, review_title)
    # Extract study names once at load time to avoid re-scanning df later
    study_names = set(df["Study"].dropna().unique()) if "Study" in df.columns else set()
    return ReviewData(
        review_id=review_id, df=df, data_type=data_type,
        review_doi=review_doi, review_title=review_title,
        analyses=analyses, study_names=study_names,
    )


def load_all_reviews(data_dir: str | Path,
                     max_reviews: int | None = None) -> list[ReviewData]:
    data_dir = Path(data_dir)
    rda_files = sorted(data_dir.glob("*.rda"))
    if max_reviews is not None:
        rda_files = rda_files[:max_reviews]
    reviews = []
    for f in rda_files:
        try:
            reviews.append(load_rda_file(f))
        except Exception as e:
            print(f"WARNING: Failed to load {f.name}: {e}")
    return reviews
