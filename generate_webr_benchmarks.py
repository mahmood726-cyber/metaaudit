"""Generate Python benchmark values for the WebR verification dashboard."""
import json
import sys
import io
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from metaaudit.recompute import compute_log_or, compute_md, pool_effects_reml, compute_prediction_interval

datasets = [
    {
        "name": "Binary, low heterogeneity (k=5)",
        "type": "binary",
        "ei": [10, 15, 8, 20, 12],
        "ni": [100, 120, 80, 150, 110],
        "ci": [20, 25, 15, 30, 22],
        "cn": [100, 120, 80, 150, 110],
    },
    {
        "name": "Binary, high heterogeneity (k=6)",
        "type": "binary",
        "ei": [5, 3, 15, 40, 8, 1],
        "ni": [100, 80, 120, 50, 200, 60],
        "ci": [30, 2, 25, 5, 20, 10],
        "cn": [100, 80, 120, 50, 200, 60],
    },
    {
        "name": "Binary, zero cells (k=4)",
        "type": "binary",
        "ei": [0, 1, 0, 2],
        "ni": [100, 80, 120, 90],
        "ci": [5, 8, 3, 7],
        "cn": [100, 80, 120, 90],
    },
    {
        "name": "Continuous MD (k=5)",
        "type": "continuous",
        "em": [120, 118, 122, 119, 121],
        "es": [15, 12, 18, 14, 16],
        "en": [50, 60, 40, 70, 55],
        "cm": [130, 128, 131, 129, 127],
        "cs": [16, 13, 17, 15, 14],
        "cn": [50, 60, 40, 70, 55],
    },
    {
        "name": "Binary, large k (k=8)",
        "type": "binary",
        "ei": [12, 8, 20, 5, 15, 10, 7, 18],
        "ni": [100, 90, 150, 70, 110, 130, 85, 140],
        "ci": [18, 15, 28, 12, 22, 20, 14, 25],
        "cn": [100, 90, 150, 70, 110, 130, 85, 140],
    },
]

results = []
for d in datasets:
    if d["type"] == "binary":
        yi, vi = compute_log_or(
            np.array(d["ei"], dtype=float),
            np.array(d["ni"], dtype=float),
            np.array(d["ci"], dtype=float),
            np.array(d["cn"], dtype=float),
        )
    else:
        yi, vi = compute_md(
            np.array(d["em"], dtype=float),
            np.array(d["es"], dtype=float),
            np.array(d["en"], dtype=float),
            np.array(d["cm"], dtype=float),
            np.array(d["cs"], dtype=float),
            np.array(d["cn"], dtype=float),
        )

    pooled = pool_effects_reml(yi, vi)
    pi = compute_prediction_interval(
        pooled["estimate"], pooled["se"], pooled["tau2"], pooled["k"]
    )

    results.append({
        "name": d["name"],
        "type": d["type"],
        "estimate": round(pooled["estimate"], 6),
        "se": round(pooled["se"], 6),
        "se_hksj": round(pooled["se_hksj"], 6),
        "tau2": round(pooled["tau2"], 6),
        "I2": round(pooled["I2"], 2),
        "ci_lower": round(pooled["ci_lower"], 6),
        "ci_upper": round(pooled["ci_upper"], 6),
        "pi_lower": round(pi["pi_lower"], 6) if pi["computable"] else None,
        "pi_upper": round(pi["pi_upper"], 6) if pi["computable"] else None,
        "pi_computable": pi["computable"],
    })

print(json.dumps(results, indent=2))
