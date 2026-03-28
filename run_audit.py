"""MetaAudit CLI — run the full audit pipeline on Pairwise70 data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

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
import pandas as pd

DEFAULT_DATA_DIR = r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data"
DEFAULT_OUTPUT_DIR = r"C:\MetaAudit\results"


def run_detectors_on_analysis(ag, ma, study_data, overlap_result):
    """Run all detectors for one analysis group.

    overlap_result: pre-computed DetectorResult for this review's overlap check.
    """
    results = []
    results.append(detect_prediction_gap(ma))
    context = {}
    if ag.data_type == DataType.BINARY:
        total_events = (ag.df["Experimental.cases"].sum() + ag.df["Control.cases"].sum())
        total_n = (ag.df["Experimental.N"].sum() + ag.df["Control.N"].sum())
        context["event_rate"] = total_events / total_n if total_n > 0 else 0
    results.append(detect_model_misspec(ma, context))
    results.append(detect_fragility(ma, study_data))
    if ag.data_type == DataType.BINARY:
        total_n = int(ag.df["Experimental.N"].sum() + ag.df["Control.N"].sum())
    elif ag.data_type == DataType.CONTINUOUS:
        total_n = int(ag.df["Experimental.N"].sum() + ag.df["Control.N"].sum())
    else:
        total_n = 0
    results.append(detect_underpowered(ma, total_n))
    results.append(detect_pub_bias(ma))
    results.append(detect_small_study(ma))
    results.append(detect_excess_sig(ma))
    results.append(detect_integrity(ag.df, ag.data_type))
    results.append(overlap_result)
    results.append(detect_overclaiming(ma))
    results.append(detect_certainty_mismatch(
        grade_certainty=None,
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

    print("Building study overlap index...")
    studies_by_review = {}
    for r in reviews:
        study_names = set(r.study_names) if r.study_names else set()
        if not study_names and "Study" in r.df.columns:
            study_names = set(r.df["Study"].dropna().unique())
        studies_by_review[r.review_id] = study_names
    overlap_index = build_overlap_index(studies_by_review)
    print(f"Found {len(overlap_index)} review pairs with shared studies")

    # Pre-compute overlap result once per review (not once per MA)
    overlap_cache: dict[str, DetectorResult] = {}
    for r in reviews:
        study_names = studies_by_review[r.review_id]
        overlap_cache[r.review_id] = detect_overlap(r.review_id, study_names, overlap_index)

    all_results: dict[str, list[DetectorResult]] = {}
    total_analyses = sum(len(r.analyses) for r in reviews)
    print(f"Running 11 detectors on {total_analyses} meta-analyses...")

    done = 0
    for review in reviews:
        for ag in review.analyses:
            ma = recompute_ma(ag.df, ag.data_type)
            study_data = ag.df if ag.data_type == DataType.BINARY else None
            results = run_detectors_on_analysis(
                ag, ma, study_data, overlap_cache[ag.review_id]
            )
            all_results[ag.ma_id] = results
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{total_analyses} analyses processed...")

    print(f"All {done} analyses complete.")

    print("Computing correlations...")
    matrix = build_flaw_matrix(all_results)
    prevalence = compute_prevalence(matrix)
    cooccurrence = compute_cooccurrence(matrix)
    severity_scores = compute_severity_scores(all_results)

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
    for module, prev in sorted(prevalence.items(), key=lambda x: -(x[1] if not np.isnan(x[1]) else -1)):
        if not np.isnan(prev):
            print(f"  {module:25s} {100*prev:.1f}%")
        else:
            print(f"  {module:25s} N/A")
    print(f"{'='*60}")

    json_path = os.path.join(args.output_dir, "audit_results.json")
    csv_path = os.path.join(args.output_dir, "audit_results.csv")
    export_json(all_results, json_path)
    export_csv(all_results, csv_path)

    prevalence_path = os.path.join(args.output_dir, "prevalence.json")
    with open(prevalence_path, "w") as f:
        # Replace NaN with None so output is valid JSON
        clean_prev = {k: (v if v == v else None) for k, v in prevalence.items()}
        json.dump(clean_prev, f, indent=2)

    cooccurrence.to_csv(os.path.join(args.output_dir, "cooccurrence.csv"))

    print(f"\nResults saved to {args.output_dir}/")
    print("Done.")


if __name__ == "__main__":
    main()
