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
    """Compute Hedges' g (bias-corrected SMD) and sampling variances.

    Guards against n_total < 3 (df < 1) which would cause division by zero.
    Invalid studies (df < 1) are returned as NaN.
    """
    n_total = e_n + c_n
    df = n_total - 2
    # Guard: need df >= 1 for pooled SD and Hedges' J
    invalid = df < 1
    df_safe = np.where(invalid, 1, df)  # avoid division by zero in computation
    sp = np.sqrt(((e_n - 1) * e_sd ** 2 + (c_n - 1) * c_sd ** 2) / df_safe)
    d = (e_mean - c_mean) / np.where(sp == 0, np.finfo(float).eps, sp)
    j = 1.0 - 3.0 / (4.0 * df_safe - 1.0)
    yi = j * d
    # P1-1 fix: use df (not n_total) in variance denominator per Hedges (1981)
    vi = (n_total / (e_n * c_n)) + (yi ** 2) / (2.0 * df_safe)
    # Mark invalid studies as NaN
    yi = np.where(invalid, np.nan, yi)
    vi = np.where(invalid, np.nan, vi)
    return yi, vi


def _reml_tau2(yi: np.ndarray, vi: np.ndarray, max_iter: int = 100,
               tol: float = 1e-6) -> tuple[float, bool]:
    """Estimate tau² using true REML Fisher scoring with DL starting value.

    Returns (tau2, converged). If not converged, caller should fall back to DL.
    """
    k = len(yi)
    if k < 2:
        return 0.0, True
    # DL starting value
    wi = 1.0 / vi
    w_sum = wi.sum()
    theta_fe = (wi * yi).sum() / w_sum
    Q = ((yi - theta_fe) ** 2 * wi).sum()
    c = w_sum - (wi ** 2).sum() / w_sum
    tau2 = max(0.0, (Q - (k - 1)) / c)
    converged = False
    for _ in range(max_iter):
        w = 1.0 / (vi + tau2)
        w_sum = w.sum()
        theta = (w * yi).sum() / w_sum
        resid = yi - theta
        # REML gradient: 0.5 * (Q_w - (k-1)) where Q_w = sum(w^2 * resid^2)
        Q_w = (w * resid ** 2).sum()
        # REML Fisher information:
        # I = 0.5 * (sum(w^2) - 2*sum(w^3)/sum(w) + (sum(w^2)/sum(w))^2)
        w2 = (w ** 2).sum()
        w3 = (w ** 3).sum()
        info = 0.5 * (w2 - 2.0 * w3 / w_sum + (w2 / w_sum) ** 2)
        if info <= 0:
            break
        gradient = 0.5 * (Q_w - (k - 1))
        tau2_new = max(0.0, tau2 + gradient / info)
        if abs(tau2_new - tau2) < tol:
            tau2 = tau2_new
            converged = True
            break
        tau2 = tau2_new
    else:
        converged = False
    return tau2, converged


def pool_effects_reml(yi: np.ndarray, vi: np.ndarray) -> dict:
    """Pool effects using REML random-effects model with HKSJ adjustment."""
    k = len(yi)
    tau2, converged = _reml_tau2(yi, vi)
    if not converged:
        # Fall back to DerSimonian-Laird (closed-form)
        wi = 1.0 / vi
        w_sum = wi.sum()
        theta_fe = (wi * yi).sum() / w_sum
        Q_dl = ((yi - theta_fe) ** 2 * wi).sum()
        c = w_sum - (wi ** 2).sum() / w_sum
        tau2 = max(0.0, (Q_dl - (k - 1)) / c)
    w = 1.0 / (vi + tau2)
    w_sum = w.sum()
    estimate = (w * yi).sum() / w_sum
    se = 1.0 / np.sqrt(w_sum)
    theta_w = estimate
    q_resid = (w * (yi - theta_w) ** 2).sum()
    hksj_factor = q_resid / (k - 1) if k > 1 else 1.0
    se_hksj = se * np.sqrt(max(1.0, hksj_factor))
    df = max(1, k - 1)
    t_crit = stats.t.ppf(0.975, df)
    ci_lower = estimate - t_crit * se_hksj
    ci_upper = estimate + t_crit * se_hksj
    t_stat = estimate / se_hksj if se_hksj > 0 else 0.0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
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
        "converged": converged,
    }


def compute_prediction_interval(
    estimate: float, se_hksj: float, tau2: float, k: int
) -> dict:
    """Compute 95% prediction interval (Higgins-Thompson-Spiegelhalter).

    Uses HKSJ-adjusted SE so the PI correctly accounts for uncertainty in
    the pooled estimate.
    """
    if k < 3:
        return {"pi_lower": float("-inf"), "pi_upper": float("inf"),
                "computable": False}
    df = k - 2
    t_crit = stats.t.ppf(0.975, df)
    pi_se = np.sqrt(se_hksj ** 2 + tau2)
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
    yi: np.ndarray
    vi: np.ndarray
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
    measure: str


def _extract_effects(df, data_type: DataType) -> tuple[np.ndarray, np.ndarray, str]:
    if data_type == DataType.BINARY:
        yi, vi = compute_log_or(
            df["Experimental.cases"].values,
            df["Experimental.N"].values,
            df["Control.cases"].values,
            df["Control.N"].values,
        )
        return yi, vi, "logOR"
    elif data_type == DataType.CONTINUOUS:
        yi, vi = compute_md(
            df["Experimental.mean"].values,
            df["Experimental.SD"].values,
            df["Experimental.N"].values,
            df["Control.mean"].values,
            df["Control.SD"].values,
            df["Control.N"].values,
        )
        return yi, vi, "MD"
    else:
        yi = df["GIV.Mean"].values.astype(float)
        vi = (df["GIV.SE"].values.astype(float)) ** 2
        return yi, vi, "GIV"


def recompute_ma(df, data_type: DataType) -> RecomputedMA:
    yi, vi, measure = _extract_effects(df, data_type)
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
        pooled["estimate"], pooled["se_hksj"], pooled["tau2"], k
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
