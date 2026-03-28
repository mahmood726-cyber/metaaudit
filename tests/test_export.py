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
