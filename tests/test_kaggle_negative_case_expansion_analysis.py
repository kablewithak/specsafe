from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from specsafe.kaggle_trace_analysis.negative_case_expansion_analysis import (
    build_negative_case_analysis_report,
    build_negative_case_replay_report,
)

ATTEMPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-negative-case-expansion-v1"
    / "attempt-001-t4"
)
ANALYSIS_REPORT_PATH = ATTEMPT_DIR / "trace_analysis_report.json"
REPLAY_REPORT_PATH = ATTEMPT_DIR / "trace_replay_report.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_negative_case_analysis_report_is_deterministic() -> None:
    retained = _load_json(ANALYSIS_REPORT_PATH)
    regenerated = build_negative_case_analysis_report(ATTEMPT_DIR)

    assert regenerated == retained


def test_negative_case_replay_report_is_deterministic() -> None:
    retained = _load_json(REPLAY_REPORT_PATH)
    regenerated = build_negative_case_replay_report(ATTEMPT_DIR)

    assert regenerated == retained


def test_negative_case_analysis_preserves_archive_boundary() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)

    assert report["report_id"] == "v5_qwen_negative_case_expansion_v1_attempt_001_analysis"
    assert report["analysis_status"] == "diagnostic_analysis_only"
    assert report["collection_id"] == "v5-qwen-negative-case-expansion-v1"
    assert report["attempt_id"] == "attempt-001-t4"
    assert report["evidence_class"] == "kaggle_environment_measured"
    assert report["source_archive_boundary"]["raw_prompt_text_retained"] is False
    assert report["source_archive_boundary"]["secrets_printed"] is False


def test_negative_case_counts_match_collection_output() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)
    signal = report["signal_diagnostics"]

    assert report["record_counts"] == {
        "case_count": 16,
        "expected_outcome_record_count": 64,
        "runtime_record_count": 64,
        "timing_record_count": 64,
    }
    assert signal["target_argmax_match_count"] == 51
    assert signal["target_argmax_nonmatch_count"] == 13
    assert signal["target_argmax_match_rate"] == pytest.approx(0.796875)


def test_negative_case_crosses_combined_negative_count_floor_only_on_raw_count() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)
    combined = report["combined_raw_count_implication"]

    assert combined["v2_nonmatch_count"] == 23
    assert combined["negative_case_nonmatch_count"] == 13
    assert combined["combined_record_count"] == 184
    assert combined["combined_match_count"] == 148
    assert combined["combined_nonmatch_count"] == 36
    assert combined["minimum_negative_count_for_calibration_fit"] == 30
    assert combined["negative_count_floor_crossed_on_raw_count"] is True
    assert combined["negative_count_shortfall_after_collection"] == 0
    assert combined["calibration_fit_authorized_by_this_report"] is False


def test_runtime_outcome_join_and_label_boundary_are_clean() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)
    join_status = report["runtime_outcome_join_status"]

    assert join_status["one_to_one_join_passed"] is True
    assert join_status["joined_record_count"] == 64
    assert join_status["runtime_forbidden_fields_present"] == []


def test_hashes_match_retention_manifest_inputs() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)

    assert set(report["manifest_hash_status"].values()) == {True}
    assert report["input_file_hashes"]["runtime_records.jsonl"] == (
        "b782c8d00c32895909f498ce75f7c494e60a97e5b2f73d43b2bada4956e563c2"
    )
    assert report["input_file_hashes"]["expected_outcome_records.jsonl"] == (
        "e7dc7a24bd056d9677cb9afc226e12c8b9bbc0ae8face0afdcf72790f9265ae6"
    )


