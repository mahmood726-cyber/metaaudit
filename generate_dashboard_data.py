"""Generate compact summary data for the HTML dashboard."""
import json
import csv
import os
import math
from collections import Counter, defaultdict

RESULTS_DIR = r"C:\MetaAudit\results"

print("Loading audit_results.json...")
with open(os.path.join(RESULTS_DIR, "audit_results.json")) as f:
    results = json.load(f)
print(f"  Loaded {len(results)} meta-analyses")

# 1. Headline numbers
fail_counts = {}
for ma_id, detections in results.items():
    n_fail = sum(1 for d in detections if d["severity"] in ("FAIL", "CRITICAL"))
    fail_counts[ma_id] = n_fail

total_mas = len(results)
any_fail = sum(1 for c in fail_counts.values() if c > 0)
multi_fail = sum(1 for c in fail_counts.values() if c >= 3)

# 2. Per-module severity breakdown
module_breakdown = defaultdict(lambda: {"PASS": 0, "WARN": 0, "FAIL": 0, "CRITICAL": 0, "INSUFF": 0})
all_severities = {"PASS": 0, "WARN": 0, "FAIL": 0, "CRITICAL": 0, "INSUFF": 0}
for ma_id, detections in results.items():
    for d in detections:
        mod = d["module"]
        sev = d["severity"]
        if d["metrics"].get("insufficient_data"):
            module_breakdown[mod]["INSUFF"] += 1
            all_severities["INSUFF"] += 1
        else:
            module_breakdown[mod][sev] += 1
            all_severities[sev] += 1

# 3. Review-level summary
review_summary = defaultdict(lambda: {"mas": 0, "fails": 0, "warns": 0, "modules_fail": set()})
for ma_id, detections in results.items():
    review_id = ma_id.rsplit("__", 1)[0]
    review_summary[review_id]["mas"] += 1
    for d in detections:
        if d["severity"] in ("FAIL", "CRITICAL"):
            review_summary[review_id]["fails"] += 1
            review_summary[review_id]["modules_fail"].add(d["module"])
        elif d["severity"] == "WARN":
            review_summary[review_id]["warns"] += 1

review_list = []
for rid, s in sorted(review_summary.items()):
    review_list.append({
        "id": rid,
        "mas": s["mas"],
        "fails": s["fails"],
        "warns": s["warns"],
        "fail_modules": sorted(s["modules_fail"]),
        "severity_score": s["fails"] * 2 + s["warns"],
    })

# 4. Fail distribution histogram
fail_dist = Counter(fail_counts.values())

# 5. Load prevalence and cooccurrence
with open(os.path.join(RESULTS_DIR, "prevalence.json")) as f:
    prevalence_raw = json.load(f)

# Handle NaN from Python's json (it's not valid JSON but Python wrote it)
prevalence = {}
for k, v in prevalence_raw.items():
    if v != v:  # NaN check
        prevalence[k] = None
    else:
        prevalence[k] = round(v * 100, 1)

cooc_modules = []
cooc_matrix = {}
with open(os.path.join(RESULTS_DIR, "cooccurrence.csv")) as f:
    reader = csv.reader(f)
    header = next(reader)
    cooc_modules = header[1:]
    for row in reader:
        if not row or not row[0]:
            continue
        mod = row[0]
        vals = []
        for v in row[1:]:
            try:
                fv = float(v)
                vals.append(round(fv, 4) if math.isfinite(fv) else None)
            except (ValueError, IndexError):
                vals.append(None)
        cooc_matrix[mod] = vals

# 6. Sample of worst MAs for explorer (top 200 by fail count to keep size small)
# Actually include all reviews since there are only ~500
print(f"  Reviews: {len(review_list)}")

# 7. Module display names
module_labels = {
    "prediction_gap": "Prediction Gap",
    "model_misspec": "Model Misspecification",
    "fragility": "Fragility",
    "underpowered": "Underpowered",
    "pub_bias": "Publication Bias",
    "small_study": "Small-Study Effects",
    "excess_sig": "Excess Significance",
    "integrity": "Integrity",
    "overlap": "Overlap",
    "overclaiming": "Overclaiming",
    "certainty_mismatch": "Certainty Mismatch",
}

# Build dashboard data
dashboard = {
    "headline": {
        "total_reviews": len(review_summary),
        "total_mas": total_mas,
        "any_fail": any_fail,
        "any_fail_pct": round(100 * any_fail / total_mas, 1),
        "multi_fail": multi_fail,
        "multi_fail_pct": round(100 * multi_fail / total_mas, 1),
    },
    "all_severities": all_severities,
    "module_breakdown": {k: dict(v) for k, v in module_breakdown.items()},
    "module_labels": module_labels,
    "prevalence": prevalence,
    "cooccurrence": {"modules": cooc_modules, "matrix": cooc_matrix},
    "fail_distribution": {str(k): v for k, v in sorted(fail_dist.items())},
    "reviews": review_list,
}

out_path = os.path.join(RESULTS_DIR, "dashboard_data.json")
with open(out_path, "w") as f:
    json.dump(dashboard, f, separators=(',', ':'))
size_kb = os.path.getsize(out_path) / 1024
print(f"Dashboard data written to {out_path}")
print(f"Size: {size_kb:.0f} KB")
print(f"\nHeadline stats:")
print(f"  Total MAs:    {total_mas:,}")
print(f"  Any fail:     {any_fail:,} ({100*any_fail/total_mas:.1f}%)")
print(f"  Multi-fail:   {multi_fail:,} ({100*multi_fail/total_mas:.1f}%)")
print(f"  Reviews:      {len(review_summary):,}")
print(f"\nSeverity totals: {dict(all_severities)}")
print(f"\nTop 5 reviews by severity:")
for r in sorted(review_list, key=lambda x: -x['severity_score'])[:5]:
    print(f"  {r['id']}: {r['fails']} fails, {r['warns']} warns, score={r['severity_score']}")
