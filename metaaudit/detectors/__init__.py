"""Flaw detection modules for MetaAudit."""

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

ALL_DETECTORS = [
    "prediction_gap",
    "model_misspec",
    "fragility",
    "underpowered",
    "pub_bias",
    "small_study",
    "excess_sig",
    "integrity",
    "overlap",
    "overclaiming",
    "certainty_mismatch",
]

__all__ = [
    "detect_prediction_gap",
    "detect_model_misspec",
    "detect_fragility",
    "detect_underpowered",
    "detect_pub_bias",
    "detect_small_study",
    "detect_excess_sig",
    "detect_integrity",
    "detect_overlap",
    "build_overlap_index",
    "detect_overclaiming",
    "detect_certainty_mismatch",
    "ALL_DETECTORS",
]
