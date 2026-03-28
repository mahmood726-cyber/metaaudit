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
