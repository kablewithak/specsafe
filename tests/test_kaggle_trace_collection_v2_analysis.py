from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from specsafe.kaggle_trace_analysis.expanded_archive_analysis import (
    build_trace_analysis_report,
)

ATTEMPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
REPORT_PATH = ATTEMPT_DIR / "trace_analysis_report.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_trace_analysis_report_is_deterministic() -> None:
    retained = _load_json(REPORT_PATH)
    regenerated = build_trace_analysis_report(ATTEMPT_DIR)

    assert regenerated == retained


def test_trace_analysis_preserves_retained_archive_boundary() -> None:
    report = _load_json(REPORT_PATH)

    assert report["report_id"] == "v5_qwen_trace_collection_v2_attempt_001_analysis"
    assert report["analysis_status"] == "diagnostic_analysis_only"
    assert report["collection_id"] == "v5-qwen-governed-trace-collection-v2"
    assert report["attempt_id"] == "attempt-001-t4"
    assert report["evidence_class"] == "kaggle_environment_measured"
    assert report["source_archive_boundary"]["raw_prompt_text_retained"] is False
    assert report["source_archive_boundary"]["secrets_printed"] is False


def test_trace_analysis_counts_match_collection_output() -> None:
    report = _load_json(REPORT_PATH)

    assert report["record_counts"] == {
        "case_count": 30,
        "expected_outcome_record_count": 120,
        "runtime_record_count": 120,
        "timing_record_count": 120,
    }
    assert report["signal_diagnostics"]["target_argmax_match_count"] == 97
    assert report["signal_diagnostics"]["target_argmax_nonmatch_count"] == 23
    assert report["signal_diagnostics"]["target_argmax_match_rate"] == pytest.approx(
        0.8083333333333333
    )


def test_runtime_outcome_join_and_label_boundary_are_clean() -> None:
    report = _load_json(REPORT_PATH)
    join_status = report["runtime_outcome_join_status"]

    assert join_status["one_to_one_join_passed"] is True
    assert join_status["joined_record_count"] == 120
    assert join_status["runtime_forbidden_fields_present"] == []


def test_hashes_match_retention_manifest_inputs() -> None:
    report = _load_json(REPORT_PATH)

    assert set(report["manifest_hash_status"].values()) == {True}
    assert report["input_file_hashes"]["runtime_records.jsonl"] == (
        "d82229e07cc32da8b6e73b26190b92b8b802326b2eb816b509ed55967e49f804"
    )
    assert report["input_file_hashes"]["expected_outcome_records.jsonl"] == (
        "79e436dcc415597c208208cec888544ef2a3a059c13d5891325b82ca9fc896e3"
    )


def test_confidence_signal_is_directionally_supportive_but_diagnostic_only() -> None:
    report = _load_json(REPORT_PATH)
    signal = report["signal_diagnostics"]
    confidence_by_acceptance = signal["raw_confidence_by_acceptance"]
    entropy_by_acceptance = signal["draft_entropy_by_acceptance"]

    assert confidence_by_acceptance["matches"]["mean"] == pytest.approx(0.6399255032391892)
    assert confidence_by_acceptance["nonmatches"]["mean"] == pytest.approx(0.22993675295425497)
    assert (
        confidence_by_acceptance["matches"]["mean"]
        > (confidence_by_acceptance["nonmatches"]["mean"])
    )

    assert entropy_by_acceptance["matches"]["mean"] == pytest.approx(1.8441315958487619)
    assert entropy_by_acceptance["nonmatches"]["mean"] == pytest.approx(3.7787872190060825)
    assert entropy_by_acceptance["nonmatches"]["mean"] > (entropy_by_acceptance["matches"]["mean"])

    assert signal["raw_confidence_roc_auc_diagnostic"] == pytest.approx(0.8655311519497983)


def test_fixed_bin_diagnostic_metrics_are_retained_without_promotion() -> None:
    report = _load_json(REPORT_PATH)
    signal = report["signal_diagnostics"]
    bins = signal["fixed_probability_bins"]

    assert signal["raw_confidence_brier_diagnostic"] == pytest.approx(0.18776377614415718)
    assert signal["fixed_bin_expected_calibration_error"] == pytest.approx(0.2469890072320898)
    assert signal["fixed_bin_maximum_calibration_error"] == pytest.approx(0.44021765887737274)

    assert [bucket["record_count"] for bucket in bins] == [24, 23, 16, 17, 40]
    assert [bucket["match_count"] for bucket in bins] == [13, 12, 15, 17, 40]
    assert bins[-1]["observed_match_rate"] == pytest.approx(1.0)

    assert report["threshold_promotion_status"] == "not_authorized_by_analysis"
    assert report["calibration_fit_status"] == "not_authorized_by_analysis"


def test_stratification_matches_governed_corpus_design() -> None:
    report = _load_json(REPORT_PATH)
    stratification = report["stratification"]

    assert stratification["split_record_counts"] == {
        "adversarial_regression": 12,
        "calibration": 36,
        "development": 36,
        "final_evaluation": 36,
    }
    assert stratification["workload_record_counts"] == {
        "code": 40,
        "open_ended_chat": 40,
        "structured_text": 40,
    }
    assert stratification["position_match_rates"]["3"]["match_rate"] == pytest.approx(
        0.9666666666666667
    )
    assert stratification["split_match_rates"]["final_evaluation"]["match_rate"] == (
        pytest.approx(0.6944444444444444)
    )


def test_analysis_does_not_authorize_stronger_claims() -> None:
    report = _load_json(REPORT_PATH)
    nonclaims = report["nonclaim_boundaries"]

    assert nonclaims == {
        "production_claim_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "threshold_promotion_status": "not_authorized",
    }
