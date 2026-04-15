"""
MetaAudit — Pre-Registered Sensitivity Analyses
================================================
4 analyses as specified in docs/osf-preregistration.md:
  SA1: Threshold ±10% shifts on all numeric detector thresholds
  SA2: Exclude k < 5 MAs from prevalence calculations
  SA3: Binary outcomes only
  SA4: Compare REML tau² vs DL tau² (first 100 MAs)

Results saved to:
  C:/MetaAudit/results/sensitivity_results.md
  C:/MetaAudit/results/sensitivity_data.json
"""

from __future__ import annotations

import io
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# UTF-8 stdout (Windows cp1252 safety)
# ---------------------------------------------------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent


def _resolve_pairwise_dir():
    env_data = os.getenv("METAAUDIT_DATA_DIR") or os.getenv("PAIRWISE70_DATA_DIR")
    candidates = []
    if env_data:
        candidates.append(Path(env_data).expanduser())
    candidates.extend([
        PROJECT_ROOT.parent / "Projects" / "Pairwise70" / "data",
        PROJECT_ROOT.parent / "Models" / "Pairwise70" / "data",
    ])
    return next((path.resolve() for path in candidates if path.exists()), candidates[0].resolve())


AUDIT_JSON = PROJECT_ROOT / "results" / "audit_results.json"
OUTPUT_MD = PROJECT_ROOT / "results" / "sensitivity_results.md"
OUTPUT_JSON = PROJECT_ROOT / "results" / "sensitivity_data.json"
DATA_DIR = _resolve_pairwise_dir()

# ---------------------------------------------------------------------------
# Load audit results
# ---------------------------------------------------------------------------
print("Loading audit_results.json...")
with open(AUDIT_JSON) as f:
    AUDIT = json.load(f)