def test_confidence_signal_is_directionally_supportive_but_diagnostic_only() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)
    signal = report["signal_diagnostics"]
    confidence_by_acceptance = signal["raw_confidence_by_acceptance"]
    entropy_by_acceptance = signal["draft_entropy_by_acceptance"]

    assert confidence_by_acceptance["matches"]["mean"] == pytest.approx(0.43474915419139115)
    assert confidence_by_acceptance["nonmatches"]["mean"] == pytest.approx(0.207277827251416)
    assert (
        confidence_by_acceptance["matches"]["mean"]
        > (confidence_by_acceptance["nonmatches"]["mean"])
    )

    assert entropy_by_acceptance["matches"]["mean"] == pytest.approx(2.9756482623371423)
    assert entropy_by_acceptance["nonmatches"]["mean"] == pytest.approx(3.976880348645724)
    assert entropy_by_acceptance["nonmatches"]["mean"] > (entropy_by_acceptance["matches"]["mean"])

    assert signal["raw_confidence_roc_auc_diagnostic"] == pytest.approx(0.7918552036199095)


def test_fixed_bin_diagnostic_metrics_are_retained_without_promotion() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)
    signal = report["signal_diagnostics"]
    bins = signal["fixed_probability_bins"]

    assert signal["raw_confidence_brier_diagnostic"] == pytest.approx(0.3137117831119408)
    assert signal["fixed_bin_expected_calibration_error"] == pytest.approx(0.4083309590932913)
    assert signal["fixed_bin_maximum_calibration_error"] == pytest.approx(0.5645891942761161)

    assert [bucket["record_count"] for bucket in bins] == [18, 22, 7, 12, 5]
    assert [bucket["match_count"] for bucket in bins] == [9, 19, 6, 12, 5]
    assert bins[-1]["observed_match_rate"] == pytest.approx(1.0)

    assert report["threshold_promotion_status"] == "not_authorized_by_analysis"
    assert report["calibration_fit_status"] == "not_authorized_by_analysis"


def test_negative_case_replay_thresholds_are_monotonic_and_diagnostic() -> None:
    report = _load_json(REPLAY_REPORT_PATH)
    thresholds = report["threshold_diagnostics"]

    assert [row["selected_count"] for row in thresholds] == [64, 60, 46, 35, 24, 17, 17, 10, 5, 1]
    selected_nonmatch_counts = [row["selected_nonmatch_count"] for row in thresholds]
    assert selected_nonmatch_counts == [13, 10, 4, 4, 1, 0, 0, 0, 0, 0]
    assert thresholds[5]["threshold"] == "0.5"
    assert thresholds[5]["selected_match_count"] == 17
    assert thresholds[5]["selected_nonmatch_count"] == 0
    assert thresholds[8]["selected_match_rate"] == pytest.approx(1.0)

    selected_counts = [row["selected_count"] for row in thresholds]
    assert selected_counts == sorted(selected_counts, reverse=True)

    assert report["threshold_promotion_status"] == "not_authorized_by_replay"
    assert report["calibration_fit_status"] == "not_authorized_by_replay"


def test_stratification_matches_negative_case_design() -> None:
    report = _load_json(ANALYSIS_REPORT_PATH)
    stratification = report["stratification"]

    assert stratification["split_record_counts"] == {
        "negative_probe_calibration_candidate": 32,
        "negative_probe_holdout": 32,
    }
    assert stratification["workload_record_counts"] == {
        "code": 24,
        "open_ended_chat": 24,
        "structured_text": 16,
    }
    assert stratification["workload_match_rates"]["structured_text"]["match_rate"] == (
        pytest.approx(0.6875)
    )
    assert stratification["negative_case_intent_match_rates"]["ranking_ambiguity"] == {
        "match_count": 2,
        "match_rate": 0.5,
        "nonmatch_count": 2,
        "record_count": 4,
    }


def test_analysis_and_replay_do_not_authorize_stronger_claims() -> None:
    analysis_report = _load_json(ANALYSIS_REPORT_PATH)
    replay_report = _load_json(REPLAY_REPORT_PATH)

    assert analysis_report["nonclaim_boundaries"] == {
        "production_claim_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "threshold_promotion_status": "not_authorized",
    }
    assert replay_report["nonclaim_boundaries"] == {
        "production_claim_status": "not_authorized",
        "public_release_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "threshold_promotion_status": "not_authorized",
    }
