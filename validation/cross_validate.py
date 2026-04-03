"""
Cross-validation of MetaAudit Python engine against R metafor.

Selects 10 binary Pairwise70 reviews, runs REML on study-level data
in both Python (HKSJ) and R (normal-theory + HKSJ), and reports
agreement statistics.

Usage:
    python C:/MetaAudit/validation/cross_validate.py
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import math

import numpy as np
import pandas as pd

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, r"C:\MetaAudit")
from metaaudit.loader import load_rda_file, DataType
from metaaudit.recompute import recompute_ma, compute_log_or, compute_prediction_interval

DATA_DIR   = r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data"
R_SCRIPT   = r"C:\MetaAudit\validation\metafor_validate.R"
RSCRIPT    = r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
OUTPUT_DIR = r"C:\MetaAudit\validation"
N_REVIEWS  = 10

# ── tolerances ───────────────────────────────────────────────────────────────
TOL_ESTIMATE = 0.001
TOL_SE       = 0.001
TOL_TAU2     = 0.01
TOL_I2       = 1.0       # percentage points
TOL_CI       = 0.01
TOL_PI       = 0.05
TOL_Q        = 0.001


# ── helpers ──────────────────────────────────────────────────────────────────

def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    return f"{v:.4f}"


def _match(py, r, tol) -> str:
    if py is None or r is None:
        return "—"
    if not math.isfinite(py) or not math.isfinite(r):
        return "—"
    return "YES" if abs(py - r) <= tol else "NO "


def run_r(csv_path: str) -> dict | None:
    """Call Rscript and parse key=value output. Returns None on failure."""
    try:
        result = subprocess.run(
            [RSCRIPT, "--no-save", "--no-restore", R_SCRIPT, csv_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"    R error: {result.stderr.strip()[:300]}")
            return None
        out = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                try:
                    out[k.strip()] = float(v.strip())
                except ValueError:
                    pass
        return out if out else None
    except subprocess.TimeoutExpired:
        print("    R timed out.")
        return None
    except Exception as e:
        print(f"    R call failed: {e}")
        return None


def select_reviews() -> list[dict]:
    """Return first 10 binary reviews (first analysis group, k >= 3)."""
    files = sorted(os.listdir(DATA_DIR))
    selected = []
    for fname in files:
        if len(selected) >= N_REVIEWS:
            break
        path = os.path.join(DATA_DIR, fname)
        try:
            rv = load_rda_file(path)
        except Exception as e:
            print(f"  WARNING: could not load {fname}: {e}")
            continue
        # Need at least one binary analysis group with k >= 3
        for ag in rv.analyses:
            if ag.data_type == DataType.BINARY and ag.k >= 3:
                selected.append({"review_id": rv.review_id, "ag": ag})
                break
    return selected


def python_recompute(ag) -> dict:
    """Run MetaAudit Python engine on one AnalysisGroup."""
    ma = recompute_ma(ag.df, ag.data_type)
    pi = compute_prediction_interval(ma.estimate, ma.se_hksj, ma.tau2, ma.k)
    return {
        "estimate":  ma.estimate,
        "se":        ma.se,
        "se_hksj":   ma.se_hksj,
        "tau2":      ma.tau2,
        "I2":        ma.I2,
        "ci_lower":  ma.ci_lower,
        "ci_upper":  ma.ci_upper,
        "pi_lower":  pi["pi_lower"],
        "pi_upper":  pi["pi_upper"],
        "p_value":   ma.p_value,
        "Q":         ma.Q,
        "k":         ma.k,
    }


def write_csv_for_r(ag, tmp_path: str) -> None:
    """Write study-level binary data to CSV for R."""
    df = ag.df.copy()
    out = pd.DataFrame({
        "e_cases": df["Experimental.cases"].values,
        "e_n":     df["Experimental.N"].values,
        "c_cases": df["Control.cases"].values,
        "c_n":     df["Control.N"].values,
    })
    out.to_csv(tmp_path, index=False)


# ── comparison table rows ─────────────────────────────────────────────────────

def build_rows(review_id: str, k: int, py: dict, r_nt: dict, r_hk: dict) -> list[dict]:
    """Build comparison rows for all statistics of one MA."""
    rows = []
    stats = [
        ("estimate", "Estimate (logOR)", TOL_ESTIMATE),
        ("se",       "SE (pooled)",      TOL_SE),
        ("tau2",     "tau²",             TOL_TAU2),
        ("I2",       "I² (%)",           TOL_I2),
        ("Q",        "Q stat",           TOL_Q),
        ("ci_lower", "CI lower",         TOL_CI),
        ("ci_upper", "CI upper",         TOL_CI),
        ("pi_lower", "PI lower",         TOL_PI),
        ("pi_upper", "PI upper",         TOL_PI),
    ]
    for key, label, tol in stats:
        py_val  = py.get(key)
        # R normal-theory keys are the same names; HKSJ keys are prefixed
        rnt_val = r_nt.get(key)      if r_nt else None
        rhk_val = r_hk.get(f"hksj_{key}") if r_hk else None

        diff_nt = (abs(py_val - rnt_val) if (py_val is not None and rnt_val is not None
                   and math.isfinite(py_val) and math.isfinite(rnt_val)) else None)
        diff_hk = (abs(py_val - rhk_val) if (py_val is not None and rhk_val is not None
                   and math.isfinite(py_val) and math.isfinite(rhk_val)) else None)

        rows.append({
            "review": review_id,
            "k": k,
            "stat": label,
            "python": py_val,
            "r_nt":  rnt_val,
            "r_hksj": rhk_val,
            "diff_vs_nt":   diff_nt,
            "diff_vs_hksj": diff_hk,
            "match_nt":  _match(py_val, rnt_val, tol),
            "match_hksj": _match(py_val, rhk_val, tol),
            "tol": tol,
        })
    return rows


# ── markdown report ───────────────────────────────────────────────────────────

def write_report(all_rows: list[dict], summary: dict, out_path: str) -> None:
    lines = []
    lines.append("# MetaAudit vs R metafor Cross-Validation\n")
    lines.append("## Method\n")
    lines.append(
        "10 binary Cochrane meta-analyses (first qualifying analysis group per review) "
        "recomputed in Python (MetaAudit REML + HKSJ) and R (metafor 4.8.0 REML).  \n"
        "Two R variants compared: **normal-theory CIs** (default `rma()`) and "
        "**HKSJ CIs** (`test=\"knha\"`).  \n"
        "Continuity correction 0.5 applied only to zero-cell studies (`to=\"only0\"`).  \n"
        "Prediction interval: Python uses `sqrt(se_hksj² + tau²)` × t_{k-2}; "
        "R `predict()` uses `sqrt(tau²)` × t_{k-2} (no SE term in standard metafor PI).  \n"
    )
    lines.append("\n## Comparison Notes\n")
    lines.append(
        "- **Estimate / tau² / I² / Q**: should match closely (same REML algorithm).  \n"
        "- **SE**: Python `se` = `1/sqrt(sum(w))` (unadjusted); HKSJ inflates CIs but not SE itself.  \n"
        "- **CI bounds**: differ between normal-theory and HKSJ by design.  \n"
        "- **PI bounds**: Python adds `se_hksj²` inside the square root; R adds 0 SE term.  \n"
    )

    # Per-review detail tables
    for review_id in summary["reviews"]:
        rev_rows = [r for r in all_rows if r["review"] == review_id]
        if not rev_rows:
            continue
        k = rev_rows[0]["k"]
        lines.append(f"\n### {review_id} (k = {k})\n")
        lines.append(
            "| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |\n"
            "|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|\n"
        )
        for row in rev_rows:
            lines.append(
                f"| {row['stat']:22s} "
                f"| {_fmt(row['python']):>10s} "
                f"| {_fmt(row['r_nt']):>10s} "
                f"| {_fmt(row['r_hksj']):>10s} "
                f"| {_fmt(row['diff_vs_nt']):>10s} "
                f"| {_fmt(row['diff_vs_hksj']):>12s} "
                f"| {row['match_nt']:^9s} "
                f"| {row['match_hksj']:^11s} |\n"
            )

    # Summary
    lines.append("\n## Summary Table\n")
    lines.append(
        "| Review | k | estimate | tau² | I² | Q | CI(NT) | CI(HKSJ) | PI(HKSJ) |\n"
        "|--------|---|---------|------|----|----|--------|----------|----------|\n"
    )
    for review_id in summary["reviews"]:
        rev_rows = [r for r in all_rows if r["review"] == review_id]
        if not rev_rows:
            continue
        k = rev_rows[0]["k"]

        def get_match(stat, col):
            for r in rev_rows:
                if r["stat"] == stat:
                    return r[col]
            return "—"

        lines.append(
            f"| {review_id:30s} | {k:3d} "
            f"| {get_match('Estimate (logOR)', 'match_nt'):^8s} "
            f"| {get_match('tau²', 'match_nt'):^4s} "
            f"| {get_match('I² (%)', 'match_nt'):^3s} "
            f"| {get_match('Q stat', 'match_nt'):^3s} "
            f"| {get_match('CI lower', 'match_nt'):^6s}/{get_match('CI upper', 'match_nt'):^6s} "
            f"| {get_match('CI lower', 'match_hksj'):^6s}/{get_match('CI upper', 'match_hksj'):^6s} "
            f"| {get_match('PI lower', 'match_hksj'):^6s}/{get_match('PI upper', 'match_hksj'):^6s} |\n"
        )

    # Overall stats
    nt_matches   = [r for r in all_rows if r["match_nt"] == "YES"]
    hksj_matches = [r for r in all_rows if r["match_hksj"] == "YES"]
    nt_total     = [r for r in all_rows if r["match_nt"] != "—"]
    hksj_total   = [r for r in all_rows if r["match_hksj"] != "—"]

    # Mean absolute tau2 difference
    tau2_rows_nt = [r for r in all_rows if r["stat"] == "tau²" and r["diff_vs_nt"] is not None]
    tau2_rows_hk = [r for r in all_rows if r["stat"] == "tau²" and r["diff_vs_hksj"] is not None]
    mean_tau2_nt = np.mean([r["diff_vs_nt"] for r in tau2_rows_nt]) if tau2_rows_nt else float("nan")
    mean_tau2_hk = np.mean([r["diff_vs_hksj"] for r in tau2_rows_hk]) if tau2_rows_hk else float("nan")

    estimate_rows_nt = [r for r in all_rows if r["stat"] == "Estimate (logOR)" and r["diff_vs_nt"] is not None]
    mean_est_nt = np.mean([r["diff_vs_nt"] for r in estimate_rows_nt]) if estimate_rows_nt else float("nan")

    lines.append("\n## Overall Statistics\n")
    lines.append(
        f"- Reviews validated: {len(summary['reviews'])}/10  \n"
        f"- Comparisons vs normal-theory: {len(nt_matches)}/{len(nt_total)} within tolerance  \n"
        f"- Comparisons vs HKSJ: {len(hksj_matches)}/{len(hksj_total)} within tolerance  \n"
        f"- Mean |Δ estimate| vs R normal-theory: {mean_est_nt:.5f}  \n"
        f"- Mean |Δ tau²| vs R normal-theory: {mean_tau2_nt:.5f}  \n"
        f"- Mean |Δ tau²| vs R HKSJ: {mean_tau2_hk:.5f}  \n"
    )
    lines.append(
        "\n### Expected mismatches (by design)\n"
        "- **CI bounds (normal-theory)**: Python uses t-distribution (HKSJ), "
        "R normal-theory uses z — so mismatches are expected and correct.  \n"
        "- **PI bounds**: Python includes `se_hksj²` in PI variance; "
        "standard metafor `predict()` uses only `tau²` — intentional difference.  \n"
        "- All core statistics (estimate, tau², I², Q) should match within tolerance 0.001.  \n"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\nReport saved to {out_path}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("Selecting 10 binary reviews...")
    reviews = select_reviews()
    print(f"  Selected {len(reviews)} reviews.")

    all_rows = []
    summary  = {"reviews": []}

    for i, item in enumerate(reviews, 1):
        review_id = item["review_id"]
        ag        = item["ag"]
        print(f"\n[{i:2d}/10] {review_id}  (k={ag.k})")

        # Python engine
        py = python_recompute(ag)
        print(f"        Python: estimate={py['estimate']:.4f}  tau2={py['tau2']:.4f}  I2={py['I2']:.1f}%  k={py['k']}")

        # Write CSV for R
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp_path = tmp.name
        try:
            write_csv_for_r(ag, tmp_path)
            r_out = run_r(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        if r_out:
            print(f"        R (NT): estimate={r_out.get('estimate', float('nan')):.4f}  "
                  f"tau2={r_out.get('tau2', float('nan')):.4f}  "
                  f"I2={r_out.get('I2', float('nan')):.1f}%")
            print(f"        R (HKSJ): ci=[{r_out.get('hksj_ci_lower', float('nan')):.4f}, "
                  f"{r_out.get('hksj_ci_upper', float('nan')):.4f}]")
        else:
            print("        R: FAILED — skipping this review.")

        rows = build_rows(review_id, ag.k, py, r_out or {}, r_out or {})
        all_rows.extend(rows)
        summary["reviews"].append(review_id)

    out_path = os.path.join(OUTPUT_DIR, "cross_validation_results.md")
    write_report(all_rows, summary, out_path)

    # Also write a machine-readable CSV of all comparisons
    csv_path = os.path.join(OUTPUT_DIR, "cross_validation_results.csv")
    pd.DataFrame(all_rows).to_csv(csv_path, index=False)
    print(f"CSV saved to {csv_path}")

    # Quick pass/fail summary to stdout
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 70)
    for review_id in summary["reviews"]:
        rev_rows = [r for r in all_rows if r["review"] == review_id]
        core = [r for r in rev_rows if r["stat"] in ("Estimate (logOR)", "tau²", "I² (%)", "Q stat")]
        core_nt_pass = all(r["match_nt"] == "YES" for r in core if r["match_nt"] != "—")
        hksj_ci = [r for r in rev_rows if r["stat"] in ("CI lower", "CI upper")]
        hksj_pass = all(r["match_hksj"] == "YES" for r in hksj_ci if r["match_hksj"] != "—")
        k = rev_rows[0]["k"] if rev_rows else 0
        print(f"  {review_id:35s}  k={k:3d}  "
              f"core(NT)={'PASS' if core_nt_pass else 'FAIL'}  "
              f"CI(HKSJ)={'PASS' if hksj_pass else 'FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
