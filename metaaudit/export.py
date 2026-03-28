"""Export audit results to JSON and CSV."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from metaaudit.severity import DetectorResult


class _SafeEncoder(json.JSONEncoder):
    """Encode numpy scalars and non-finite floats safely."""

    def default(self, obj):  # noqa: ANN001
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            v = float(obj)
            return None if not math.isfinite(v) else v
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

    def iterencode(self, o, _one_shot=False):  # noqa: ANN001
        # Also sanitise plain Python floats that are NaN/Inf
        def _sanitise(obj):  # noqa: ANN001
            if isinstance(obj, float) and not math.isfinite(obj):
                return None
            if isinstance(obj, dict):
                return {k: _sanitise(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitise(v) for v in obj]
            return obj

        return super().iterencode(_sanitise(o), _one_shot)


def export_json(
    results: dict[str, list[DetectorResult]],
    path: str | Path,
) -> None:
    data = {}
    for ma_id, detections in results.items():
        data[ma_id] = [d.to_dict() for d in detections]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=_SafeEncoder)


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