N_TOTAL = len(AUDIT)
print(f"  {N_TOTAL} meta-analyses loaded.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_fail(severity: str) -> bool:
    return severity in ("FAIL", "CRITICAL")


def baseline_counts(audit: dict) -> dict:
    """Compute baseline any_fail%, multi_fail%, and per-module FAIL prevalences."""
    any_fail = sum(1 for rl in audit.values() if any(is_fail(r["severity"]) for r in rl))
    multi_fail = sum(
        1 for rl in audit.values()
        if sum(1 for r in rl if is_fail(r["severity"])) >= 3
    )
    modules = ["prediction_gap", "model_misspec", "fragility", "underpowered",
               "pub_bias", "small_study", "excess_sig", "integrity", "overlap",
               "overclaiming"]
    prev = {}
    for mod in modules:
        vals = []
        for rl in audit.values():
            for r in rl:
                if r["module"] == mod:
                    if not r["metrics"].get("insufficient_data", False):
                        vals.append(1 if is_fail(r["severity"]) else 0)
                    break
        prev[mod] = 100 * sum(vals) / len(vals) if vals else float("nan")
    n = len(audit)
    return {
        "n": n,
        "any_fail_pct": 100 * any_fail / n,
        "multi_fail_pct": 100 * multi_fail / n,
        "module_prev": prev,
    }


def compute_summary(subset: dict) -> dict:
    """any_fail%, multi_fail% for a subset of the audit dict."""
    n = len(subset)
    if n == 0:
        return {"n": 0, "any_fail_pct": float("nan"), "multi_fail_pct": float("nan")}
    any_fail = sum(1 for rl in subset.values() if any(is_fail(r["severity"]) for r in rl))
    multi_fail = sum(
        1 for rl in subset.values()
        if sum(1 for r in rl if is_fail(r["severity"])) >= 3
    )
    modules = ["prediction_gap", "model_misspec", "fragility", "underpowered",
               "pub_bias", "small_study", "excess_sig", "integrity", "overlap",
               "overclaiming"]
    prev = {}
    for mod in modules:
        vals = []
        for rl in subset.values():
            for r in rl:
                if r["module"] == mod:
                    if not r["metrics"].get("insufficient_data", False):
                        vals.append(1 if is_fail(r["severity"]) else 0)
                    break
        prev[mod] = 100 * sum(vals) / len(vals) if vals else float("nan")
    return {
        "n": n,
        "any_fail_pct": 100 * any_fail / n,
        "multi_fail_pct": 100 * multi_fail / n,
        "module_prev": prev,
    }


# ---------------------------------------------------------------------------
# SA1 — Threshold sensitivity (±10% shifts)
# ---------------------------------------------------------------------------
print("\nSA1: Threshold sensitivity analysis...")

# Re-classify each MA under shifted thresholds.
# For each detector, look at its stored metrics and re-apply shifted thresholds.
# Modules without a numeric threshold to shift:
#   prediction_gap, integrity, overlap, certainty_mismatch (keep as-is).

def _is_insufficient(r: dict) -> bool:
    return r["metrics"].get("insufficient_data", False)


def reclassify_model_misspec(r: dict, i2_thresh: float) -> str:
    if _is_insufficient(r):
        return r["severity"]
    I2 = r["metrics"].get("I2", 0.0)
    if I2 > i2_thresh:
        return "FAIL"
    # Keep event_rate WARN logic — not affected by ±10% shift on I2
    event_rate = r["metrics"].get("event_rate")
    measure = r["metrics"].get("measure", "")
    is_ratio = measure in ("logOR", "logRR", "OR", "RR")
    if is_ratio and event_rate is not None and event_rate > 0.20:
        return "WARN"
    return "PASS"


def reclassify_fragility(r: dict, mafi_fail: int) -> str:
    if _is_insufficient(r):
        return r["severity"]
    mafi = r["metrics"].get("mafi")
    if mafi is None:
        return r["severity"]
    if mafi <= mafi_fail:
        return "FAIL"
    if mafi <= 5:
        return "WARN"
    return "PASS"


def reclassify_underpowered(r: dict, ois_thresh: int) -> str:
    if _is_insufficient(r):
        return r["severity"]
    k = r["metrics"].get("k", 99)
    total_n = r["metrics"].get("total_n", 99999)
    significant = r["metrics"].get("significant", False)
    # k thresholds stay fixed (can't shift integer boundary meaningfully)
    if k < 3:
        return "FAIL" if significant else "WARN"
    if k < 5:
        return "WARN"
    if total_n < ois_thresh and significant:
        return "WARN"
    return "PASS"


def reclassify_pub_bias(r: dict, p_thresh: float) -> str:
    if _is_insufficient(r):
        return r["severity"]
    egger_p = r["metrics"].get("egger_p") or 1.0
    begg_p  = r["metrics"].get("begg_p")  or 1.0
    k0      = r["metrics"].get("trimfill_k0", 0) or 0
    trimfill_pos = k0 >= 2
    # Guard: None values treated as non-significant (p=1.0)
    if egger_p is None:
        egger_p = 1.0
    if begg_p is None:
        begg_p = 1.0
    n_pos = sum([egger_p < p_thresh, begg_p < p_thresh, trimfill_pos])
    if n_pos >= 2:
        return "FAIL"
    if n_pos == 1:
        return "WARN"
    return "PASS"


def reclassify_small_study(r: dict, p_thresh: float, rho_thresh: float) -> str:
    if _is_insufficient(r):
        return r["severity"]
    precision_p = r["metrics"].get("peters_p", 1.0)
    spearman_rho = r["metrics"].get("spearman_rho", 0.0)
    spearman_p   = r["metrics"].get("spearman_p", 1.0)
    small_larger = r["metrics"].get("small_studies_larger", False)
    prec_pos = precision_p < p_thresh
    spearman_pos = (spearman_p < p_thresh) and small_larger
    if prec_pos and spearman_rho > rho_thresh:
        return "FAIL"
    if prec_pos or spearman_pos:
        return "WARN"
    return "PASS"


def reclassify_excess_sig(r: dict, oe_thresh: float, p_thresh: float) -> str:
    if _is_insufficient(r):
        return r["severity"]
    oe_ratio = r["metrics"].get("oe_ratio", 0.0)
    p_excess = r["metrics"].get("p_excess", 1.0)
    if oe_ratio > oe_thresh and p_excess < p_thresh:
        return "FAIL"
    if oe_ratio > oe_thresh:
        return "WARN"
    return "PASS"


def reclassify_overclaiming(r: dict, mcid_logOR: float) -> str:
    if _is_insufficient(r):
        return r["severity"]
    effect_abs = r["metrics"].get("effect_abs")
    if effect_abs is None:
        return r["severity"]
    measure = r["metrics"].get("measure", "")
    mcid_orig = r["metrics"].get("mcid")
    if mcid_orig is None:
        return r["severity"]
    # Only shift MCID for logOR and logRR (same threshold used); others stay
    if measure in ("logOR", "logRR"):
        mcid = mcid_logOR
    else:
        mcid = mcid_orig
    fraction = effect_abs / mcid if mcid > 0 else float("inf")
    if fraction < 0.50:
        return "FAIL"
    if fraction < 1.0:
        return "WARN"
    return "PASS"


def apply_threshold_shift(audit: dict, cfg: dict) -> dict:
    """Return a new audit-like dict with re-classified severities.

    cfg keys:
      i2_thresh, mafi_fail, ois_thresh, pub_p, ss_p, ss_rho, es_oe, es_p, mcid_logOR
    """
    shifted = {}
    for ma_id, rl in audit.items():
        new_rl = []
        for r in rl:
            mod = r["module"]
            if mod == "model_misspec":
                new_sev = reclassify_model_misspec(r, cfg["i2_thresh"])
            elif mod == "fragility":
                new_sev = reclassify_fragility(r, cfg["mafi_fail"])
            elif mod == "underpowered":
                new_sev = reclassify_underpowered(r, cfg["ois_thresh"])
            elif mod == "pub_bias":
                new_sev = reclassify_pub_bias(r, cfg["pub_p"])
            elif mod == "small_study":
                new_sev = reclassify_small_study(r, cfg["ss_p"], cfg["ss_rho"])
            elif mod == "excess_sig":
                new_sev = reclassify_excess_sig(r, cfg["es_oe"], cfg["es_p"])
            elif mod == "overclaiming":
                new_sev = reclassify_overclaiming(r, cfg["mcid_logOR"])
            else:
                # prediction_gap, integrity, overlap, certainty_mismatch: keep original
                new_sev = r["severity"]
            new_rl.append({**r, "severity": new_sev})
        shifted[ma_id] = new_rl
    return shifted


# Baseline config
LOGIT_1_25 = math.log(1.25)  # 0.22314

BASE_CFG = dict(
    i2_thresh=50.0, mafi_fail=2, ois_thresh=1600,
    pub_p=0.10, ss_p=0.10, ss_rho=0.40,
    es_oe=1.5, es_p=0.10, mcid_logOR=LOGIT_1_25,
)

# Stricter (-10%)
STRICT_CFG = dict(
    i2_thresh=45.0, mafi_fail=1, ois_thresh=1440,
    pub_p=0.09, ss_p=0.09, ss_rho=0.36,
    es_oe=1.35, es_p=0.09, mcid_logOR=LOGIT_1_25 * 0.90,
)

# Lenient (+10%)
LENIENT_CFG = dict(
    i2_thresh=55.0, mafi_fail=3, ois_thresh=1760,
    pub_p=0.11, ss_p=0.11, ss_rho=0.44,
    es_oe=1.65, es_p=0.11, mcid_logOR=LOGIT_1_25 * 1.10,
)

strict_audit  = apply_threshold_shift(AUDIT, STRICT_CFG)
lenient_audit = apply_threshold_shift(AUDIT, LENIENT_CFG)

base_summary   = compute_summary(AUDIT)
strict_summary = compute_summary(strict_audit)
lenient_summary = compute_summary(lenient_audit)

print(f"  Base:    any_fail={base_summary['any_fail_pct']:.1f}%  multi_fail={base_summary['multi_fail_pct']:.1f}%")
print(f"  Strict:  any_fail={strict_summary['any_fail_pct']:.1f}%  multi_fail={strict_summary['multi_fail_pct']:.1f}%")
print(f"  Lenient: any_fail={lenient_summary['any_fail_pct']:.1f}%  multi_fail={lenient_summary['multi_fail_pct']:.1f}%")


# ---------------------------------------------------------------------------
# SA2 — Exclude k < 5
# ---------------------------------------------------------------------------
print("\nSA2: Excluding k < 5 meta-analyses...")

def get_k(rl: list) -> int | None:
    for r in rl:
        if r["module"] == "underpowered":
            return r["metrics"].get("k")
    return None

k5_audit = {ma_id: rl for ma_id, rl in AUDIT.items() if (get_k(rl) or 0) >= 5}
sa2_summary = compute_summary(k5_audit)
print(f"  k>=5 subset: n={sa2_summary['n']}/{N_TOTAL}")
print(f"  any_fail={sa2_summary['any_fail_pct']:.1f}%  multi_fail={sa2_summary['multi_fail_pct']:.1f}%")


# ---------------------------------------------------------------------------
# SA3 — Binary outcomes only
# ---------------------------------------------------------------------------
print("\nSA3: Binary outcomes only...")

def get_data_type(rl: list) -> str:
    for r in rl:
        if r["module"] == "integrity":
            return r["metrics"].get("data_type", "unknown")
    return "unknown"

binary_audit = {ma_id: rl for ma_id, rl in AUDIT.items() if get_data_type(rl) == "binary"}
sa3_summary = compute_summary(binary_audit)
print(f"  Binary subset: n={sa3_summary['n']}/{N_TOTAL}")
print(f"  any_fail={sa3_summary['any_fail_pct']:.1f}%  multi_fail={sa3_summary['multi_fail_pct']:.1f}%")


# ---------------------------------------------------------------------------
# SA4 — REML vs DL tau2 (first 100 MAs)
# ---------------------------------------------------------------------------
print("\nSA4: REML vs DL tau2 comparison (first 100 MAs)...")

# Need to recompute from raw data.
# Import MetaAudit pipeline components.
import sys
sys.path.insert(0, "C:/MetaAudit")
from metaaudit.loader import load_all_reviews, DataType
from metaaudit.recompute import _extract_effects, _reml_tau2

def _dl_tau2(yi: np.ndarray, vi: np.ndarray) -> float:
    """DerSimonian-Laird tau2 (closed-form)."""
    k = len(yi)
    if k < 2:
        return 0.0
    wi = 1.0 / vi
    w_sum = wi.sum()
    theta_fe = (wi * yi).sum() / w_sum
    Q = ((yi - theta_fe) ** 2 * wi).sum()
    c = w_sum - (wi ** 2).sum() / w_sum
    return max(0.0, (Q - (k - 1)) / c)


def severity_classification(tau2: float, I2: float, total_n: int, k: int,
                             significant: bool, yi: np.ndarray,
                             vi: np.ndarray) -> dict[str, str]:
    """Return severity for detectors that depend on tau2/I2."""
    # model_misspec: FAIL if I2 > 50
    # (pub_bias, small_study: don't use tau2 directly for classification)
    # We need to know if tau2 change shifts I2 at all (I2 from Q is independent of tau2)
    # Actually I2 = max(0, 100*(Q-(k-1))/Q) is independent of tau2.
    # The detectors that use tau2 directly:
    #   - pub_bias: uses tau2 for trim-and-fill (but classification via p-values, not tau2)
    #   - prediction interval: uses tau2 => prediction_gap severity
    # For simplicity, track which detectors would change classification if tau2 differs.
    # The key difference: PI = estimate +/- t * sqrt(se_hksj^2 + tau2)
    # We check if prediction_gap classification changes.
    # (model_misspec I2 does not depend on tau2 estimator)
    return {}  # filled inline below


# Load first ~100 MAs worth of reviews
print("  Loading review data for first 100 MAs...")
reviews = load_all_reviews(DATA_DIR, max_reviews=None)

# Build MA list in same order as AUDIT JSON
ma_ids_ordered = list(AUDIT.keys())[:100]

# Build a lookup: ma_id -> analysis group
ag_lookup = {}
for rv in reviews:
    for ag in rv.analyses:
        ag_lookup[ag.ma_id] = ag

# For each of the first 100 MAs, compute REML and DL tau2
sa4_records = []
n_classification_change = 0

for ma_id in ma_ids_ordered:
    if ma_id not in ag_lookup:
        continue
    ag = ag_lookup[ma_id]
    try:
        yi, vi, measure = _extract_effects(ag.df, ag.data_type)
        mask = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
        yi_c, vi_c = yi[mask], vi[mask]
        k = len(yi_c)
        if k < 2:
            continue

        reml_tau2, _ = _reml_tau2(yi_c, vi_c)
        dl_tau2_val  = _dl_tau2(yi_c, vi_c)

        # Check if prediction_gap severity changes
        # PI uses tau2 in sqrt(se_hksj^2 + tau2)
        # Severity: CRITICAL if PI includes null on significant MA
        # ci_lower/ci_upper from original run
        orig_rl = AUDIT[ma_id]
        pg_orig = next((r for r in orig_rl if r["module"] == "prediction_gap"), None)

        changed = False
        if pg_orig and not pg_orig["metrics"].get("insufficient_data", False):
            orig_sev = pg_orig["severity"]
            # Recompute PI with DL tau2 instead of REML
            # get se_hksj from original run (we don't store it, approximate from CI)
            ci_lower = pg_orig["metrics"].get("ci_lower", float("nan"))
            ci_upper = pg_orig["metrics"].get("ci_upper", float("nan"))
            # Estimate from pooled result
            w = 1.0 / (vi_c + reml_tau2)
            w_sum = w.sum()
            estimate = (w * yi_c).sum() / w_sum
            q_resid = (w * (yi_c - estimate) ** 2).sum()
            hksj_factor = q_resid / (k - 1) if k > 1 else 1.0
            se_base = 1.0 / np.sqrt(w_sum)
            se_hksj = se_base * np.sqrt(max(1.0, hksj_factor))

            # PI with REML tau2
            df_pi = max(1, k - 2)
            t_crit_pi = stats.t.ppf(0.975, df_pi)
            pi_se_reml = math.sqrt(se_hksj ** 2 + reml_tau2)
            pi_lower_reml = estimate - t_crit_pi * pi_se_reml
            pi_upper_reml = estimate + t_crit_pi * pi_se_reml

            # PI with DL tau2
            pi_se_dl = math.sqrt(se_hksj ** 2 + dl_tau2_val)
            pi_lower_dl = estimate - t_crit_pi * pi_se_dl
            pi_upper_dl = estimate + t_crit_pi * pi_se_dl

            # Classify prediction_gap: CRITICAL if PI crosses null AND MA is significant
            def pg_severity(pi_lower, pi_upper, est):
                if k < 3:
                    return "PASS"
                crosses_null = (pi_lower < 0 < pi_upper) or (pi_lower < 0 and pi_upper < 0 and est > 0)
                # simpler: does PI include zero?
                if pi_lower <= 0 <= pi_upper:
                    return "CRITICAL"
                return "PASS"

            sev_reml = pg_severity(pi_lower_reml, pi_upper_reml, estimate)
            sev_dl   = pg_severity(pi_lower_dl, pi_upper_dl, estimate)
            if sev_reml != sev_dl:
                changed = True

        sa4_records.append({
            "ma_id": ma_id,
            "k": k,
            "reml_tau2": round(float(reml_tau2), 6),
            "dl_tau2": round(float(dl_tau2_val), 6),
            "abs_diff": round(abs(float(reml_tau2) - float(dl_tau2_val)), 6),
            "classification_change": changed,
        })
        if changed:
            n_classification_change += 1

    except Exception as e:
        print(f"  WARNING: {ma_id}: {e}")
        continue

# Summary stats
if sa4_records:
    diffs = [r["abs_diff"] for r in sa4_records]
    reml_vals = [r["reml_tau2"] for r in sa4_records]
    dl_vals   = [r["dl_tau2"]   for r in sa4_records]
    mean_diff = float(np.mean(diffs))
    max_diff  = float(np.max(diffs))
    corr, _ = stats.pearsonr(reml_vals, dl_vals)
    n_valid = len(sa4_records)
    print(f"  Valid MAs: {n_valid}/100")
    print(f"  Mean |REML - DL|: {mean_diff:.5f}")
    print(f"  Max |REML - DL|:  {max_diff:.5f}")
    print(f"  Pearson r(REML, DL): {corr:.4f}")
    print(f"  Classification changes: {n_classification_change}/{n_valid}")
else:
    mean_diff = max_diff = corr = float("nan")
    n_valid = 0
    print("  No valid records computed.")

sa4_summary = {
    "n_valid": n_valid,
    "mean_abs_diff": round(mean_diff, 6),
    "max_abs_diff": round(max_diff, 6),
    "pearson_r": round(float(corr), 4) if not math.isnan(corr) else None,
    "n_classification_change": n_classification_change,
    "records": sa4_records,
}


# ---------------------------------------------------------------------------
# Compile full results
# ---------------------------------------------------------------------------
print("\nCompiling results...")

SA_DATA = {
    "sa1_base":   base_summary,
    "sa1_strict":  strict_summary,
    "sa1_lenient": lenient_summary,
    "sa1_configs": {
        "base":   BASE_CFG,
        "strict":  STRICT_CFG,
        "lenient": LENIENT_CFG,
    },
    "sa2": sa2_summary,
    "sa3": sa3_summary,
    "sa4": sa4_summary,
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(SA_DATA, f, indent=2)
print(f"  Raw data saved: {OUTPUT_JSON}")


# ---------------------------------------------------------------------------
# Format Markdown report
# ---------------------------------------------------------------------------
MODULES = [
    "prediction_gap", "model_misspec", "fragility", "underpowered",
    "pub_bias", "small_study", "excess_sig", "integrity", "overlap",
    "overclaiming",
]

MODULE_LABELS = {
    "prediction_gap": "Prediction gap",
    "model_misspec":  "Model misspec.",
    "fragility":      "Fragility (MAFI)",
    "underpowered":   "Underpowered",
    "pub_bias":       "Publication bias",
    "small_study":    "Small-study effect",
    "excess_sig":     "Excess significance",
    "integrity":      "Data integrity",
    "overlap":        "Study overlap",
    "overclaiming":   "Overclaiming",
}


def fmt(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    return f"{v:.1f}%"


lines = []
lines.append("# MetaAudit — Sensitivity Analysis Results\n")
lines.append(f"N = {N_TOTAL} meta-analyses (501 Cochrane reviews, Pairwise70 dataset)\n")

# ---- SA1 ----
lines.append("## SA1: Threshold Sensitivity (±10% Shifts)\n")
lines.append(
    "Numeric detector thresholds shifted by −10% (strict) and +10% (lenient). "
    "Detectors without continuous thresholds (prediction gap, integrity, overlap) unchanged.\n"
)

lines.append("**Threshold configurations**\n")
lines.append("| Parameter | Strict | Base | Lenient |")
lines.append("|-----------|--------|------|---------|")
thresh_rows = [
    ("I² threshold (%)",        45,       50,       55),
    ("MAFI FAIL threshold",     1,        2,        3),
    ("OIS (total N)",           1440,     1600,     1760),
    ("Pub bias p",              0.09,     0.10,     0.11),
    ("Small-study p",           0.09,     0.10,     0.11),
    ("Small-study Spearman rho",0.36,     0.40,     0.44),
    ("Excess sig O/E ratio",    1.35,     1.50,     1.65),
    ("Excess sig p",            0.09,     0.10,     0.11),
    ("MCID logOR",              f"{LOGIT_1_25*0.90:.3f}", f"{LOGIT_1_25:.3f}", f"{LOGIT_1_25*1.10:.3f}"),
]
for row in thresh_rows:
    lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")

lines.append("")
lines.append("**Overall results under shifted thresholds**\n")
lines.append("| Scenario | N | Any FAIL (%) | Multi-FAIL (%) |")
lines.append("|----------|---|-------------|----------------|")
lines.append(f"| Strict (−10%) | {strict_summary['n']} | {fmt(strict_summary['any_fail_pct'])} | {fmt(strict_summary['multi_fail_pct'])} |")
lines.append(f"| **Base**      | {base_summary['n']}   | **{fmt(base_summary['any_fail_pct'])}** | **{fmt(base_summary['multi_fail_pct'])}** |")
lines.append(f"| Lenient (+10%)| {lenient_summary['n']} | {fmt(lenient_summary['any_fail_pct'])} | {fmt(lenient_summary['multi_fail_pct'])} |")

lines.append("")
lines.append("**Per-module FAIL prevalence under shifted thresholds**\n")
lines.append("| Module | Strict (−10%) | Base | Lenient (+10%) |")
lines.append("|--------|--------------|------|----------------|")
for mod in MODULES:
    label = MODULE_LABELS.get(mod, mod)
    v_s = fmt(strict_summary["module_prev"].get(mod))
    v_b = fmt(base_summary["module_prev"].get(mod))
    v_l = fmt(lenient_summary["module_prev"].get(mod))
    lines.append(f"| {label} | {v_s} | {v_b} | {v_l} |")

lines.append("")

# ---- SA2 ----
lines.append("## SA2: Restrict to k ≥ 5 Studies\n")
lines.append(
    f"Excludes {N_TOTAL - sa2_summary['n']} meta-analyses with k < 5. "
    f"Retained: {sa2_summary['n']} MAs ({100*sa2_summary['n']/N_TOTAL:.1f}% of corpus).\n"
)
lines.append("| Metric | Full corpus | k ≥ 5 only |")
lines.append("|--------|------------|------------|")
lines.append(f"| N | {N_TOTAL} | {sa2_summary['n']} |")
lines.append(f"| Any FAIL (%) | {fmt(base_summary['any_fail_pct'])} | {fmt(sa2_summary['any_fail_pct'])} |")
lines.append(f"| Multi-FAIL (%) | {fmt(base_summary['multi_fail_pct'])} | {fmt(sa2_summary['multi_fail_pct'])} |")

lines.append("")
lines.append("**Per-module prevalence (k ≥ 5 subset)**\n")
lines.append("| Module | Full corpus | k ≥ 5 only | Delta |")
lines.append("|--------|------------|------------|-------|")
for mod in MODULES:
    label = MODULE_LABELS.get(mod, mod)
    v_f = base_summary["module_prev"].get(mod, float("nan"))
    v_k = sa2_summary["module_prev"].get(mod, float("nan"))
    if math.isnan(v_f) or math.isnan(v_k):
        delta = "N/A"
    else:
        d = v_k - v_f
        delta = f"{d:+.1f}pp"
    lines.append(f"| {label} | {fmt(v_f)} | {fmt(v_k)} | {delta} |")

lines.append("")

# ---- SA3 ----
lines.append("## SA3: Binary Outcomes Only\n")
lines.append(
    f"Restricts to binary (event-rate) outcomes only. "
    f"Excluded {N_TOTAL - sa3_summary['n']} continuous/GIV MAs. "
    f"Retained: {sa3_summary['n']} ({100*sa3_summary['n']/N_TOTAL:.1f}%).\n"
)
lines.append("| Metric | Full corpus | Binary only |")
lines.append("|--------|------------|-------------|")
lines.append(f"| N | {N_TOTAL} | {sa3_summary['n']} |")
lines.append(f"| Any FAIL (%) | {fmt(base_summary['any_fail_pct'])} | {fmt(sa3_summary['any_fail_pct'])} |")
lines.append(f"| Multi-FAIL (%) | {fmt(base_summary['multi_fail_pct'])} | {fmt(sa3_summary['multi_fail_pct'])} |")

lines.append("")
lines.append("**Per-module prevalence (binary MAs)**\n")
lines.append("| Module | Full corpus | Binary only | Delta |")
lines.append("|--------|------------|-------------|-------|")
for mod in MODULES:
    label = MODULE_LABELS.get(mod, mod)
    v_f = base_summary["module_prev"].get(mod, float("nan"))
    v_b = sa3_summary["module_prev"].get(mod, float("nan"))
    if math.isnan(v_f) or math.isnan(v_b):
        delta = "N/A"
    else:
        d = v_b - v_f
        delta = f"{d:+.1f}pp"
    lines.append(f"| {label} | {fmt(v_f)} | {fmt(v_b)} | {delta} |")

lines.append("")

# ---- SA4 ----
lines.append("## SA4: REML vs DerSimonian-Laird tau² Estimator\n")
lines.append(
    f"First {sa4_summary['n_valid']} eligible MAs (k ≥ 2) from the corpus "
    "were recomputed with both REML and DL tau² estimators. "
    "Classification change = prediction-gap severity differs between estimators.\n"
)
lines.append("| Statistic | Value |")
lines.append("|-----------|-------|")
lines.append(f"| MAs analysed | {sa4_summary['n_valid']} |")
lines.append(f"| Mean |REML − DL| | {sa4_summary['mean_abs_diff']:.5f} |")
lines.append(f"| Max |REML − DL|  | {sa4_summary['max_abs_diff']:.5f} |")
lines.append(f"| Pearson r (REML, DL) | {sa4_summary['pearson_r']} |")
lines.append(f"| MAs with classification change | {sa4_summary['n_classification_change']}/{sa4_summary['n_valid']} |")

lines.append("")
lines.append("*Note:* tau² affects the prediction interval width, which determines prediction-gap severity. "
             "I² and other thresholds are independent of the tau² estimator.\n")

md_text = "\n".join(lines) + "\n"

with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(md_text)
print(f"  Markdown report saved: {OUTPUT_MD}")

# ---------------------------------------------------------------------------
# Print summary to console
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("SENSITIVITY ANALYSIS SUMMARY")
print("=" * 70)

print("\nSA1 — Overall results:")
print(f"  Strict  (-10%): any_fail={fmt(strict_summary['any_fail_pct'])}  multi_fail={fmt(strict_summary['multi_fail_pct'])}")
print(f"  Base:           any_fail={fmt(base_summary['any_fail_pct'])}  multi_fail={fmt(base_summary['multi_fail_pct'])}")
print(f"  Lenient (+10%): any_fail={fmt(lenient_summary['any_fail_pct'])}  multi_fail={fmt(lenient_summary['multi_fail_pct'])}")

print(f"\nSA2 — k>=5 only (n={sa2_summary['n']}): any_fail={fmt(sa2_summary['any_fail_pct'])}  multi_fail={fmt(sa2_summary['multi_fail_pct'])}")
print(f"SA3 — Binary only (n={sa3_summary['n']}): any_fail={fmt(sa3_summary['any_fail_pct'])}  multi_fail={fmt(sa3_summary['multi_fail_pct'])}")

print(f"\nSA4 — tau2 estimator comparison (n={sa4_summary['n_valid']}):")
print(f"  Mean |REML - DL| = {sa4_summary['mean_abs_diff']:.5f}")
print(f"  Max  |REML - DL| = {sa4_summary['max_abs_diff']:.5f}")
print(f"  Pearson r       = {sa4_summary['pearson_r']}")
print(f"  Classification changes = {sa4_summary['n_classification_change']}/{sa4_summary['n_valid']}")

print("\nDone.")
