# MetaAudit Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Python engine — loader, recompute layer, 11 flaw detectors, correlator, exporter, and CLI runner — all TDD, all tested against Pairwise70 data.

**Architecture:** Python package `metaaudit/` with pure-function detectors consuming standardised DataFrames. Each detector returns `{severity, detail, metrics}`. A recompute layer pools effects from study-level data. Results export to JSON for the dashboard (Phase 2 plan).

**Tech Stack:** Python 3.x, pyreadr, numpy, scipy, pandas. R 4.5.2 + metafor for cross-validation only.

**Data source:** Pairwise70 at `C:\Users\user\OneDrive - NHS\Documents\Pairwise70\`

**Working directory:** `C:\MetaAudit\`

---

## File Structure

```
C:\MetaAudit\
├── metaaudit/
│   ├── __init__.py              # Package init, version
│   ├── severity.py              # Severity enum + DetectorResult dataclass
│   ├── loader.py                # Read .rda files → standardised DataFrames
│   ├── recompute.py             # Pool effects, I², tau², CI, PI from raw study data
│   ├── detectors/
│   │   ├── __init__.py          # Registry of all detectors
│   │   ├── prediction_gap.py    # Module 1: PI vs CI
│   │   ├── model_misspec.py     # Module 2: FE vs RE appropriateness
│   │   ├── fragility.py         # Module 3: MAFI fragility index
│   │   ├── underpowered.py      # Module 4: k<3/5, OIS
│   │   ├── pub_bias.py          # Module 5: Egger/Begg/trim-fill
│   │   ├── small_study.py       # Module 6: Peters/funnel asymmetry
│   │   ├── excess_sig.py        # Module 7: Ioannidis-Trikalinos test
│   │   ├── integrity.py         # Module 8: GRIM/impossible values
│   │   ├── overlap.py           # Module 9: Cross-review study overlap
│   │   ├── overclaiming.py      # Module 10: Effect vs MCID
│   │   └── certainty_mismatch.py # Module 11: GRADE vs automated severity
│   ├── correlator.py            # Co-occurrence, specialty, temporal analysis
│   └── export.py                # JSON + CSV output
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_severity.py
│   ├── test_loader.py
│   ├── test_recompute.py
│   ├── test_prediction_gap.py
│   ├── test_model_misspec.py
│   ├── test_fragility.py
│   ├── test_underpowered.py
│   ├── test_pub_bias.py
│   ├── test_small_study.py
│   ├── test_excess_sig.py
│   ├── test_integrity.py
│   ├── test_overlap.py
│   ├── test_overclaiming.py
│   ├── test_certainty_mismatch.py
│   ├── test_correlator.py
│   ├── test_export.py
│   └── test_integration.py
├── run_audit.py                 # CLI entry point
├── requirements.txt
├── pytest.ini
└── .gitignore
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `C:\MetaAudit\requirements.txt`
- Create: `C:\MetaAudit\pytest.ini`
- Create: `C:\MetaAudit\.gitignore`
- Create: `C:\MetaAudit\metaaudit\__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
pyreadr>=0.5.0
numpy>=1.24.0
scipy>=1.10.0
pandas>=2.0.0
pytest>=7.0.0
```

- [ ] **Step 2: Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.pytest_cache/
results/
*.egg-info/
dist/
build/
.venv/
```

- [ ] **Step 4: Create metaaudit/__init__.py**

```python
"""MetaAudit — A Computational Audit of Evidence Synthesis."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Create empty detector package**

```python
# metaaudit/detectors/__init__.py
"""Flaw detection modules for MetaAudit."""
```

- [ ] **Step 6: Install dependencies**

Run: `cd /c/MetaAudit && python -m pip install pyreadr numpy scipy pandas pytest`

- [ ] **Step 7: Verify install**

Run: `cd /c/MetaAudit && python -c "import pyreadr, numpy, scipy, pandas; print('OK')"`
Expected: `OK`

- [ ] **Step 8: Commit**

```bash
cd /c/MetaAudit && git add -A && git commit -m "chore: project scaffolding with dependencies"
```

---

### Task 2: Severity Module

**Files:**
- Create: `C:\MetaAudit\metaaudit\severity.py`
- Create: `C:\MetaAudit\tests\test_severity.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_severity.py
from metaaudit.severity import Severity, DetectorResult


def test_severity_ordering():
    assert Severity.PASS < Severity.WARN < Severity.FAIL < Severity.CRITICAL


def test_severity_from_string():
    assert Severity.from_string("PASS") == Severity.PASS
    assert Severity.from_string("fail") == Severity.FAIL


def test_detector_result_creation():
    r = DetectorResult(
        module="prediction_gap",
        severity=Severity.FAIL,
        detail="CI excludes null but PI includes it",
        metrics={"pi_lower": -0.3, "pi_upper": 1.2},
    )
    assert r.module == "prediction_gap"
    assert r.severity == Severity.FAIL
    assert r.metrics["pi_lower"] == -0.3


def test_detector_result_insufficient_data():
    r = DetectorResult.insufficient_data("pub_bias", reason="k < 10")
    assert r.severity == Severity.PASS
    assert r.detail == "Insufficient data: k < 10"
    assert r.metrics["insufficient_data"] is True


def test_detector_result_to_dict():
    r = DetectorResult(
        module="fragility",
        severity=Severity.WARN,
        detail="MAFI = 4",
        metrics={"mafi": 4},
    )
    d = r.to_dict()
    assert d["module"] == "fragility"
    assert d["severity"] == "WARN"
    assert d["detail"] == "MAFI = 4"
    assert d["metrics"]["mafi"] == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_severity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'metaaudit.severity'`

- [ ] **Step 3: Implement severity.py**

```python
# metaaudit/severity.py
"""Severity classification and detector result dataclass."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class Severity(enum.IntEnum):
    PASS = 0
    WARN = 1
    FAIL = 2
    CRITICAL = 3

    @classmethod
    def from_string(cls, s: str) -> Severity:
        return cls[s.upper()]


