from metaaudit.severity import Severity, DetectorResult


def test_severity_ordering():
    assert Severity.PASS < Severity.WARN < Severity.FAIL < Severity.CRITICAL


def test_severity_from_string():
    assert Severity.from_string("PASS") == Severity.PASS
    assert Severity.from_string("fail") == Severity.FAIL


def test_detector_result_creation():
    r = DetectorResult(
        module="prediction_gap",
        severity=Severity.FAIL,
        detail="CI excludes null but PI includes it",
        metrics={"pi_lower": -0.3, "pi_upper": 1.2},
    )
    assert r.module == "prediction_gap"
    assert r.severity == Severity.FAIL
    assert r.metrics["pi_lower"] == -0.3


def test_detector_result_insufficient_data():
    r = DetectorResult.insufficient_data("pub_bias", reason="k < 10")
    assert r.severity == Severity.PASS
    assert r.detail == "Insufficient data: k < 10"
    assert r.metrics["insufficient_data"] is True


def test_detector_result_to_dict():
    r = DetectorResult(
        module="fragility",
        severity=Severity.WARN,
        detail="MAFI = 4",
        metrics={"mafi": 4},
    )
    d = r.to_dict()
    assert d["module"] == "fragility"
    assert d["severity"] == "WARN"
    assert d["detail"] == "MAFI = 4"
    assert d["metrics"]["mafi"] == 4
