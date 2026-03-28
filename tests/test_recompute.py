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
    yi, vi = compute_log_or(
        e_cases=np.array([0]),
        e_n=np.array([50]),
        c_cases=np.array([5]),
        c_n=np.array([50]),
    )
    assert np.isfinite(yi[0])
    assert yi[0] < 0


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
    assert -0.70 < yi[0] < -0.55


def test_pool_reml_homogeneous():
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
        estimate=-0.5, se_hksj=0.1, tau2=0.05, k=5
    )
    assert pi["pi_lower"] < -0.5
    assert pi["pi_upper"] > -0.5
    ci_width = 2 * 1.96 * 0.1
    pi_width = pi["pi_upper"] - pi["pi_lower"]
    assert pi_width > ci_width


def test_recompute_ma_binary(binary_study_data):
    result = recompute_ma(binary_study_data, DataType.BINARY)
    assert isinstance(result, RecomputedMA)
    assert result.k == 5
    assert result.estimate < 0
    assert result.ci_lower < result.estimate < result.ci_upper
    assert 0.0 <= result.I2 <= 100.0


def test_recompute_ma_continuous(continuous_study_data):
    result = recompute_ma(continuous_study_data, DataType.CONTINUOUS)
    assert result.k == 4
    assert result.estimate < 0