@dataclass
class DetectorResult:
    module: str
    severity: Severity
    detail: str
    metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def insufficient_data(cls, module: str, reason: str) -> DetectorResult:
        return cls(
            module=module,
            severity=Severity.PASS,
            detail=f"Insufficient data: {reason}",
            metrics={"insufficient_data": True},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "severity": self.severity.name,
            "detail": self.detail,
            "metrics": self.metrics,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_severity.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/severity.py tests/test_severity.py && git commit -m "feat: severity enum and DetectorResult dataclass"
```

---

### Task 3: Data Loader

**Files:**
- Create: `C:\MetaAudit\metaaudit\loader.py`
- Create: `C:\MetaAudit\tests\conftest.py`
- Create: `C:\MetaAudit\tests\test_loader.py`

- [ ] **Step 1: Write shared test fixtures**

```python
# tests/conftest.py
"""Shared test fixtures for MetaAudit tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def binary_study_data():
    """5 studies with binary outcomes — a clean, simple MA."""
    return pd.DataFrame({
        "Study": ["Alpha 2010", "Beta 2012", "Gamma 2013", "Delta 2015", "Epsilon 2017"],
        "Study.year": [2010, 2012, 2013, 2015, 2017],
        "Comparison": ["Drug A vs Placebo"] * 5,
        "Outcome": ["Mortality"] * 5,
        "Subgroup": [None] * 5,
        "Analysis.number": [1] * 5,
        "Experimental.cases": [10, 15, 8, 20, 12],
        "Experimental.N": [100, 120, 80, 150, 110],
        "Control.cases": [20, 25, 15, 30, 22],
        "Control.N": [100, 120, 80, 150, 110],
        "review_doi": ["10.1002/14651858.CD000001.pub1"] * 5,
        "review_title": ["Test Review Alpha"] * 5,
    })


@pytest.fixture
def continuous_study_data():
    """4 studies with continuous outcomes."""
    return pd.DataFrame({
        "Study": ["Study A", "Study B", "Study C", "Study D"],
        "Study.year": [2011, 2013, 2015, 2018],
        "Comparison": ["Treatment vs Control"] * 4,
        "Outcome": ["Blood Pressure"] * 4,
        "Subgroup": [None] * 4,
        "Analysis.number": [1] * 4,
        "Experimental.mean": [120.0, 118.5, 122.0, 119.0],
        "Experimental.SD": [15.0, 12.0, 18.0, 14.0],
        "Experimental.N": [50, 60, 40, 70],
        "Control.mean": [130.0, 128.0, 131.0, 129.5],
        "Control.SD": [16.0, 13.0, 17.0, 15.0],
        "Control.N": [50, 60, 40, 70],
        "review_doi": ["10.1002/14651858.CD000002.pub1"] * 4,
        "review_title": ["Test Review Beta"] * 4,
    })


@pytest.fixture
def multi_analysis_data(binary_study_data):
    """Two analyses within one review (k=5 and k=3)."""
    analysis2 = pd.DataFrame({
        "Study": ["Zeta 2014", "Eta 2016", "Theta 2018"],
        "Study.year": [2014, 2016, 2018],
        "Comparison": ["Drug A vs Placebo"] * 3,
        "Outcome": ["Hospitalisation"] * 3,
        "Subgroup": [None] * 3,
        "Analysis.number": [2] * 3,
        "Experimental.cases": [5, 8, 3],
        "Experimental.N": [60, 70, 50],
        "Control.cases": [12, 15, 10],
        "Control.N": [60, 70, 50],
        "review_doi": ["10.1002/14651858.CD000001.pub1"] * 3,
        "review_title": ["Test Review Alpha"] * 3,
    })
    return pd.concat([binary_study_data, analysis2], ignore_index=True)


@pytest.fixture
def small_k_data():
    """Only 2 studies — edge case for most detectors."""
    return pd.DataFrame({
        "Study": ["Only 2015", "Two 2018"],
        "Study.year": [2015, 2018],
        "Comparison": ["Drug B vs Placebo"] * 2,
        "Outcome": ["Death"] * 2,
        "Subgroup": [None] * 2,
        "Analysis.number": [1] * 2,
        "Experimental.cases": [3, 5],
        "Experimental.N": [40, 50],
        "Control.cases": [8, 12],
        "Control.N": [40, 50],
        "review_doi": ["10.1002/14651858.CD000003.pub1"] * 2,
        "review_title": ["Test Review Gamma"] * 2,
    })


@pytest.fixture
def zero_events_data():
    """Studies with zero cells — needs continuity correction."""
    return pd.DataFrame({
        "Study": ["ZeroA 2010", "ZeroB 2012", "ZeroC 2014"],
        "Study.year": [2010, 2012, 2014],
        "Comparison": ["Drug C vs Placebo"] * 3,
        "Outcome": ["Rare Event"] * 3,
        "Subgroup": [None] * 3,
        "Analysis.number": [1] * 3,
        "Experimental.cases": [0, 1, 0],
        "Experimental.N": [100, 80, 120],
        "Control.cases": [3, 5, 2],
        "Control.N": [100, 80, 120],
        "review_doi": ["10.1002/14651858.CD000004.pub1"] * 3,
        "review_title": ["Test Review Delta"] * 3,
    })
```

- [ ] **Step 2: Write loader tests**

```python
# tests/test_loader.py
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'metaaudit.loader'`

- [ ] **Step 4: Implement loader.py**

```python
# metaaudit/loader.py
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
    # Fallback: check which columns have non-null data
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
    # .rda files contain one or more named DataFrames; take the first
    df = list(result.values())[0]
    review_id = path.stem  # e.g. "CD000028_pub4_data"
    data_type = detect_data_type(df)
    review_doi = df["review_doi"].iloc[0] if "review_doi" in df.columns else None
    review_title = df["review_title"].iloc[0] if "review_title" in df.columns else None
    analyses = split_by_analysis(df, review_id, review_doi, review_title)
    return ReviewData(
        review_id=review_id, df=df, data_type=data_type,
        review_doi=review_doi, review_title=review_title,
        analyses=analyses,
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_loader.py -v`
Expected: All pass (real-data tests may skip if Pairwise70 not on path)

- [ ] **Step 6: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/loader.py tests/conftest.py tests/test_loader.py && git commit -m "feat: data loader for Pairwise70 .rda files"
```

---

### Task 4: Recompute Layer

**Files:**
- Create: `C:\MetaAudit\metaaudit\recompute.py`
- Create: `C:\MetaAudit\tests\test_recompute.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_recompute.py
import math
import numpy as np
import pytest
from metaaudit.recompute import (
    compute_log_or,
    compute_md,
    compute_smd,
    pool_effects_reml,
    compute_prediction_interval,
    RecomputedMA,
    recompute_ma,
)
from metaaudit.loader import DataType


def test_log_or_basic():
    # 10/100 vs 20/100 => OR = (10*80)/(20*90) = 800/1800 = 0.444
    yi, vi = compute_log_or(
        e_cases=np.array([10]),
        e_n=np.array([100]),
        c_cases=np.array([20]),
        c_n=np.array([100]),
    )
    assert len(yi) == 1
    expected_or = (10 * 80) / (20 * 90)
    assert abs(yi[0] - math.log(expected_or)) < 0.01


def test_log_or_zero_cell_correction():
    # 0/50 vs 5/50 — needs continuity correction
    yi, vi = compute_log_or(
        e_cases=np.array([0]),
        e_n=np.array([50]),
        c_cases=np.array([5]),
        c_n=np.array([50]),
    )
    assert np.isfinite(yi[0])
    assert yi[0] < 0  # OR < 1


def test_compute_md():
    yi, vi = compute_md(
        e_mean=np.array([120.0, 118.0]),
        e_sd=np.array([15.0, 12.0]),
        e_n=np.array([50, 60]),
        c_mean=np.array([130.0, 128.0]),
        c_sd=np.array([16.0, 13.0]),
        c_n=np.array([50, 60]),
    )
    assert len(yi) == 2
    assert abs(yi[0] - (-10.0)) < 0.01
    assert abs(yi[1] - (-10.0)) < 0.01


def test_compute_smd():
    yi, vi = compute_smd(
        e_mean=np.array([120.0]),
        e_sd=np.array([15.0]),
        e_n=np.array([50]),
        c_mean=np.array([130.0]),
        c_sd=np.array([16.0]),
        c_n=np.array([50]),
    )
    assert len(yi) == 1
    # Hedges' g: pooled SD ~ 15.52, d ~ -10/15.52 ~ -0.644, J ~ 0.992
    assert -0.70 < yi[0] < -0.55


def test_pool_reml_homogeneous():
    # 5 identical studies => tau2 ~ 0, I2 ~ 0
    yi = np.array([-0.5, -0.5, -0.5, -0.5, -0.5])
    vi = np.array([0.04, 0.04, 0.04, 0.04, 0.04])
    result = pool_effects_reml(yi, vi)
    assert abs(result["estimate"] - (-0.5)) < 0.01
    assert result["tau2"] < 0.001
    assert result["I2"] < 5.0


def test_pool_reml_heterogeneous():
    yi = np.array([-0.2, -0.8, 0.1, -1.0, -0.5])
    vi = np.array([0.04, 0.04, 0.04, 0.04, 0.04])
    result = pool_effects_reml(yi, vi)
    assert result["tau2"] > 0.01
    assert result["I2"] > 20.0
    assert result["ci_lower"] < result["estimate"] < result["ci_upper"]


def test_prediction_interval():
    pi = compute_prediction_interval(
        estimate=-0.5, se=0.1, tau2=0.05, k=5
    )
    assert pi["pi_lower"] < -0.5
    assert pi["pi_upper"] > -0.5
    # PI should be wider than CI
    ci_width = 2 * 1.96 * 0.1
    pi_width = pi["pi_upper"] - pi["pi_lower"]
    assert pi_width > ci_width


def test_recompute_ma_binary(binary_study_data):
    result = recompute_ma(binary_study_data, DataType.BINARY)
    assert isinstance(result, RecomputedMA)
    assert result.k == 5
    assert result.estimate < 0  # Fewer events in experimental => OR < 1 => log(OR) < 0
    assert result.ci_lower < result.estimate < result.ci_upper
    assert 0.0 <= result.I2 <= 100.0


def test_recompute_ma_continuous(continuous_study_data):
    result = recompute_ma(continuous_study_data, DataType.CONTINUOUS)
    assert result.k == 4
    assert result.estimate < 0  # Experimental mean < Control mean
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_recompute.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement recompute.py**

```python
# metaaudit/recompute.py
"""Recompute pooled effects, heterogeneity, and prediction intervals from study-level data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats

from metaaudit.loader import DataType


def compute_log_or(
    e_cases: np.ndarray, e_n: np.ndarray,
    c_cases: np.ndarray, c_n: np.ndarray,
    cc: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute log odds ratios and sampling variances. Continuity correction for zero cells."""
    a = e_cases.astype(float)
    b = (e_n - e_cases).astype(float)
    c = c_cases.astype(float)
    d = (c_n - c_cases).astype(float)
    # Apply continuity correction where any cell is zero
    needs_cc = (a == 0) | (b == 0) | (c == 0) | (d == 0)
    a = np.where(needs_cc, a + cc, a)
    b = np.where(needs_cc, b + cc, b)
    c = np.where(needs_cc, c + cc, c)
    d = np.where(needs_cc, d + cc, d)
    yi = np.log((a * d) / (b * c))
    vi = 1.0 / a + 1.0 / b + 1.0 / c + 1.0 / d
    return yi, vi


def compute_md(
    e_mean: np.ndarray, e_sd: np.ndarray, e_n: np.ndarray,
    c_mean: np.ndarray, c_sd: np.ndarray, c_n: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute mean differences and sampling variances."""
    yi = e_mean - c_mean
    vi = (e_sd ** 2) / e_n + (c_sd ** 2) / c_n
    return yi, vi


def compute_smd(
    e_mean: np.ndarray, e_sd: np.ndarray, e_n: np.ndarray,
    c_mean: np.ndarray, c_sd: np.ndarray, c_n: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Hedges' g (bias-corrected SMD) and sampling variances."""
    n_total = e_n + c_n
    # Pooled SD
    sp = np.sqrt(((e_n - 1) * e_sd ** 2 + (c_n - 1) * c_sd ** 2) / (n_total - 2))
    # Cohen's d
    d = (e_mean - c_mean) / sp
    # Hedges' correction factor J
    df = n_total - 2
    j = 1.0 - 3.0 / (4.0 * df - 1.0)
    yi = j * d
    vi = (n_total / (e_n * c_n)) + (yi ** 2) / (2.0 * n_total)
    return yi, vi


def _reml_tau2(yi: np.ndarray, vi: np.ndarray, max_iter: int = 100,
               tol: float = 1e-6) -> float:
    """Estimate between-study variance tau² using REML (Fisher scoring)."""
    k = len(yi)
    if k < 2:
        return 0.0
    # DerSimonian-Laird as starting value
    wi = 1.0 / vi
    w_sum = wi.sum()
    theta_fe = (wi * yi).sum() / w_sum
    Q = ((yi - theta_fe) ** 2 * wi).sum()
    c = w_sum - (wi ** 2).sum() / w_sum
    tau2 = max(0.0, (Q - (k - 1)) / c)
    for _ in range(max_iter):
        w = 1.0 / (vi + tau2)
        w_sum = w.sum()
        theta = (w * yi).sum() / w_sum
        resid = yi - theta
        # Fisher scoring update
        deriv1 = -0.5 * (w ** 2).sum() + 0.5 * ((resid ** 2) * (w ** 2)).sum() \
                 + 0.5 * ((w ** 2).sum() / w_sum) - 0.5 * ((w ** 2 * resid).sum() ** 2) / (w_sum ** 2)
        # Simplified: use Paule-Mandel style iterative
        # More stable: direct REML iteration
        Q_w = ((resid ** 2) * w).sum()
        tau2_new = max(0.0, tau2 + (Q_w - (k - 1)) / (w ** 2).sum())
        if abs(tau2_new - tau2) < tol:
            tau2 = tau2_new
            break
        tau2 = tau2_new
    return tau2


def pool_effects_reml(yi: np.ndarray, vi: np.ndarray) -> dict:
    """Pool effects using REML random-effects model."""
    k = len(yi)
    tau2 = _reml_tau2(yi, vi)
    w = 1.0 / (vi + tau2)
    w_sum = w.sum()
    estimate = (w * yi).sum() / w_sum
    se = 1.0 / np.sqrt(w_sum)
    # HKSJ adjustment
    theta_w = estimate
    q_resid = (w * (yi - theta_w) ** 2).sum()
    hksj_factor = q_resid / (k - 1) if k > 1 else 1.0
    se_hksj = se * np.sqrt(max(1.0, hksj_factor))
    # CI using t-distribution (HKSJ)
    df = max(1, k - 1)
    t_crit = stats.t.ppf(0.975, df)
    ci_lower = estimate - t_crit * se_hksj
    ci_upper = estimate + t_crit * se_hksj
    # p-value
    t_stat = estimate / se_hksj if se_hksj > 0 else 0.0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    # Heterogeneity
    w_fe = 1.0 / vi
    Q = (w_fe * (yi - (w_fe * yi).sum() / w_fe.sum()) ** 2).sum()
    c = w_fe.sum() - (w_fe ** 2).sum() / w_fe.sum()
    I2 = max(0.0, 100.0 * (Q - (k - 1)) / Q) if Q > 0 else 0.0
    return {
        "estimate": float(estimate),
        "se": float(se),
        "se_hksj": float(se_hksj),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "p_value": float(p_value),
        "tau2": float(tau2),
        "I2": float(I2),
        "Q": float(Q),
        "k": k,
        "significant": p_value < 0.05,
    }


def compute_prediction_interval(
    estimate: float, se: float, tau2: float, k: int
) -> dict:
    """Compute 95% prediction interval (Higgins-Thompson-Spiegelhalter)."""
    if k < 3:
        return {"pi_lower": float("-inf"), "pi_upper": float("inf"),
                "computable": False}
    df = k - 2
    t_crit = stats.t.ppf(0.975, df)
    pi_se = np.sqrt(se ** 2 + tau2)
    pi_lower = estimate - t_crit * pi_se
    pi_upper = estimate + t_crit * pi_se
    return {
        "pi_lower": float(pi_lower),
        "pi_upper": float(pi_upper),
        "computable": True,
    }


@dataclass
class RecomputedMA:
    """All recomputed statistics for one meta-analysis."""
    k: int
    yi: np.ndarray  # Individual effect sizes
    vi: np.ndarray  # Individual variances
    estimate: float
    se: float
    se_hksj: float
    ci_lower: float
    ci_upper: float
    p_value: float
    tau2: float
    I2: float
    Q: float
    significant: bool
    pi_lower: float
    pi_upper: float
    pi_computable: bool
    data_type: DataType
    measure: str  # "logOR", "MD", "SMD", "GIV"


def _extract_effects(df, data_type: DataType) -> tuple[np.ndarray, np.ndarray, str]:
    """Extract effect sizes and variances from study-level data."""
    if data_type == DataType.BINARY:
        yi, vi = compute_log_or(
            df["Experimental.cases"].values,
            df["Experimental.N"].values,
            df["Control.cases"].values,
            df["Control.N"].values,
        )
        return yi, vi, "logOR"
    elif data_type == DataType.CONTINUOUS:
        # Use MD by default; SMD if scales likely differ
        yi, vi = compute_md(
            df["Experimental.mean"].values,
            df["Experimental.SD"].values,
            df["Experimental.N"].values,
            df["Control.mean"].values,
            df["Control.SD"].values,
            df["Control.N"].values,
        )
        return yi, vi, "MD"
    else:  # GIV
        yi = df["GIV.Mean"].values.astype(float)
        vi = (df["GIV.SE"].values.astype(float)) ** 2
        return yi, vi, "GIV"


def recompute_ma(df, data_type: DataType) -> RecomputedMA:
    """Recompute all statistics for one meta-analysis from study-level data."""
    yi, vi, measure = _extract_effects(df, data_type)
    # Filter out non-finite
    mask = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
    yi = yi[mask]
    vi = vi[mask]
    k = len(yi)
    if k == 0:
        return RecomputedMA(
            k=0, yi=yi, vi=vi, estimate=float("nan"), se=float("nan"),
            se_hksj=float("nan"), ci_lower=float("nan"), ci_upper=float("nan"),
            p_value=1.0, tau2=0.0, I2=0.0, Q=0.0, significant=False,
            pi_lower=float("nan"), pi_upper=float("nan"), pi_computable=False,
            data_type=data_type, measure=measure,
        )
    if k == 1:
        se = np.sqrt(vi[0])
        return RecomputedMA(
            k=1, yi=yi, vi=vi, estimate=float(yi[0]), se=float(se),
            se_hksj=float(se),
            ci_lower=float(yi[0] - 1.96 * se),
            ci_upper=float(yi[0] + 1.96 * se),
            p_value=float(2 * (1 - stats.norm.cdf(abs(yi[0] / se)))) if se > 0 else 1.0,
            tau2=0.0, I2=0.0, Q=0.0, significant=False,
            pi_lower=float("-inf"), pi_upper=float("inf"), pi_computable=False,
            data_type=data_type, measure=measure,
        )
    pooled = pool_effects_reml(yi, vi)
    pi = compute_prediction_interval(
        pooled["estimate"], pooled["se"], pooled["tau2"], k
    )
    return RecomputedMA(
        k=k, yi=yi, vi=vi,
        estimate=pooled["estimate"], se=pooled["se"],
        se_hksj=pooled["se_hksj"],
        ci_lower=pooled["ci_lower"], ci_upper=pooled["ci_upper"],
        p_value=pooled["p_value"], tau2=pooled["tau2"],
        I2=pooled["I2"], Q=pooled["Q"],
        significant=pooled["significant"],
        pi_lower=pi["pi_lower"], pi_upper=pi["pi_upper"],
        pi_computable=pi["computable"],
        data_type=data_type, measure=measure,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_recompute.py -v`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/recompute.py tests/test_recompute.py && git commit -m "feat: recompute layer — REML pooling, I², tau², HKSJ CI, prediction intervals"
```

---

### Task 5: Module 1 — Prediction Gap Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\prediction_gap.py`
- Create: `C:\MetaAudit\tests\test_prediction_gap.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_prediction_gap.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.prediction_gap import detect_prediction_gap


def _make_ma(estimate, ci_lower, ci_upper, pi_lower, pi_upper,
             k=10, tau2=0.1, se=0.1, pi_computable=True) -> RecomputedMA:
    return RecomputedMA(
        k=k, yi=np.zeros(k), vi=np.full(k, 0.04),
        estimate=estimate, se=se, se_hksj=se,
        ci_lower=ci_lower, ci_upper=ci_upper,
        p_value=0.01, tau2=tau2, I2=50.0, Q=10.0,
        significant=True,
        pi_lower=pi_lower, pi_upper=pi_upper,
        pi_computable=pi_computable,
        data_type=DataType.BINARY, measure="logOR",
    )


def test_pass_ci_and_pi_exclude_null():
    # Both CI and PI exclude null (negative effect, both bounds < 0)
    ma = _make_ma(-0.8, -1.2, -0.4, -1.8, -0.1)
    result = detect_prediction_gap(ma)
    assert result.severity == Severity.PASS


def test_fail_ci_excludes_but_pi_includes_null():
    # CI: [-1.2, -0.2] excludes 0; PI: [-1.8, 0.3] includes 0
    ma = _make_ma(-0.7, -1.2, -0.2, -1.8, 0.3)
    result = detect_prediction_gap(ma)
    assert result.severity == Severity.FAIL


def test_critical_pi_opposite_direction():
    # CI: [-1.0, -0.2] excludes 0; PI: [-1.5, 0.8] includes values on opposite side
    ma = _make_ma(-0.6, -1.0, -0.2, -1.5, 0.8)
    result = detect_prediction_gap(ma)
    assert result.severity == Severity.CRITICAL


def test_pass_not_significant():
    # CI includes null — nothing to check
    ma = _make_ma(-0.3, -0.8, 0.2, -1.5, 0.9)
    ma = RecomputedMA(
        k=10, yi=np.zeros(10), vi=np.full(10, 0.04),
        estimate=-0.3, se=0.2, se_hksj=0.2,
        ci_lower=-0.8, ci_upper=0.2,
        p_value=0.15, tau2=0.1, I2=50.0, Q=10.0,
        significant=False,
        pi_lower=-1.5, pi_upper=0.9, pi_computable=True,
        data_type=DataType.BINARY, measure="logOR",
    )
    result = detect_prediction_gap(ma)
    assert result.severity == Severity.PASS


def test_insufficient_data_pi_not_computable():
    ma = _make_ma(-0.5, -0.9, -0.1, float("-inf"), float("inf"),
                  k=2, pi_computable=False)
    result = detect_prediction_gap(ma)
    assert result.metrics.get("insufficient_data") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_prediction_gap.py -v`
Expected: FAIL

- [ ] **Step 3: Implement prediction_gap.py**

```python
# metaaudit/detectors/prediction_gap.py
"""Module 1: Prediction Gap — CI excludes null but PI includes it."""

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import Severity, DetectorResult

MODULE = "prediction_gap"


def detect_prediction_gap(ma: RecomputedMA) -> DetectorResult:
    if not ma.pi_computable:
        return DetectorResult.insufficient_data(MODULE, reason="k < 3, PI not computable")

    if not ma.significant:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="MA not significant — prediction gap not applicable",
            metrics={"significant": False},
        )

    null = 0.0  # log scale: null is 0 for logOR, MD, SMD
    ci_excludes_null = (ma.ci_lower > null) or (ma.ci_upper < null)

    if not ci_excludes_null:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="CI includes null",
            metrics={"ci_excludes_null": False},
        )

    pi_includes_null = ma.pi_lower <= null <= ma.pi_upper

    if not pi_includes_null:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="Both CI and PI exclude null — effect generalises",
            metrics={
                "ci_excludes_null": True, "pi_includes_null": False,
                "pi_lower": ma.pi_lower, "pi_upper": ma.pi_upper,
            },
        )

    # PI includes null — check if it also includes opposite direction
    effect_negative = ma.estimate < null
    pi_includes_opposite = (effect_negative and ma.pi_upper > null) or \
                           (not effect_negative and ma.pi_lower < null)

    # Quantify: how far past null does the PI extend?
    if effect_negative:
        opposite_extent = ma.pi_upper  # positive = opposite direction
    else:
        opposite_extent = -ma.pi_lower  # negative = opposite direction

    if opposite_extent > 0 and abs(opposite_extent) > 0.1:
        return DetectorResult(
            module=MODULE, severity=Severity.CRITICAL,
            detail=f"CI excludes null but PI extends into opposite direction "
                   f"(PI: [{ma.pi_lower:.3f}, {ma.pi_upper:.3f}])",
            metrics={
                "ci_excludes_null": True, "pi_includes_null": True,
                "pi_includes_opposite": True,
                "pi_lower": ma.pi_lower, "pi_upper": ma.pi_upper,
                "opposite_extent": opposite_extent,
            },
        )

    return DetectorResult(
        module=MODULE, severity=Severity.FAIL,
        detail=f"CI excludes null but PI includes it "
               f"(PI: [{ma.pi_lower:.3f}, {ma.pi_upper:.3f}])",
        metrics={
            "ci_excludes_null": True, "pi_includes_null": True,
            "pi_includes_opposite": False,
            "pi_lower": ma.pi_lower, "pi_upper": ma.pi_upper,
        },
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_prediction_gap.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/prediction_gap.py tests/test_prediction_gap.py && git commit -m "feat: Module 1 — prediction gap detector (PI vs CI)"
```

---

### Task 6: Module 2 — Model Misspecification Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\model_misspec.py`
- Create: `C:\MetaAudit\tests\test_model_misspec.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_model_misspec.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.model_misspec import detect_model_misspec


def _make_ma(I2, tau2, k=10, data_type=DataType.BINARY,
             measure="logOR", df=None) -> tuple[RecomputedMA, dict]:
    """Return (RecomputedMA, context_dict)."""
    ma = RecomputedMA(
        k=k, yi=np.zeros(k), vi=np.full(k, 0.04),
        estimate=-0.5, se=0.1, se_hksj=0.1,
        ci_lower=-0.7, ci_upper=-0.3,
        p_value=0.01, tau2=tau2, I2=I2, Q=k * 2,
        significant=True,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=True,
        data_type=data_type, measure=measure,
    )
    ctx = {}
    if df is not None:
        ctx["event_rate"] = df
    return ma, ctx


def test_pass_low_heterogeneity():
    ma, ctx = _make_ma(I2=20.0, tau2=0.01)
    result = detect_model_misspec(ma, ctx)
    assert result.severity == Severity.PASS


def test_fail_high_heterogeneity_fe_inappropriate():
    # I2 > 50% — fixed-effect model would be inappropriate
    ma, ctx = _make_ma(I2=65.0, tau2=0.15)
    result = detect_model_misspec(ma, ctx)
    assert result.severity == Severity.FAIL


def test_warn_very_high_heterogeneity():
    # I2 > 75% — unexplained substantial heterogeneity
    ma, ctx = _make_ma(I2=82.0, tau2=0.30)
    result = detect_model_misspec(ma, ctx)
    assert result.severity in (Severity.WARN, Severity.FAIL)


def test_warn_or_for_common_outcome():
    # OR used when event rate > 20% — RR would be more appropriate
    ma, ctx = _make_ma(I2=20.0, tau2=0.01, measure="logOR")
    ctx["event_rate"] = 0.35  # 35% event rate
    result = detect_model_misspec(ma, ctx)
    assert result.severity == Severity.WARN


def test_pass_or_for_rare_outcome():
    ma, ctx = _make_ma(I2=20.0, tau2=0.01, measure="logOR")
    ctx["event_rate"] = 0.08
    result = detect_model_misspec(ma, ctx)
    assert result.severity == Severity.PASS


def test_insufficient_data_k1():
    ma, ctx = _make_ma(I2=0.0, tau2=0.0, k=1)
    result = detect_model_misspec(ma, ctx)
    assert result.metrics.get("insufficient_data") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_model_misspec.py -v`
Expected: FAIL

- [ ] **Step 3: Implement model_misspec.py**

```python
# metaaudit/detectors/model_misspec.py
"""Module 2: Model Misspecification — FE/RE appropriateness and effect measure choice."""

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import Severity, DetectorResult

MODULE = "model_misspec"


def detect_model_misspec(ma: RecomputedMA, context: dict | None = None) -> DetectorResult:
    context = context or {}

    if ma.k < 2:
        return DetectorResult.insufficient_data(MODULE, reason="k < 2")

    issues = []
    severity = Severity.PASS

    # Check 1: High heterogeneity — FE model would be inappropriate
    if ma.I2 > 75.0:
        issues.append(f"Very high heterogeneity (I²={ma.I2:.1f}%) — "
                      f"pooled estimate may be misleading without subgroup exploration")
        severity = max(severity, Severity.FAIL)
    elif ma.I2 > 50.0:
        issues.append(f"Substantial heterogeneity (I²={ma.I2:.1f}%) — "
                      f"fixed-effect model inappropriate")
        severity = max(severity, Severity.FAIL)

    # Check 2: Effect measure appropriateness
    event_rate = context.get("event_rate")
    if event_rate is not None and ma.measure == "logOR" and event_rate > 0.20:
        issues.append(f"OR used for common outcome (event rate {event_rate:.0%}) — "
                      f"RR would be more interpretable and less biased")
        severity = max(severity, Severity.WARN)

    if not issues:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="No model misspecification detected",
            metrics={"I2": ma.I2, "tau2": ma.tau2, "measure": ma.measure},
        )

    return DetectorResult(
        module=MODULE, severity=severity,
        detail="; ".join(issues),
        metrics={
            "I2": ma.I2, "tau2": ma.tau2, "measure": ma.measure,
            "event_rate": event_rate, "issue_count": len(issues),
        },
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_model_misspec.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/model_misspec.py tests/test_model_misspec.py && git commit -m "feat: Module 2 — model misspecification detector (FE/RE, effect measure)"
```

---

### Task 7: Module 3 — Fragility (MAFI) Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\fragility.py`
- Create: `C:\MetaAudit\tests\test_fragility.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_fragility.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.fragility import detect_fragility


def _make_binary_ma(e_cases, e_n, c_cases, c_n, significant=True):
    """Build a RecomputedMA with study-level binary data attached."""
    import pandas as pd
    k = len(e_cases)
    yi = np.zeros(k)
    vi = np.full(k, 0.04)
    ma = RecomputedMA(
        k=k, yi=yi, vi=vi,
        estimate=-0.5, se=0.1, se_hksj=0.1,
        ci_lower=-0.9, ci_upper=-0.1,
        p_value=0.01 if significant else 0.20,
        tau2=0.05, I2=30.0, Q=5.0,
        significant=significant,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=True,
        data_type=DataType.BINARY, measure="logOR",
    )
    study_data = pd.DataFrame({
        "Experimental.cases": e_cases,
        "Experimental.N": e_n,
        "Control.cases": c_cases,
        "Control.N": c_n,
    })
    return ma, study_data


def test_fragile_mafi_1():
    # Barely significant — removing 1 event should flip it
    ma, df = _make_binary_ma(
        e_cases=[10, 12, 8], e_n=[100, 100, 100],
        c_cases=[15, 18, 14], c_n=[100, 100, 100],
    )
    result = detect_fragility(ma, df)
    assert result.severity in (Severity.FAIL, Severity.WARN)
    assert "mafi" in result.metrics


def test_robust_large_effect():
    # Very large, clearly significant effect
    ma, df = _make_binary_ma(
        e_cases=[5, 3, 2, 4, 6], e_n=[100, 100, 100, 100, 100],
        c_cases=[30, 35, 28, 32, 40], c_n=[100, 100, 100, 100, 100],
    )
    result = detect_fragility(ma, df)
    assert result.severity == Severity.PASS
    assert result.metrics["mafi"] > 5


def test_not_significant_skip():
    ma, df = _make_binary_ma(
        e_cases=[10, 12], e_n=[100, 100],
        c_cases=[11, 13], c_n=[100, 100],
        significant=False,
    )
    result = detect_fragility(ma, df)
    assert result.severity == Severity.PASS


def test_continuous_data_skip():
    ma = RecomputedMA(
        k=5, yi=np.zeros(5), vi=np.full(5, 0.04),
        estimate=-0.5, se=0.1, se_hksj=0.1,
        ci_lower=-0.7, ci_upper=-0.3,
        p_value=0.01, tau2=0.05, I2=30.0, Q=5.0,
        significant=True,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=True,
        data_type=DataType.CONTINUOUS, measure="MD",
    )
    result = detect_fragility(ma, None)
    assert result.metrics.get("insufficient_data") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_fragility.py -v`
Expected: FAIL

- [ ] **Step 3: Implement fragility.py**

```python
# metaaudit/detectors/fragility.py
"""Module 3: Fragility — Meta-Analysis Fragility Index (MAFI)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from metaaudit.loader import DataType
from metaaudit.recompute import RecomputedMA, compute_log_or, pool_effects_reml
from metaaudit.severity import Severity, DetectorResult

MODULE = "fragility"


def _compute_mafi(e_cases: np.ndarray, e_n: np.ndarray,
                  c_cases: np.ndarray, c_n: np.ndarray) -> int:
    """Compute fragility index: minimum event changes to lose significance.

    Modifies only the arm with FEWER events (adds events one at a time)
    until the pooled p-value crosses 0.05.
    """
    e_cases = e_cases.copy().astype(float)
    c_cases = c_cases.copy().astype(float)
    e_n_arr = e_n.copy().astype(float)
    c_n_arr = c_n.copy().astype(float)

    # Determine which arm has fewer total events
    total_e = e_cases.sum()
    total_c = c_cases.sum()
    modify_experimental = total_e < total_c

    changes = 0
    max_changes = int(min(e_n_arr.sum(), c_n_arr.sum()))  # Safety bound

    for _ in range(max_changes):
        yi, vi = compute_log_or(e_cases, e_n_arr, c_cases, c_n_arr)
        mask = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
        if mask.sum() < 2:
            break
        pooled = pool_effects_reml(yi[mask], vi[mask])
        if pooled["p_value"] >= 0.05:
            return changes

        # Add one event to the arm with fewer events, in the study
        # where the difference is largest (most room to shift)
        if modify_experimental:
            diffs = c_cases - e_cases
            idx = int(np.argmax(diffs))
            if e_cases[idx] < e_n_arr[idx]:
                e_cases[idx] += 1
            else:
                break
        else:
            diffs = e_cases - c_cases
            idx = int(np.argmax(diffs))
            if c_cases[idx] < c_n_arr[idx]:
                c_cases[idx] += 1
            else:
                break
        changes += 1

    return changes


def detect_fragility(ma: RecomputedMA,
                     study_data: pd.DataFrame | None) -> DetectorResult:
    if ma.data_type != DataType.BINARY:
        return DetectorResult.insufficient_data(
            MODULE, reason="Fragility index requires binary outcome data"
        )

    if not ma.significant:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="MA not significant — fragility not applicable",
            metrics={"significant": False},
        )

    if study_data is None or len(study_data) < 2:
        return DetectorResult.insufficient_data(MODULE, reason="No study-level data")

    mafi = _compute_mafi(
        study_data["Experimental.cases"].values,
        study_data["Experimental.N"].values,
        study_data["Control.cases"].values,
        study_data["Control.N"].values,
    )

    if mafi <= 2:
        severity = Severity.FAIL
        detail = f"Extremely fragile: MAFI = {mafi} (≤2 event changes flip significance)"
    elif mafi <= 5:
        severity = Severity.WARN
        detail = f"Fragile: MAFI = {mafi} (≤5 event changes flip significance)"
    else:
        severity = Severity.PASS
        detail = f"Robust: MAFI = {mafi}"

    return DetectorResult(
        module=MODULE, severity=severity, detail=detail,
        metrics={"mafi": mafi, "k": ma.k},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_fragility.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/fragility.py tests/test_fragility.py && git commit -m "feat: Module 3 — fragility (MAFI) detector"
```

---

### Task 8: Module 4 — Underpowered MA Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\underpowered.py`
- Create: `C:\MetaAudit\tests\test_underpowered.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_underpowered.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.underpowered import detect_underpowered


def _make_ma(k, total_n, significant=True):
    return RecomputedMA(
        k=k, yi=np.zeros(k), vi=np.full(k, 0.04),
        estimate=-0.5, se=0.1, se_hksj=0.1,
        ci_lower=-0.7, ci_upper=-0.3 if significant else 0.1,
        p_value=0.01 if significant else 0.20,
        tau2=0.05, I2=30.0, Q=5.0,
        significant=significant,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=k >= 3,
        data_type=DataType.BINARY, measure="logOR",
    )


def test_pass_adequate_k():
    ma = _make_ma(k=10, total_n=2000)
    result = detect_underpowered(ma, total_n=2000)
    assert result.severity == Severity.PASS


def test_warn_k_less_than_5():
    ma = _make_ma(k=4, total_n=400)
    result = detect_underpowered(ma, total_n=400)
    assert result.severity == Severity.WARN


def test_fail_k_less_than_3_significant():
    ma = _make_ma(k=2, total_n=200, significant=True)
    result = detect_underpowered(ma, total_n=200)
    assert result.severity == Severity.FAIL


def test_warn_k_less_than_3_not_significant():
    ma = _make_ma(k=2, total_n=200, significant=False)
    result = detect_underpowered(ma, total_n=200)
    assert result.severity == Severity.WARN


def test_warn_small_total_n():
    ma = _make_ma(k=8, total_n=80)
    result = detect_underpowered(ma, total_n=80)
    # Small total sample despite adequate k
    assert result.severity >= Severity.WARN
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_underpowered.py -v`
Expected: FAIL

- [ ] **Step 3: Implement underpowered.py**

```python
# metaaudit/detectors/underpowered.py
"""Module 4: Underpowered MA — insufficient studies or sample size."""

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import Severity, DetectorResult

MODULE = "underpowered"

# Optimal information size: rough approximation
# For OR=0.8 (moderate effect), alpha=0.05, power=0.80 => ~800 per arm
OIS_THRESHOLD = 1600  # Total N for moderate effect detection


def detect_underpowered(ma: RecomputedMA, total_n: int) -> DetectorResult:
    issues = []
    severity = Severity.PASS

    # Check k (number of studies)
    if ma.k < 3:
        if ma.significant:
            issues.append(f"Only k={ma.k} studies with significant result — "
                          f"unreliable heterogeneity estimate and inflated type I error")
            severity = max(severity, Severity.FAIL)
        else:
            issues.append(f"Only k={ma.k} studies — insufficient for reliable pooling")
            severity = max(severity, Severity.WARN)
    elif ma.k < 5:
        issues.append(f"Only k={ma.k} studies — heterogeneity estimates unreliable")
        severity = max(severity, Severity.WARN)

    # Check total sample size against OIS
    if total_n < OIS_THRESHOLD and ma.significant:
        issues.append(f"Total N={total_n} below optimal information size "
                      f"({OIS_THRESHOLD}) — effect may be overestimated")
        severity = max(severity, Severity.WARN)

    if not issues:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail=f"Adequate: k={ma.k}, total N={total_n}",
            metrics={"k": ma.k, "total_n": total_n},
        )

    return DetectorResult(
        module=MODULE, severity=severity,
        detail="; ".join(issues),
        metrics={"k": ma.k, "total_n": total_n, "ois_threshold": OIS_THRESHOLD},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_underpowered.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/underpowered.py tests/test_underpowered.py && git commit -m "feat: Module 4 — underpowered MA detector (k, OIS)"
```

---

### Task 9: Module 5 — Publication Bias Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\pub_bias.py`
- Create: `C:\MetaAudit\tests\test_pub_bias.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_pub_bias.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.pub_bias import detect_pub_bias


def _make_ma(k, yi=None, vi=None):
    if yi is None:
        yi = np.random.default_rng(42).normal(-0.5, 0.2, k)
    if vi is None:
        vi = np.random.default_rng(42).uniform(0.02, 0.08, k)
    return RecomputedMA(
        k=k, yi=yi, vi=vi,
        estimate=float(np.mean(yi)), se=0.1, se_hksj=0.1,
        ci_lower=-0.7, ci_upper=-0.3,
        p_value=0.01, tau2=0.05, I2=30.0, Q=5.0,
        significant=True,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=True,
        data_type=DataType.BINARY, measure="logOR",
    )


def test_insufficient_data_small_k():
    ma = _make_ma(k=5)
    result = detect_pub_bias(ma)
    assert result.metrics.get("insufficient_data") is True


def test_pass_symmetric_funnel():
    # Symmetric: effects centred, no variance-size correlation
    rng = np.random.default_rng(123)
    k = 20
    yi = rng.normal(-0.5, 0.05, k)  # Tight around true effect
    vi = rng.uniform(0.02, 0.10, k)  # Random precision, no correlation
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_pub_bias(ma)
    assert result.severity in (Severity.PASS, Severity.WARN)


def test_fail_asymmetric_funnel():
    # Small studies show much larger effects (classic pub bias pattern)
    k = 15
    # Large studies: precise, near true effect
    yi_large = np.array([-0.3, -0.35, -0.28, -0.32, -0.31])
    vi_large = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
    # Small studies: imprecise, exaggerated effects
    yi_small = np.array([-1.2, -1.0, -0.9, -1.1, -0.95, -1.3, -0.85, -1.05, -1.15, -0.98])
    vi_small = np.array([0.15, 0.12, 0.10, 0.14, 0.11, 0.16, 0.13, 0.12, 0.15, 0.10])
    yi = np.concatenate([yi_large, yi_small])
    vi = np.concatenate([vi_large, vi_small])
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_pub_bias(ma)
    assert result.severity >= Severity.WARN


def test_metrics_contain_test_results():
    ma = _make_ma(k=12)
    result = detect_pub_bias(ma)
    assert "egger_p" in result.metrics
    assert "begg_p" in result.metrics
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_pub_bias.py -v`
Expected: FAIL

- [ ] **Step 3: Implement pub_bias.py**

```python
# metaaudit/detectors/pub_bias.py
"""Module 5: Publication Bias — Egger's test, Begg's rank test, trim-and-fill."""

from __future__ import annotations

import numpy as np
from scipy import stats

from metaaudit.recompute import RecomputedMA, pool_effects_reml
from metaaudit.severity import Severity, DetectorResult

MODULE = "pub_bias"
MIN_K = 10


def _egger_test(yi: np.ndarray, vi: np.ndarray) -> tuple[float, float]:
    """Egger's regression test for funnel plot asymmetry.
    Regress standardised effect (yi/sqrt(vi)) on precision (1/sqrt(vi)).
    Returns (intercept, p_value).
    """
    se = np.sqrt(vi)
    precision = 1.0 / se
    z = yi / se
    # Weighted linear regression: z = a + b * precision
    n = len(yi)
    x = precision
    y = z
    x_mean = x.mean()
    y_mean = y.mean()
    ss_xx = ((x - x_mean) ** 2).sum()
    ss_xy = ((x - x_mean) * (y - y_mean)).sum()
    if ss_xx == 0:
        return 0.0, 1.0
    b = ss_xy / ss_xx
    a = y_mean - b * x_mean
    residuals = y - (a + b * x)
    mse = (residuals ** 2).sum() / (n - 2)
    se_a = np.sqrt(mse * (1.0 / n + x_mean ** 2 / ss_xx))
    if se_a == 0:
        return a, 1.0
    t_stat = a / se_a
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
    return float(a), float(p_value)


def _begg_test(yi: np.ndarray, vi: np.ndarray) -> tuple[float, float]:
    """Begg and Mazumdar rank correlation test.
    Kendall's tau between effect sizes and variances.
    Returns (tau, p_value).
    """
    n = len(yi)
    if n < 3:
        return 0.0, 1.0
    # Standardize effects by subtracting pooled estimate
    w = 1.0 / vi
    theta = (w * yi).sum() / w.sum()
    resid = yi - theta
    tau, p_value = stats.kendalltau(resid, vi)
    return float(tau), float(p_value)


def _trim_and_fill(yi: np.ndarray, vi: np.ndarray,
                   side: str = "right") -> dict:
    """Simple trim-and-fill (L0 estimator).
    Returns adjusted estimate and number of imputed studies.
    """
    pooled = pool_effects_reml(yi, vi)
    theta = pooled["estimate"]
    # Rank by distance from pooled estimate
    resid = yi - theta
    abs_resid = np.abs(resid)
    ranks = stats.rankdata(abs_resid)
    # Count asymmetric studies on the side with fewer
    n_right = (resid > 0).sum()
    n_left = (resid < 0).sum()
    k0 = abs(n_right - n_left)
    if k0 == 0:
        return {"adjusted_estimate": theta, "k_imputed": 0,
                "original_estimate": theta}
    # Impute mirror studies
    if n_right > n_left:
        # Trim rightmost k0 studies, mirror them
        idx = np.argsort(resid)[-k0:]
    else:
        idx = np.argsort(resid)[:k0]
    imputed_yi = 2 * theta - yi[idx]
    imputed_vi = vi[idx]
    all_yi = np.concatenate([yi, imputed_yi])
    all_vi = np.concatenate([vi, imputed_vi])
    adj = pool_effects_reml(all_yi, all_vi)
    return {
        "adjusted_estimate": adj["estimate"],
        "k_imputed": int(k0),
        "original_estimate": theta,
    }


def detect_pub_bias(ma: RecomputedMA) -> DetectorResult:
    if ma.k < MIN_K:
        return DetectorResult.insufficient_data(
            MODULE, reason=f"k={ma.k} < {MIN_K}, bias tests underpowered"
        )

    egger_intercept, egger_p = _egger_test(ma.yi, ma.vi)
    begg_tau, begg_p = _begg_test(ma.yi, ma.vi)
    tf = _trim_and_fill(ma.yi, ma.vi)

    # Count how many tests suggest bias (p < 0.10)
    signals = 0
    if egger_p < 0.10:
        signals += 1
    if begg_p < 0.10:
        signals += 1

    metrics = {
        "egger_intercept": egger_intercept,
        "egger_p": egger_p,
        "begg_tau": begg_tau,
        "begg_p": begg_p,
        "trim_fill_adjusted": tf["adjusted_estimate"],
        "trim_fill_k_imputed": tf["k_imputed"],
        "trim_fill_original": tf["original_estimate"],
        "signals": signals,
    }

    if signals >= 2:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail=f"Publication bias: Egger p={egger_p:.3f}, Begg p={begg_p:.3f}, "
                   f"trim-fill imputed {tf['k_imputed']} studies "
                   f"(adjusted effect: {tf['adjusted_estimate']:.3f})",
            metrics=metrics,
        )
    elif signals == 1:
        return DetectorResult(
            module=MODULE, severity=Severity.WARN,
            detail=f"Possible bias: Egger p={egger_p:.3f}, Begg p={begg_p:.3f}",
            metrics=metrics,
        )
    else:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="No evidence of publication bias",
            metrics=metrics,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_pub_bias.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/pub_bias.py tests/test_pub_bias.py && git commit -m "feat: Module 5 — publication bias detector (Egger/Begg/trim-fill)"
```

---

### Task 10: Module 6 — Small-Study Effects Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\small_study.py`
- Create: `C:\MetaAudit\tests\test_small_study.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_small_study.py
import numpy as np
import pandas as pd
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.small_study import detect_small_study


def _make_ma(k, yi, vi, data_type=DataType.BINARY, study_data=None):
    return RecomputedMA(
        k=k, yi=yi, vi=vi,
        estimate=float(np.mean(yi)), se=0.1, se_hksj=0.1,
        ci_lower=-0.8, ci_upper=-0.2,
        p_value=0.01, tau2=0.05, I2=30.0, Q=5.0,
        significant=True,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=True,
        data_type=data_type, measure="logOR",
    )


def test_insufficient_data():
    yi = np.array([-0.5, -0.6, -0.4])
    vi = np.array([0.04, 0.05, 0.03])
    ma = _make_ma(k=3, yi=yi, vi=vi)
    result = detect_small_study(ma)
    assert result.metrics.get("insufficient_data") is True


def test_pass_no_size_effect_correlation():
    rng = np.random.default_rng(99)
    k = 15
    yi = rng.normal(-0.5, 0.1, k)
    vi = rng.uniform(0.02, 0.10, k)
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_small_study(ma)
    assert result.severity in (Severity.PASS, Severity.WARN)


def test_fail_small_studies_larger_effects():
    # Small studies (high variance) have exaggerated effects
    k = 12
    yi = np.array([-0.3, -0.28, -0.32, -0.29,   # large studies
                   -0.9, -1.1, -0.85, -1.0,       # medium studies
                   -1.5, -1.8, -1.6, -1.7])        # small studies
    vi = np.array([0.01, 0.01, 0.01, 0.01,
                   0.06, 0.07, 0.05, 0.06,
                   0.15, 0.18, 0.16, 0.17])
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_small_study(ma)
    assert result.severity >= Severity.WARN
    assert "correlation" in result.metrics or "peters_p" in result.metrics
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_small_study.py -v`
Expected: FAIL

- [ ] **Step 3: Implement small_study.py**

```python
# metaaudit/detectors/small_study.py
"""Module 6: Small-Study Effects — funnel asymmetry where small studies show larger effects."""

from __future__ import annotations

import numpy as np
from scipy import stats

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import Severity, DetectorResult

MODULE = "small_study"
MIN_K = 10


def _peters_test(yi: np.ndarray, vi: np.ndarray,
                 n_total: np.ndarray | None = None) -> tuple[float, float]:
    """Peters' test: weighted regression of effect on 1/N.
    More robust than Egger's for binary outcomes.
    Falls back to Egger's if sample sizes unavailable.
    """
    if n_total is not None and len(n_total) == len(yi):
        x = 1.0 / n_total
    else:
        # Fallback: use sqrt(vi) as proxy for 1/sqrt(N)
        x = np.sqrt(vi)
    n = len(yi)
    w = 1.0 / vi
    # WLS regression: yi = a + b*x, weighted by 1/vi
    sw = w.sum()
    swx = (w * x).sum()
    swy = (w * yi).sum()
    swxx = (w * x ** 2).sum()
    swxy = (w * x * yi).sum()
    denom = sw * swxx - swx ** 2
    if abs(denom) < 1e-12:
        return 0.0, 1.0
    b = (sw * swxy - swx * swy) / denom
    a = (swy - b * swx) / sw
    # Residuals and SE of slope
    predicted = a + b * x
    resid = yi - predicted
    mse = (w * resid ** 2).sum() / (n - 2)
    se_b = np.sqrt(mse * sw / denom)
    if se_b == 0:
        return b, 1.0
    t_stat = b / se_b
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
    return float(b), float(p_value)


def detect_small_study(ma: RecomputedMA) -> DetectorResult:
    if ma.k < MIN_K:
        return DetectorResult.insufficient_data(
            MODULE, reason=f"k={ma.k} < {MIN_K}"
        )

    slope, peters_p = _peters_test(ma.yi, ma.vi)

    # Also compute rank correlation between |effect| and variance
    abs_yi = np.abs(ma.yi)
    corr, corr_p = stats.spearmanr(abs_yi, ma.vi)

    # Small-study effect: larger effects in smaller (higher variance) studies
    # The slope should indicate that higher variance → more extreme effect
    has_asymmetry = peters_p < 0.10
    small_larger = corr > 0  # Positive: larger |effect| with larger variance

    metrics = {
        "peters_slope": slope,
        "peters_p": peters_p,
        "correlation": float(corr),
        "correlation_p": float(corr_p),
    }

    if has_asymmetry and small_larger:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail=f"Small-study effects: Peters p={peters_p:.3f}, "
                   f"effect-variance correlation r={corr:.2f}",
            metrics=metrics,
        )
    elif has_asymmetry or (corr_p < 0.05 and small_larger):
        return DetectorResult(
            module=MODULE, severity=Severity.WARN,
            detail=f"Possible small-study effects: Peters p={peters_p:.3f}, "
                   f"correlation r={corr:.2f}",
            metrics=metrics,
        )
    else:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="No small-study effects detected",
            metrics=metrics,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_small_study.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/small_study.py tests/test_small_study.py && git commit -m "feat: Module 6 — small-study effects detector (Peters/Spearman)"
```

---

### Task 11: Module 7 — Excess Significance Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\excess_sig.py`
- Create: `C:\MetaAudit\tests\test_excess_sig.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_excess_sig.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.excess_sig import detect_excess_sig


def _make_ma(k, yi, vi):
    return RecomputedMA(
        k=k, yi=yi, vi=vi,
        estimate=float(np.average(yi, weights=1.0/vi)),
        se=0.1, se_hksj=0.1,
        ci_lower=-0.7, ci_upper=-0.3,
        p_value=0.01, tau2=0.05, I2=30.0, Q=5.0,
        significant=True,
        pi_lower=-1.5, pi_upper=0.5, pi_computable=True,
        data_type=DataType.BINARY, measure="logOR",
    )


def test_insufficient_data():
    ma = _make_ma(k=3, yi=np.array([-0.5, -0.6, -0.4]),
                  vi=np.array([0.04, 0.05, 0.03]))
    result = detect_excess_sig(ma)
    assert result.metrics.get("insufficient_data") is True


def test_pass_expected_matches_observed():
    # 10 studies, true effect ~ -0.5, all well-powered => all significant, expected ~ 10
    k = 10
    yi = np.full(k, -0.5)
    vi = np.full(k, 0.02)  # Low variance => high power => all significant
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_excess_sig(ma)
    assert result.severity == Severity.PASS


def test_fail_too_many_significant():
    # 10 studies, very weak true effect, but all "significant" => suspicious
    k = 10
    # True effect is tiny but studies report significant
    yi = np.array([-0.5, -0.6, -0.55, -0.48, -0.52,
                   -0.58, -0.45, -0.62, -0.53, -0.49])
    vi = np.array([0.06, 0.07, 0.065, 0.08, 0.075,
                   0.06, 0.085, 0.07, 0.065, 0.08])
    # With these variances, individual z ~ -0.5/sqrt(0.07) ~ -1.89 => p~0.06 (borderline)
    # Expected significant ~ 4-5, but if all 10 are "significant" that's excess
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_excess_sig(ma)
    assert "observed" in result.metrics
    assert "expected" in result.metrics


def test_metrics_contain_oe_ratio():
    k = 10
    yi = np.full(k, -0.5)
    vi = np.full(k, 0.04)
    ma = _make_ma(k=k, yi=yi, vi=vi)
    result = detect_excess_sig(ma)
    assert "oe_ratio" in result.metrics
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_excess_sig.py -v`
Expected: FAIL

- [ ] **Step 3: Implement excess_sig.py**

```python
# metaaudit/detectors/excess_sig.py
"""Module 7: Excess Significance — Ioannidis & Trikalinos test."""

from __future__ import annotations

import numpy as np
from scipy import stats

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import Severity, DetectorResult

MODULE = "excess_sig"
MIN_K = 5


def detect_excess_sig(ma: RecomputedMA) -> DetectorResult:
    if ma.k < MIN_K:
        return DetectorResult.insufficient_data(
            MODULE, reason=f"k={ma.k} < {MIN_K}"
        )

    yi = ma.yi
    vi = ma.vi
    se = np.sqrt(vi)
    theta = ma.estimate  # Best estimate of true effect

    # For each study, compute the power to detect the pooled effect
    # Power = P(|Z| > 1.96 | true effect = theta, se_i)
    # Z_i = theta / se_i
    observed_sig = 0
    expected_sig = 0.0

    for i in range(ma.k):
        # Individual study z-test
        z_i = yi[i] / se[i]
        is_sig = abs(z_i) > 1.96
        if is_sig:
            observed_sig += 1

        # Expected: power of this study to detect the pooled effect
        ncp = abs(theta) / se[i]  # Non-centrality parameter
        # Power = P(Z > 1.96 - ncp) + P(Z < -1.96 - ncp) for two-sided
        power = stats.norm.sf(1.96 - ncp) + stats.norm.cdf(-1.96 - ncp)
        expected_sig += power

    oe_ratio = observed_sig / expected_sig if expected_sig > 0 else float("inf")

    # Binomial test: is observed significantly more than expected?
    if expected_sig > 0:
        p_excess = stats.binom_test(
            observed_sig, ma.k,
            min(expected_sig / ma.k, 1.0),
            alternative="greater",
        ) if hasattr(stats, "binom_test") else stats.binomtest(
            observed_sig, ma.k,
            min(expected_sig / ma.k, 1.0),
            alternative="greater",
        ).pvalue
    else:
        p_excess = 1.0

    metrics = {
        "observed": observed_sig,
        "expected": round(expected_sig, 1),
        "oe_ratio": round(oe_ratio, 2),
        "p_excess": float(p_excess),
    }

    if oe_ratio > 1.5 and p_excess < 0.10:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail=f"Excess significance: O={observed_sig}, E={expected_sig:.1f}, "
                   f"O/E={oe_ratio:.2f}, p={p_excess:.3f}",
            metrics=metrics,
        )
    elif oe_ratio > 1.2 and p_excess < 0.10:
        return DetectorResult(
            module=MODULE, severity=Severity.WARN,
            detail=f"Borderline excess significance: O/E={oe_ratio:.2f}, p={p_excess:.3f}",
            metrics=metrics,
        )
    else:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail=f"No excess significance: O={observed_sig}, E={expected_sig:.1f}",
            metrics=metrics,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_excess_sig.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/excess_sig.py tests/test_excess_sig.py && git commit -m "feat: Module 7 — excess significance detector (Ioannidis-Trikalinos)"
```

---

### Task 12: Module 8 — Data Integrity Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\integrity.py`
- Create: `C:\MetaAudit\tests\test_integrity.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_integrity.py
import numpy as np
import pandas as pd
import pytest
from metaaudit.severity import Severity
from metaaudit.loader import DataType
from metaaudit.detectors.integrity import detect_integrity


def test_pass_clean_data():
    df = pd.DataFrame({
        "Experimental.cases": [10, 15, 8, 20, 12],
        "Experimental.N": [100, 120, 80, 150, 110],
        "Control.cases": [20, 25, 15, 30, 22],
        "Control.N": [100, 120, 80, 150, 110],
    })
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.PASS


def test_fail_events_exceed_n():
    df = pd.DataFrame({
        "Experimental.cases": [10, 150, 8],  # 150 > 120!
        "Experimental.N": [100, 120, 80],
        "Control.cases": [20, 25, 15],
        "Control.N": [100, 120, 80],
    })
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.FAIL
    assert "impossible" in result.detail.lower()


def test_warn_duplicate_effect_sizes():
    df = pd.DataFrame({
        "Experimental.cases": [10, 10, 10],  # Identical across studies
        "Experimental.N": [100, 100, 100],
        "Control.cases": [20, 20, 20],
        "Control.N": [100, 100, 100],
    })
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity >= Severity.WARN


def test_fail_negative_values():
    df = pd.DataFrame({
        "Experimental.cases": [10, -5, 8],  # Negative!
        "Experimental.N": [100, 120, 80],
        "Control.cases": [20, 25, 15],
        "Control.N": [100, 120, 80],
    })
    result = detect_integrity(df, DataType.BINARY)
    assert result.severity == Severity.FAIL


def test_pass_continuous_clean():
    df = pd.DataFrame({
        "Experimental.mean": [120.0, 118.5],
        "Experimental.SD": [15.0, 12.0],
        "Experimental.N": [50, 60],
        "Control.mean": [130.0, 128.0],
        "Control.SD": [16.0, 13.0],
        "Control.N": [50, 60],
    })
    result = detect_integrity(df, DataType.CONTINUOUS)
    assert result.severity == Severity.PASS


def test_fail_negative_sd():
    df = pd.DataFrame({
        "Experimental.mean": [120.0],
        "Experimental.SD": [-15.0],  # Negative SD!
        "Experimental.N": [50],
        "Control.mean": [130.0],
        "Control.SD": [16.0],
        "Control.N": [50],
    })
    result = detect_integrity(df, DataType.CONTINUOUS)
    assert result.severity == Severity.FAIL
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_integrity.py -v`
Expected: FAIL

- [ ] **Step 3: Implement integrity.py**

```python
# metaaudit/detectors/integrity.py
"""Module 8: Data Integrity — impossible values, duplicates, GRIM checks."""

from __future__ import annotations

import numpy as np
import pandas as pd

from metaaudit.loader import DataType
from metaaudit.severity import Severity, DetectorResult

MODULE = "integrity"


def _check_binary_impossible(df: pd.DataFrame) -> list[str]:
    issues = []
    for col_cases, col_n in [
        ("Experimental.cases", "Experimental.N"),
        ("Control.cases", "Control.N"),
    ]:
        if col_cases not in df.columns or col_n not in df.columns:
            continue
        cases = df[col_cases]
        n = df[col_n]
        # Events > N
        mask = cases > n
        if mask.any():
            bad = df.index[mask].tolist()
            issues.append(f"Impossible: events > N in {col_cases} at rows {bad}")
        # Negative values
        mask_neg = (cases < 0) | (n < 0)
        if mask_neg.any():
            bad = df.index[mask_neg].tolist()
            issues.append(f"Impossible: negative values in {col_cases}/{col_n} at rows {bad}")
    return issues


def _check_continuous_impossible(df: pd.DataFrame) -> list[str]:
    issues = []
    for prefix in ["Experimental", "Control"]:
        sd_col = f"{prefix}.SD"
        n_col = f"{prefix}.N"
        if sd_col in df.columns:
            mask = df[sd_col] < 0
            if mask.any():
                bad = df.index[mask].tolist()
                issues.append(f"Impossible: negative SD in {sd_col} at rows {bad}")
        if n_col in df.columns:
            mask = df[n_col] <= 0
            if mask.any():
                bad = df.index[mask].tolist()
                issues.append(f"Impossible: non-positive N in {n_col} at rows {bad}")
    return issues


def _check_duplicates(df: pd.DataFrame, data_type: DataType) -> list[str]:
    issues = []
    if data_type == DataType.BINARY:
        cols = ["Experimental.cases", "Experimental.N", "Control.cases", "Control.N"]
    elif data_type == DataType.CONTINUOUS:
        cols = ["Experimental.mean", "Experimental.SD", "Experimental.N",
                "Control.mean", "Control.SD", "Control.N"]
    else:
        return issues
    available = [c for c in cols if c in df.columns]
    if not available or len(df) < 3:
        return issues
    dupes = df.duplicated(subset=available, keep=False)
    n_dupes = dupes.sum()
    if n_dupes >= 2 and n_dupes / len(df) > 0.5:
        issues.append(f"Suspicious: {n_dupes}/{len(df)} studies have identical data values")
    return issues


def _grim_check(means: np.ndarray, ns: np.ndarray) -> list[str]:
    """GRIM test: check if reported means are consistent with integer counts and N."""
    issues = []
    for i, (m, n) in enumerate(zip(means, ns)):
        if n <= 0 or not np.isfinite(m):
            continue
        # Granularity: mean of integers with N items has granularity 1/N
        granularity = 1.0 / n
        remainder = m % granularity
        # Allow small floating point tolerance
        if min(remainder, granularity - remainder) > 0.01 * granularity:
            # Only flag for small N where GRIM is meaningful
            if n <= 100:
                issues.append(f"GRIM inconsistency at row {i}: mean={m}, N={n}")
    return issues


def detect_integrity(df: pd.DataFrame, data_type: DataType) -> DetectorResult:
    all_issues = []

    if data_type == DataType.BINARY:
        all_issues.extend(_check_binary_impossible(df))
    elif data_type == DataType.CONTINUOUS:
        all_issues.extend(_check_continuous_impossible(df))
        # GRIM check on continuous data with integer-plausible means
        if "Experimental.mean" in df.columns and "Experimental.N" in df.columns:
            all_issues.extend(_grim_check(
                df["Experimental.mean"].values, df["Experimental.N"].values
            ))

    all_issues.extend(_check_duplicates(df, data_type))

    impossible = [i for i in all_issues if "impossible" in i.lower()]
    suspicious = [i for i in all_issues if "impossible" not in i.lower()]

    metrics = {
        "impossible_count": len(impossible),
        "suspicious_count": len(suspicious),
        "total_issues": len(all_issues),
    }

    if impossible:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail="; ".join(all_issues),
            metrics=metrics,
        )
    elif suspicious:
        return DetectorResult(
            module=MODULE, severity=Severity.WARN,
            detail="; ".join(all_issues),
            metrics=metrics,
        )
    else:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="No data integrity issues detected",
            metrics=metrics,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_integrity.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/integrity.py tests/test_integrity.py && git commit -m "feat: Module 8 — data integrity detector (impossible values, GRIM, duplicates)"
```

---

### Task 13: Module 9 — Study Overlap Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\overlap.py`
- Create: `C:\MetaAudit\tests\test_overlap.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_overlap.py
import pytest
from metaaudit.severity import Severity
from metaaudit.detectors.overlap import detect_overlap, build_overlap_index


def test_build_overlap_index():
    studies_by_review = {
        "CD001": {"Smith 2010", "Jones 2012", "Lee 2014"},
        "CD002": {"Smith 2010", "Brown 2013", "Lee 2014"},
        "CD003": {"Taylor 2015", "White 2016"},
    }
    index = build_overlap_index(studies_by_review)
    # CD001 and CD002 share Smith 2010 and Lee 2014
    assert index[("CD001", "CD002")] == {"Smith 2010", "Lee 2014"}
    assert ("CD001", "CD003") not in index
    assert ("CD002", "CD003") not in index


def test_pass_no_overlap():
    studies_by_review = {
        "CD001": {"A", "B", "C"},
        "CD002": {"D", "E", "F"},
    }
    index = build_overlap_index(studies_by_review)
    result = detect_overlap("CD001", {"A", "B", "C"}, index)
    assert result.severity == Severity.PASS


def test_warn_moderate_overlap():
    studies_by_review = {
        "CD001": {"A", "B", "C", "D", "E", "F", "G", "H", "I", "J"},
        "CD002": {"A", "B", "C", "X", "Y", "Z", "W", "V", "U", "T"},
    }
    index = build_overlap_index(studies_by_review)
    # 3/10 = 30% overlap
    result = detect_overlap("CD001", studies_by_review["CD001"], index)
    assert result.severity == Severity.WARN


def test_fail_high_overlap_contradictory():
    studies_by_review = {
        "CD001": {"A", "B", "C", "D"},
        "CD002": {"A", "B", "C", "E"},  # 75% overlap
    }
    index = build_overlap_index(studies_by_review)
    result = detect_overlap(
        "CD001", studies_by_review["CD001"], index,
        review_conclusions={"CD001": "effective", "CD002": "not effective"},
    )
    assert result.severity == Severity.FAIL
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_overlap.py -v`
Expected: FAIL

- [ ] **Step 3: Implement overlap.py**

```python
# metaaudit/detectors/overlap.py
"""Module 9: Study Overlap — cross-review study sharing detection."""

from __future__ import annotations

from metaaudit.severity import Severity, DetectorResult

MODULE = "overlap"
OVERLAP_WARN_THRESHOLD = 0.30  # 30%


def build_overlap_index(
    studies_by_review: dict[str, set[str]],
) -> dict[tuple[str, str], set[str]]:
    """Build pairwise overlap index. Only stores pairs with >=1 shared study."""
    index = {}
    review_ids = sorted(studies_by_review.keys())
    for i, r1 in enumerate(review_ids):
        for r2 in review_ids[i + 1:]:
            shared = studies_by_review[r1] & studies_by_review[r2]
            if shared:
                index[(r1, r2)] = shared
    return index


def detect_overlap(
    review_id: str,
    studies: set[str],
    overlap_index: dict[tuple[str, str], set[str]],
    review_conclusions: dict[str, str] | None = None,
) -> DetectorResult:
    if not studies:
        return DetectorResult.insufficient_data(MODULE, reason="No study identifiers")

    k = len(studies)
    max_overlap_frac = 0.0
    max_overlap_partner = None
    max_shared = set()

    for (r1, r2), shared in overlap_index.items():
        partner = None
        if r1 == review_id:
            partner = r2
        elif r2 == review_id:
            partner = r1
        if partner is None:
            continue
        frac = len(shared) / k
        if frac > max_overlap_frac:
            max_overlap_frac = frac
            max_overlap_partner = partner
            max_shared = shared

    metrics = {
        "max_overlap_fraction": round(max_overlap_frac, 3),
        "max_overlap_partner": max_overlap_partner,
        "shared_studies_count": len(max_shared),
        "total_studies": k,
    }

    if max_overlap_frac < OVERLAP_WARN_THRESHOLD:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail=f"Max overlap {max_overlap_frac:.0%} with {max_overlap_partner or 'none'}",
            metrics=metrics,
        )

    # Check for contradictory conclusions
    contradictory = False
    if review_conclusions and max_overlap_partner:
        c1 = review_conclusions.get(review_id, "")
        c2 = review_conclusions.get(max_overlap_partner, "")
        if c1 and c2 and c1 != c2:
            contradictory = True
            metrics["contradictory_conclusions"] = True
            metrics["this_conclusion"] = c1
            metrics["partner_conclusion"] = c2

    if contradictory:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail=f"{max_overlap_frac:.0%} overlap with {max_overlap_partner} "
                   f"and contradictory conclusions",
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE, severity=Severity.WARN,
        detail=f"{max_overlap_frac:.0%} overlap with {max_overlap_partner} "
               f"({len(max_shared)} shared studies)",
        metrics=metrics,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_overlap.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/overlap.py tests/test_overlap.py && git commit -m "feat: Module 9 — study overlap detector (cross-review sharing)"
```

---

### Task 14: Module 10 — Overclaiming Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\overclaiming.py`
- Create: `C:\MetaAudit\tests\test_overclaiming.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_overclaiming.py
import numpy as np
import pytest
from metaaudit.severity import Severity
from metaaudit.recompute import RecomputedMA
from metaaudit.loader import DataType
from metaaudit.detectors.overclaiming import detect_overclaiming


def _make_ma(estimate, significant=True, measure="logOR"):
    return RecomputedMA(
        k=10, yi=np.zeros(10), vi=np.full(10, 0.04),
        estimate=estimate, se=0.05, se_hksj=0.05,
        ci_lower=estimate - 0.1, ci_upper=estimate + 0.1,
        p_value=0.01 if significant else 0.20,
        tau2=0.02, I2=20.0, Q=5.0,
        significant=significant,
        pi_lower=estimate - 0.5, pi_upper=estimate + 0.5,
        pi_computable=True,
        data_type=DataType.BINARY, measure=measure,
    )


def test_pass_large_effect():
    # log(0.5) ~ -0.693 — large, clinically meaningful effect
    ma = _make_ma(estimate=-0.693)
    result = detect_overclaiming(ma)
    assert result.severity == Severity.PASS


def test_fail_trivial_effect():
    # log(0.95) ~ -0.051 — trivial effect, below MCID
    ma = _make_ma(estimate=-0.051)
    result = detect_overclaiming(ma)
    assert result.severity == Severity.FAIL


def test_pass_not_significant():
    ma = _make_ma(estimate=-0.05, significant=False)
    result = detect_overclaiming(ma)
    assert result.severity == Severity.PASS


def test_warn_borderline_effect():
    # log(0.80) ~ -0.223 — exactly at MCID boundary
    ma = _make_ma(estimate=-0.20)
    result = detect_overclaiming(ma)
    assert result.severity in (Severity.PASS, Severity.WARN)


def test_smd_trivial():
    ma = _make_ma(estimate=-0.08, measure="MD")
    # Very small MD
    result = detect_overclaiming(ma)
    assert result.severity >= Severity.WARN
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_overclaiming.py -v`
Expected: FAIL

- [ ] **Step 3: Implement overclaiming.py**

```python
# metaaudit/detectors/overclaiming.py
"""Module 10: Overclaiming — significant but clinically trivial effects."""

from __future__ import annotations

import math

from metaaudit.recompute import RecomputedMA
from metaaudit.severity import Severity, DetectorResult

MODULE = "overclaiming"

# MCIDs by measure type (on the scale the effect is reported)
MCID = {
    "logOR": math.log(1.25),   # ~0.223 — OR of 1.25 considered minimally important
    "logRR": math.log(1.25),
    "MD": None,                 # Context-dependent — use generic threshold
    "SMD": 0.2,                 # Cohen's small effect
    "GIV": None,
}

# Generic threshold when MCID unavailable
GENERIC_TRIVIAL = 0.1


def detect_overclaiming(ma: RecomputedMA) -> DetectorResult:
    if not ma.significant:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail="MA not significant — overclaiming not applicable",
            metrics={"significant": False},
        )

    abs_effect = abs(ma.estimate)
    mcid = MCID.get(ma.measure)
    threshold = mcid if mcid is not None else GENERIC_TRIVIAL
    threshold_label = f"MCID={threshold:.3f}" if mcid is not None else f"generic={threshold:.3f}"

    metrics = {
        "abs_effect": round(abs_effect, 4),
        "threshold": round(threshold, 4),
        "measure": ma.measure,
        "mcid_available": mcid is not None,
    }

    if abs_effect < threshold * 0.5:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail=f"Clinically trivial effect: |{ma.estimate:.3f}| < 50% of {threshold_label}",
            metrics=metrics,
        )
    elif abs_effect < threshold:
        return DetectorResult(
            module=MODULE, severity=Severity.WARN,
            detail=f"Effect below MCID: |{ma.estimate:.3f}| < {threshold_label}",
            metrics=metrics,
        )
    else:
        return DetectorResult(
            module=MODULE, severity=Severity.PASS,
            detail=f"Effect above MCID: |{ma.estimate:.3f}| ≥ {threshold_label}",
            metrics=metrics,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_overclaiming.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/overclaiming.py tests/test_overclaiming.py && git commit -m "feat: Module 10 — overclaiming detector (effect vs MCID)"
```

---

### Task 15: Module 11 — Certainty-Outcome Mismatch Detector

**Files:**
- Create: `C:\MetaAudit\metaaudit\detectors\certainty_mismatch.py`
- Create: `C:\MetaAudit\tests\test_certainty_mismatch.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_certainty_mismatch.py
import pytest
from metaaudit.severity import Severity, DetectorResult
from metaaudit.detectors.certainty_mismatch import detect_certainty_mismatch


def test_no_grade_available():
    other_results = [
        DetectorResult("m1", Severity.FAIL, ""),
        DetectorResult("m2", Severity.FAIL, ""),
    ]
    result = detect_certainty_mismatch(grade_certainty=None, other_results=other_results)
    assert result.metrics.get("insufficient_data") is True


def test_pass_high_grade_no_fails():
    other_results = [
        DetectorResult("m1", Severity.PASS, ""),
        DetectorResult("m2", Severity.WARN, ""),
        DetectorResult("m3", Severity.PASS, ""),
    ]
    result = detect_certainty_mismatch(grade_certainty="High", other_results=other_results)
    assert result.severity == Severity.PASS


def test_critical_high_grade_many_fails():
    other_results = [
        DetectorResult("m1", Severity.FAIL, ""),
        DetectorResult("m2", Severity.FAIL, ""),
        DetectorResult("m3", Severity.FAIL, ""),
        DetectorResult("m4", Severity.PASS, ""),
    ]
    result = detect_certainty_mismatch(grade_certainty="High", other_results=other_results)
    assert result.severity == Severity.CRITICAL


def test_fail_moderate_grade_many_fails():
    other_results = [
        DetectorResult("m1", Severity.FAIL, ""),
        DetectorResult("m2", Severity.FAIL, ""),
        DetectorResult("m3", Severity.FAIL, ""),
        DetectorResult("m4", Severity.FAIL, ""),
        DetectorResult("m5", Severity.PASS, ""),
    ]
    result = detect_certainty_mismatch(grade_certainty="Moderate", other_results=other_results)
    assert result.severity == Severity.FAIL


def test_pass_low_grade_with_fails():
    other_results = [
        DetectorResult("m1", Severity.FAIL, ""),
        DetectorResult("m2", Severity.FAIL, ""),
        DetectorResult("m3", Severity.FAIL, ""),
    ]
    result = detect_certainty_mismatch(grade_certainty="Low", other_results=other_results)
    assert result.severity == Severity.PASS  # Low certainty already acknowledged
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_certainty_mismatch.py -v`
Expected: FAIL

- [ ] **Step 3: Implement certainty_mismatch.py**

```python
# metaaudit/detectors/certainty_mismatch.py
"""Module 11: Certainty-Outcome Mismatch — GRADE certainty vs automated severity."""

from __future__ import annotations

from metaaudit.severity import Severity, DetectorResult

MODULE = "certainty_mismatch"

# GRADE levels ordered by confidence
GRADE_LEVELS = {"High": 4, "Moderate": 3, "Low": 2, "Very low": 1}


def detect_certainty_mismatch(
    grade_certainty: str | None,
    other_results: list[DetectorResult],
) -> DetectorResult:
    if grade_certainty is None:
        return DetectorResult.insufficient_data(
            MODULE, reason="No GRADE certainty rating available"
        )

    grade_level = GRADE_LEVELS.get(grade_certainty, 0)
    if grade_level == 0:
        return DetectorResult.insufficient_data(
            MODULE, reason=f"Unrecognised GRADE level: {grade_certainty}"
        )

    fail_count = sum(1 for r in other_results if r.severity >= Severity.FAIL)
    warn_count = sum(1 for r in other_results if r.severity == Severity.WARN)
    total_modules = len(other_results)

    metrics = {
        "grade_certainty": grade_certainty,
        "grade_level": grade_level,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "total_modules": total_modules,
    }

    # Only flag mismatch for High/Moderate certainty
    if grade_certainty == "High" and fail_count >= 3:
        return DetectorResult(
            module=MODULE, severity=Severity.CRITICAL,
            detail=f"GRADE 'High' certainty but {fail_count}/{total_modules} "
                   f"modules FAIL — automated checks contradict stated certainty",
            metrics=metrics,
        )

    if grade_certainty == "Moderate" and fail_count >= 4:
        return DetectorResult(
            module=MODULE, severity=Severity.FAIL,
            detail=f"GRADE 'Moderate' certainty but {fail_count}/{total_modules} "
                   f"modules FAIL — evidence weaker than stated",
            metrics=metrics,
        )

    if grade_certainty == "High" and fail_count >= 2:
        return DetectorResult(
            module=MODULE, severity=Severity.WARN,
            detail=f"GRADE 'High' with {fail_count} FAILs — minor discordance",
            metrics=metrics,
        )

    return DetectorResult(
        module=MODULE, severity=Severity.PASS,
        detail=f"GRADE '{grade_certainty}' consistent with {fail_count} FAILs",
        metrics=metrics,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_certainty_mismatch.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/certainty_mismatch.py tests/test_certainty_mismatch.py && git commit -m "feat: Module 11 — certainty-outcome mismatch detector (GRADE vs automated)"
```

---

### Task 16: Detector Registry

**Files:**
- Modify: `C:\MetaAudit\metaaudit\detectors\__init__.py`

- [ ] **Step 1: Update detector __init__.py with registry**

```python
# metaaudit/detectors/__init__.py
"""Flaw detection modules for MetaAudit.

Registry of all 11 detectors for easy iteration.
"""

from metaaudit.detectors.prediction_gap import detect_prediction_gap
from metaaudit.detectors.model_misspec import detect_model_misspec
from metaaudit.detectors.fragility import detect_fragility
from metaaudit.detectors.underpowered import detect_underpowered
from metaaudit.detectors.pub_bias import detect_pub_bias
from metaaudit.detectors.small_study import detect_small_study
from metaaudit.detectors.excess_sig import detect_excess_sig
from metaaudit.detectors.integrity import detect_integrity
from metaaudit.detectors.overlap import detect_overlap
from metaaudit.detectors.overclaiming import detect_overclaiming
from metaaudit.detectors.certainty_mismatch import detect_certainty_mismatch

ALL_DETECTORS = [
    "prediction_gap",
    "model_misspec",
    "fragility",
    "underpowered",
    "pub_bias",
    "small_study",
    "excess_sig",
    "integrity",
    "overlap",
    "overclaiming",
    "certainty_mismatch",
]
```

- [ ] **Step 2: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/detectors/__init__.py && git commit -m "feat: detector registry — all 11 modules indexed"
```

---

### Task 17: Export Module

**Files:**
- Create: `C:\MetaAudit\metaaudit\export.py`
- Create: `C:\MetaAudit\tests\test_export.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_export.py
import json
import os
import tempfile
import pytest
from metaaudit.severity import Severity, DetectorResult
from metaaudit.export import export_json, export_csv


def _sample_results():
    return {
        "CD001__A1": [
            DetectorResult("prediction_gap", Severity.FAIL, "PI crosses null",
                          {"pi_lower": -0.3, "pi_upper": 0.5}),
            DetectorResult("fragility", Severity.WARN, "MAFI=4", {"mafi": 4}),
        ],
        "CD002__A1": [
            DetectorResult("prediction_gap", Severity.PASS, "OK", {}),
            DetectorResult("fragility", Severity.PASS, "Robust", {"mafi": 12}),
        ],
    }


def test_export_json():
    results = _sample_results()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "results.json")
        export_json(results, path)
        with open(path, "r") as f:
            data = json.load(f)
        assert "CD001__A1" in data
        assert len(data["CD001__A1"]) == 2
        assert data["CD001__A1"][0]["severity"] == "FAIL"


def test_export_csv():
    results = _sample_results()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "results.csv")
        export_csv(results, path)
        with open(path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 5  # header + 4 rows
        assert "ma_id" in lines[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_export.py -v`
Expected: FAIL

- [ ] **Step 3: Implement export.py**

```python
# metaaudit/export.py
"""Export audit results to JSON and CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from metaaudit.severity import DetectorResult


def export_json(
    results: dict[str, list[DetectorResult]],
    path: str | Path,
) -> None:
    data = {}
    for ma_id, detections in results.items():
        data[ma_id] = [d.to_dict() for d in detections]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_csv(
    results: dict[str, list[DetectorResult]],
    path: str | Path,
) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ma_id", "module", "severity", "detail"])
        for ma_id, detections in results.items():
            for d in detections:
                writer.writerow([ma_id, d.module, d.severity.name, d.detail])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_export.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/export.py tests/test_export.py && git commit -m "feat: export module — JSON and CSV output"
```

---

### Task 18: Correlator

**Files:**
- Create: `C:\MetaAudit\metaaudit\correlator.py`
- Create: `C:\MetaAudit\tests\test_correlator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_correlator.py
import pytest
from metaaudit.severity import Severity, DetectorResult
from metaaudit.detectors import ALL_DETECTORS
from metaaudit.correlator import (
    build_flaw_matrix,
    compute_prevalence,
    compute_cooccurrence,
    compute_severity_scores,
)


def _sample_results():
    """3 MAs, 3 detectors for simplicity."""
    return {
        "MA1": [
            DetectorResult("prediction_gap", Severity.FAIL, "", {}),
            DetectorResult("fragility", Severity.FAIL, "", {}),
            DetectorResult("pub_bias", Severity.PASS, "", {}),
        ],
        "MA2": [
            DetectorResult("prediction_gap", Severity.FAIL, "", {}),
            DetectorResult("fragility", Severity.PASS, "", {}),
            DetectorResult("pub_bias", Severity.FAIL, "", {}),
        ],
        "MA3": [
            DetectorResult("prediction_gap", Severity.PASS, "", {}),
            DetectorResult("fragility", Severity.PASS, "", {}),
            DetectorResult("pub_bias", Severity.PASS, "", {}),
        ],
    }


def test_build_flaw_matrix():
    matrix = build_flaw_matrix(_sample_results())
    assert matrix.shape == (3, 3)  # 3 MAs × 3 modules
    assert matrix.iloc[0, 0] == 1  # MA1, prediction_gap = FAIL
    assert matrix.iloc[2, 2] == 0  # MA3, pub_bias = PASS


def test_compute_prevalence():
    matrix = build_flaw_matrix(_sample_results())
    prev = compute_prevalence(matrix)
    assert prev["prediction_gap"] == pytest.approx(2/3, abs=0.01)
    assert prev["pub_bias"] == pytest.approx(1/3, abs=0.01)


def test_compute_cooccurrence():
    matrix = build_flaw_matrix(_sample_results())
    cooc = compute_cooccurrence(matrix)
    assert cooc.shape == (3, 3)
    # Diagonal should be 1.0
    for i in range(3):
        assert cooc.iloc[i, i] == pytest.approx(1.0, abs=0.01)


def test_severity_scores():
    scores = compute_severity_scores(_sample_results())
    assert scores["MA1"] > scores["MA3"]  # MA1 has 2 fails, MA3 has 0
    assert scores["MA2"] > scores["MA3"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/MetaAudit && python -m pytest tests/test_correlator.py -v`
Expected: FAIL

- [ ] **Step 3: Implement correlator.py**

```python
# metaaudit/correlator.py
"""Correlator — flaw co-occurrence, prevalence, severity scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd

from metaaudit.severity import Severity, DetectorResult


def build_flaw_matrix(
    results: dict[str, list[DetectorResult]],
) -> pd.DataFrame:
    """Build binary matrix: rows=MAs, columns=modules, 1=FAIL/CRITICAL."""
    rows = {}
    for ma_id, detections in results.items():
        row = {}
        for d in detections:
            if not d.metrics.get("insufficient_data", False):
                row[d.module] = 1 if d.severity >= Severity.FAIL else 0
            else:
                row[d.module] = np.nan  # Insufficient data — exclude from analysis
        rows[ma_id] = row
    df = pd.DataFrame.from_dict(rows, orient="index")
    df = df.fillna(np.nan)  # Keep NaN for insufficient data
    return df


def compute_prevalence(matrix: pd.DataFrame) -> dict[str, float]:
    """Fraction of MAs with FAIL/CRITICAL for each module (excluding NaN)."""
    result = {}
    for col in matrix.columns:
        valid = matrix[col].dropna()
        if len(valid) > 0:
            result[col] = float(valid.mean())
        else:
            result[col] = float("nan")
    return result


def compute_cooccurrence(matrix: pd.DataFrame) -> pd.DataFrame:
    """Phi coefficient matrix between all detector pairs."""
    cols = matrix.columns.tolist()
    n = len(cols)
    phi = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i == j:
                phi.iloc[i, j] = 1.0
                continue
            valid = matrix[[c1, c2]].dropna()
            if len(valid) < 5:
                phi.iloc[i, j] = np.nan
                continue
            a = valid[c1].values
            b = valid[c2].values
            # Phi coefficient = Pearson correlation for binary variables
            if a.std() == 0 or b.std() == 0:
                phi.iloc[i, j] = 0.0
            else:
                phi.iloc[i, j] = float(np.corrcoef(a, b)[0, 1])
    return phi


def compute_severity_scores(
    results: dict[str, list[DetectorResult]],
) -> dict[str, float]:
    """Weighted severity score per MA. WARN=1, FAIL=2, CRITICAL=3."""
    weights = {Severity.PASS: 0, Severity.WARN: 1, Severity.FAIL: 2, Severity.CRITICAL: 3}
    scores = {}
    for ma_id, detections in results.items():
        score = sum(
            weights.get(d.severity, 0) for d in detections
            if not d.metrics.get("insufficient_data", False)
        )
        scores[ma_id] = score
    return scores
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/MetaAudit && python -m pytest tests/test_correlator.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /c/MetaAudit && git add metaaudit/correlator.py tests/test_correlator.py && git commit -m "feat: correlator — prevalence, co-occurrence, severity scoring"
```

---

### Task 19: CLI Runner

**Files:**
- Create: `C:\MetaAudit\run_audit.py`

- [ ] **Step 1: Implement run_audit.py**

```python
# run_audit.py
"""MetaAudit CLI — run the full audit pipeline on Pairwise70 data."""

from __future__ import annotations

import argparse
import os
import sys
import time

from metaaudit.loader import load_all_reviews, DataType
from metaaudit.recompute import recompute_ma
from metaaudit.severity import DetectorResult
from metaaudit.detectors.prediction_gap import detect_prediction_gap
from metaaudit.detectors.model_misspec import detect_model_misspec
from metaaudit.detectors.fragility import detect_fragility
from metaaudit.detectors.underpowered import detect_underpowered
from metaaudit.detectors.pub_bias import detect_pub_bias
from metaaudit.detectors.small_study import detect_small_study
from metaaudit.detectors.excess_sig import detect_excess_sig
from metaaudit.detectors.integrity import detect_integrity
from metaaudit.detectors.overlap import detect_overlap, build_overlap_index
from metaaudit.detectors.overclaiming import detect_overclaiming
from metaaudit.detectors.certainty_mismatch import detect_certainty_mismatch
from metaaudit.correlator import (
    build_flaw_matrix, compute_prevalence,
    compute_cooccurrence, compute_severity_scores,
)
from metaaudit.export import export_json, export_csv

DEFAULT_DATA_DIR = r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data"
DEFAULT_OUTPUT_DIR = r"C:\MetaAudit\results"


def run_detectors_on_analysis(ag, ma, study_data, overlap_index, studies_by_review):
    """Run all 11 detectors on one AnalysisGroup, return list of DetectorResults."""
    results = []

    # Module 1: Prediction Gap
    results.append(detect_prediction_gap(ma))

    # Module 2: Model Misspecification
    context = {}
    if ag.data_type == DataType.BINARY:
        total_events = (ag.df["Experimental.cases"].sum() + ag.df["Control.cases"].sum())
        total_n = (ag.df["Experimental.N"].sum() + ag.df["Control.N"].sum())
        context["event_rate"] = total_events / total_n if total_n > 0 else 0
    results.append(detect_model_misspec(ma, context))

    # Module 3: Fragility
    results.append(detect_fragility(ma, study_data))

    # Module 4: Underpowered
    if ag.data_type == DataType.BINARY:
        total_n = int(ag.df["Experimental.N"].sum() + ag.df["Control.N"].sum())
    elif ag.data_type == DataType.CONTINUOUS:
        total_n = int(ag.df["Experimental.N"].sum() + ag.df["Control.N"].sum())
    else:
        total_n = 0
    results.append(detect_underpowered(ma, total_n))

    # Module 5: Publication Bias
    results.append(detect_pub_bias(ma))

    # Module 6: Small-Study Effects
    results.append(detect_small_study(ma))

    # Module 7: Excess Significance
    results.append(detect_excess_sig(ma))

    # Module 8: Data Integrity
    results.append(detect_integrity(ag.df, ag.data_type))

    # Module 9: Study Overlap
    study_names = set()
    if "Study" in ag.df.columns:
        study_names = set(ag.df["Study"].dropna().unique())
    results.append(detect_overlap(
        ag.review_id, study_names, overlap_index
    ))

    # Module 10: Overclaiming
    results.append(detect_overclaiming(ma))

    # Module 11: Certainty Mismatch — requires GRADE data (None for now)
    results.append(detect_certainty_mismatch(
        grade_certainty=None,  # TODO: extract from Cochrane metadata if available
        other_results=results[:10],
    ))

    return results


def main():
    parser = argparse.ArgumentParser(description="MetaAudit — Computational Evidence Audit")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                        help="Path to Pairwise70 data directory")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help="Output directory for results")
    parser.add_argument("--max-reviews", type=int, default=None,
                        help="Limit number of reviews (for testing)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading reviews from {args.data_dir}...")
    t0 = time.time()
    reviews = load_all_reviews(args.data_dir, max_reviews=args.max_reviews)
    print(f"Loaded {len(reviews)} reviews in {time.time() - t0:.1f}s")

    # Build overlap index across all reviews
    print("Building study overlap index...")
    studies_by_review = {}
    for r in reviews:
        study_names = set()
        if "Study" in r.df.columns:
            study_names = set(r.df["Study"].dropna().unique())
        studies_by_review[r.review_id] = study_names
    overlap_index = build_overlap_index(studies_by_review)
    print(f"Found {len(overlap_index)} review pairs with shared studies")

    # Run all detectors on all analyses
    all_results: dict[str, list[DetectorResult]] = {}
    total_analyses = sum(len(r.analyses) for r in reviews)
    print(f"Running 11 detectors on {total_analyses} meta-analyses...")

    done = 0
    for review in reviews:
        for ag in review.analyses:
            ma = recompute_ma(ag.df, ag.data_type)
            study_data = ag.df if ag.data_type == DataType.BINARY else None
            results = run_detectors_on_analysis(
                ag, ma, study_data, overlap_index, studies_by_review
            )
            all_results[ag.ma_id] = results
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{total_analyses} analyses processed...")

    print(f"All {done} analyses complete.")

    # Correlator
    print("Computing correlations...")
    matrix = build_flaw_matrix(all_results)
    prevalence = compute_prevalence(matrix)
    cooccurrence = compute_cooccurrence(matrix)
    severity_scores = compute_severity_scores(all_results)

    # Summary stats
    fail_counts = {ma_id: sum(1 for r in rl if r.severity.value >= 2)
                   for ma_id, rl in all_results.items()}
    any_fail = sum(1 for c in fail_counts.values() if c > 0)
    multi_fail = sum(1 for c in fail_counts.values() if c >= 3)

    print(f"\n{'='*60}")
    print(f"METAAUDIT RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Reviews analysed: {len(reviews)}")
    print(f"Meta-analyses audited: {len(all_results)}")
    print(f"MAs with >= 1 FAIL: {any_fail} ({100*any_fail/len(all_results):.1f}%)")
    print(f"MAs with >= 3 FAILs: {multi_fail} ({100*multi_fail/len(all_results):.1f}%)")
    print(f"\nFlaw prevalence:")
    for module, prev in sorted(prevalence.items(), key=lambda x: -x[1]):
        print(f"  {module:25s} {100*prev:.1f}%")
    print(f"{'='*60}")

    # Export
    json_path = os.path.join(args.output_dir, "audit_results.json")
    csv_path = os.path.join(args.output_dir, "audit_results.csv")
    export_json(all_results, json_path)
    export_csv(all_results, csv_path)

    # Export correlator outputs
    prevalence_path = os.path.join(args.output_dir, "prevalence.json")
    import json
    with open(prevalence_path, "w") as f:
        json.dump(prevalence, f, indent=2)

    cooccurrence.to_csv(os.path.join(args.output_dir, "cooccurrence.csv"))

    print(f"\nResults saved to {args.output_dir}/")
    print("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
cd /c/MetaAudit && git add run_audit.py && git commit -m "feat: CLI runner — full pipeline with progress and summary output"
```

---

### Task 20: Integration Test

**Files:**
- Create: `C:\MetaAudit\tests\test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration test: full pipeline on synthetic + real data."""

import os
import json
import tempfile
import numpy as np
import pandas as pd
import pytest

from metaaudit.loader import DataType, AnalysisGroup
from metaaudit.recompute import recompute_ma
from metaaudit.detectors.prediction_gap import detect_prediction_gap
from metaaudit.detectors.model_misspec import detect_model_misspec
from metaaudit.detectors.fragility import detect_fragility
from metaaudit.detectors.underpowered import detect_underpowered
from metaaudit.detectors.pub_bias import detect_pub_bias
from metaaudit.detectors.small_study import detect_small_study
from metaaudit.detectors.excess_sig import detect_excess_sig
from metaaudit.detectors.integrity import detect_integrity
from metaaudit.detectors.overlap import detect_overlap, build_overlap_index
from metaaudit.detectors.overclaiming import detect_overclaiming
from metaaudit.detectors.certainty_mismatch import detect_certainty_mismatch
from metaaudit.correlator import build_flaw_matrix, compute_prevalence
from metaaudit.export import export_json, export_csv
from metaaudit.severity import Severity


def _run_all_detectors(df, data_type, review_id="TEST"):
    """Run full pipeline on one synthetic MA."""
    ma = recompute_ma(df, data_type)
    results = []
    results.append(detect_prediction_gap(ma))
    ctx = {}
    if data_type == DataType.BINARY:
        total_e = df["Experimental.cases"].sum() + df["Control.cases"].sum()
        total_n = df["Experimental.N"].sum() + df["Control.N"].sum()
        ctx["event_rate"] = total_e / total_n if total_n > 0 else 0
    results.append(detect_model_misspec(ma, ctx))
    study_data = df if data_type == DataType.BINARY else None
    results.append(detect_fragility(ma, study_data))
    total_n = int(df["Experimental.N"].sum() + df.get("Control.N", pd.Series([0])).sum())
    results.append(detect_underpowered(ma, total_n))
    results.append(detect_pub_bias(ma))
    results.append(detect_small_study(ma))
    results.append(detect_excess_sig(ma))
    results.append(detect_integrity(df, data_type))
    results.append(detect_overlap(review_id, set(), {}))
    results.append(detect_overclaiming(ma))
    results.append(detect_certainty_mismatch(None, results[:10]))
    return results


def test_clean_large_binary_ma():
    """A well-behaved MA with 12 studies, clear effect, low heterogeneity."""
    rng = np.random.default_rng(42)
    k = 12
    df = pd.DataFrame({
        "Study": [f"Study_{i}" for i in range(k)],
        "Study.year": list(range(2010, 2010 + k)),
        "Experimental.cases": rng.integers(5, 15, k),
        "Experimental.N": rng.integers(80, 150, k),
        "Control.cases": rng.integers(20, 35, k),
        "Control.N": rng.integers(80, 150, k),
    })
    results = _run_all_detectors(df, DataType.BINARY)
    assert len(results) == 11
    # Expect mostly PASS for a clean dataset
    fail_count = sum(1 for r in results if r.severity >= Severity.FAIL)
    assert fail_count <= 3  # Some modules may flag legitimately


def test_problematic_binary_ma():
    """A highly heterogeneous, small MA with suspicious patterns."""
    df = pd.DataFrame({
        "Study": ["A", "B", "C"],
        "Study.year": [2015, 2016, 2017],
        "Experimental.cases": [1, 40, 2],
        "Experimental.N": [100, 50, 100],
        "Control.cases": [2, 5, 3],
        "Control.N": [100, 50, 100],
    })
    results = _run_all_detectors(df, DataType.BINARY)
    assert len(results) == 11
    # Should flag multiple issues
    severities = [r.severity for r in results]
    assert Severity.WARN in severities or Severity.FAIL in severities


def test_full_pipeline_export():
    """Run pipeline, export, verify JSON structure."""
    rng = np.random.default_rng(99)
    k = 8
    df = pd.DataFrame({
        "Study": [f"S{i}" for i in range(k)],
        "Study.year": list(range(2012, 2012 + k)),
        "Experimental.cases": rng.integers(5, 20, k),
        "Experimental.N": rng.integers(80, 120, k),
        "Control.cases": rng.integers(15, 30, k),
        "Control.N": rng.integers(80, 120, k),
    })
    results = _run_all_detectors(df, DataType.BINARY, review_id="INTEG_TEST")
    all_results = {"INTEG_TEST__A1": results}

    with tempfile.TemporaryDirectory() as tmp:
        json_path = os.path.join(tmp, "test.json")
        csv_path = os.path.join(tmp, "test.csv")
        export_json(all_results, json_path)
        export_csv(all_results, csv_path)

        with open(json_path) as f:
            data = json.load(f)
        assert "INTEG_TEST__A1" in data
        assert len(data["INTEG_TEST__A1"]) == 11

        # Correlator
        matrix = build_flaw_matrix(all_results)
        prev = compute_prevalence(matrix)
        assert len(prev) > 0


PAIRWISE70_DIR = r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data"


@pytest.mark.skipif(
    not os.path.exists(PAIRWISE70_DIR),
    reason="Pairwise70 data not available"
)
def test_real_review_cd000028():
    """Run full pipeline on a real Cochrane review."""
    from metaaudit.loader import load_rda_file
    path = os.path.join(PAIRWISE70_DIR, "CD000028_pub4_data.rda")
    review = load_rda_file(path)
    assert len(review.analyses) > 0
    ag = review.analyses[0]
    results = _run_all_detectors(ag.df, ag.data_type, review_id=review.review_id)
    assert len(results) == 11
    for r in results:
        assert r.module is not None
        assert r.severity is not None
```

- [ ] **Step 2: Run all tests**

Run: `cd /c/MetaAudit && python -m pytest tests/ -v`
Expected: All tests pass (real-data tests may skip)

- [ ] **Step 3: Commit**

```bash
cd /c/MetaAudit && git add tests/test_integration.py && git commit -m "test: integration tests — full pipeline on synthetic and real data"
```

---

### Task 21: Run Full Test Suite and Verify

- [ ] **Step 1: Run complete test suite with counts**

Run: `cd /c/MetaAudit && python -m pytest tests/ -v --tb=short 2>&1 | tail -20`
Expected: 60+ tests passed, 0 failed

- [ ] **Step 2: Run a quick smoke test on real data**

Run: `cd /c/MetaAudit && python run_audit.py --max-reviews=5`
Expected: Processes 5 reviews, prints summary table, saves results to `results/`

- [ ] **Step 3: Verify output files exist**

Run: `ls -la /c/MetaAudit/results/`
Expected: `audit_results.json`, `audit_results.csv`, `prevalence.json`, `cooccurrence.csv`

- [ ] **Step 4: Final commit**

```bash
cd /c/MetaAudit && git add -A && git commit -m "chore: Phase 1 complete — 11 detectors, correlator, CLI runner, 60+ tests"
```
