from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from specsafe.kaggle_trace_calibration.combined_archive_diagnostics import (
    build_combined_calibration_diagnostic_report,
    write_json_lf,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
V2_ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
NEGATIVE_CASE_ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-negative-case-expansion-v1"
    / "attempt-001-t4"
)
REPORT_PATH = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-calibration"
    / "v5-qwen-combined-v2-negative-case"
    / "combined_calibration_diagnostic_report.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_combined_calibration_report_regenerates_deterministically(
    tmp_path: Path,
) -> None:
    expected = _load_json(REPORT_PATH)
    actual = build_combined_calibration_diagnostic_report(
        V2_ATTEMPT_DIR,
        NEGATIVE_CASE_ATTEMPT_DIR,
    )

    assert actual == expected

    written = tmp_path / "combined_calibration_diagnostic_report.json"
    write_json_lf(written, actual)
    assert _load_json(written) == expected
    assert written.read_bytes().endswith(b"\n")


def test_combined_counts_cross_calibration_sample_floors() -> None:
    report = _load_json(REPORT_PATH)
    counts = report["record_counts"]
    readiness = report["calibration_fit_readiness"]

    assert counts["runtime_record_count"] == 184
    assert counts["expected_outcome_record_count"] == 184
    assert counts["target_argmax_match_count"] == 148
    assert counts["target_argmax_nonmatch_count"] == 36
    assert readiness["minimum_record_count_for_calibration_fit"] == 100
    assert readiness["minimum_positive_count_for_calibration_fit"] == 30
    assert readiness["minimum_negative_count_for_calibration_fit"] == 30
    assert readiness["observed_record_count"] == 184
    assert readiness["observed_positive_count"] == 148
    assert readiness["observed_negative_count"] == 36
    assert readiness["negative_count_floor_crossed"] is True


def test_combined_readiness_authorizes_only_next_fit_gate() -> None:
    report = _load_json(REPORT_PATH)
    readiness = report["calibration_fit_readiness"]

    assert (
        readiness["calibration_fit_readiness_status"]
        == "sample_and_signal_ready_for_calibration_fit"
    )
    assert readiness["calibration_fit_authorized"] is True
    assert readiness["calibration_fit_execution_status"] == "not_started"
    assert readiness["next_authorized_step"] == "fit_kaggle_derived_calibrator_under_separate_gate"


def test_combined_signal_diagnostic_is_supportive_but_raw_calibration_is_not_claimed() -> None:
    report = _load_json(REPORT_PATH)
    diagnostics = report["calibration_diagnostics"]

    assert diagnostics["signal_diagnostic_passed"] is True
    assert diagnostics["raw_confidence_roc_auc_diagnostic"] == 0.8363363363363363
    assert diagnostics["raw_draft_probability_brier_diagnostic"] == 0.2315717785677341
    assert diagnostics["fixed_bin_expected_calibration_error"] == 0.303107947009899
    assert diagnostics["fixed_bin_maximum_calibration_error"] == 0.430998647990434

    interpretation = report["interpretation"]
    assert interpretation["calibration_fitting_may_start_next_gate"] is True
    assert interpretation["stronger_claims_blocked"] is True


def test_fixed_bin_reports_preserve_combined_coverage() -> None:
    report = _load_json(REPORT_PATH)
    bins = report["calibration_diagnostics"]["fixed_bin_reports"]

    assert [bin_report["record_count"] for bin_report in bins] == [42, 45, 23, 29, 45]
    assert [bin_report["match_count"] for bin_report in bins] == [22, 31, 21, 29, 45]
    assert [bin_report["nonmatch_count"] for bin_report in bins] == [20, 14, 2, 0, 0]
    assert bins[0]["observed_match_rate"] == 0.5238095238095238
    assert bins[2]["observed_match_rate"] == 0.9130434782608695
    assert bins[4]["observed_match_rate"] == 1.0


def test_source_summaries_preserve_v2_and_negative_case_counts() -> None:
    report = _load_json(REPORT_PATH)
    summaries = {item["source_id"]: item for item in report["source_summaries"]}

    v2 = summaries["v2_trace_collection"]
    negative_case = summaries["negative_case_expansion"]

    assert v2["runtime_record_count"] == 120
    assert v2["target_argmax_match_count"] == 97
    assert v2["target_argmax_nonmatch_count"] == 23
    assert v2["source_commit"] == "0dfd5118a471adeec92a609d817d06d698f783a7"

    assert negative_case["runtime_record_count"] == 64
    assert negative_case["target_argmax_match_count"] == 51
    assert negative_case["target_argmax_nonmatch_count"] == 13
    assert negative_case["source_commit"] == "cd238e3e84391585be01e635ce74c4d400ba2dce"


def test_source_report_ids_and_manifest_hashes_are_preserved() -> None:
    report = _load_json(REPORT_PATH)
    summaries = {item["source_id"]: item for item in report["source_summaries"]}

    assert (
        summaries["v2_trace_collection"]["source_report_ids"]["calibration_diagnostic_report_id"]
        == "v5_qwen_trace_collection_v2_attempt_001_calibration_diagnostic"
    )
    assert (
        summaries["negative_case_expansion"]["source_report_ids"]["analysis_report_id"]
        == "v5_qwen_negative_case_expansion_v1_attempt_001_analysis"
    )

    assert all(report["manifest_hash_status"]["v2_trace_collection"].values())
    assert all(report["manifest_hash_status"]["negative_case_expansion"].values())


def test_runtime_outcome_boundary_stays_clean_across_combined_pool() -> None:
    report = _load_json(REPORT_PATH)
    join_status = report["runtime_outcome_join_status"]

    assert join_status["one_to_one_join_passed"] is True
    assert join_status["joined_record_count"] == 184
    assert join_status["runtime_forbidden_fields_present"] == []
    assert join_status["combined_trace_id_strategy"] == "source_id_double_colon_trace_id"


def test_stratified_source_and_split_counts_are_diagnostic() -> None:
    report = _load_json(REPORT_PATH)
    stratified = report["calibration_diagnostics"]["stratified_counts"]

    by_source = stratified["by_source_id"]
    assert by_source["v2_trace_collection"]["record_count"] == 120
    assert by_source["negative_case_expansion"]["record_count"] == 64

    by_split = stratified["by_split"]
    assert by_split["calibration"]["record_count"] == 36
    assert by_split["negative_probe_calibration_candidate"]["record_count"] == 32
    assert by_split["negative_probe_holdout"]["record_count"] == 32


def test_fit_boundary_is_explicit_and_does_not_promote_thresholds() -> None:
    report = _load_json(REPORT_PATH)
    fit_boundary = report["proposed_fit_boundary"]

    assert fit_boundary["authorized_only_if_calibration_fit_authorized"] is True
    assert fit_boundary["fit_must_be_separate_pr"] is True
    assert fit_boundary["candidate_fit_splits"] == [
        "v2_trace_collection:calibration",
        "negative_case_expansion:negative_probe_calibration_candidate",
    ]
    assert (
        "v2_trace_collection:final_evaluation" in fit_boundary["holdout_or_final_evaluation_splits"]
    )
    assert fit_boundary["threshold_promotion_allowed_from_this_report"] is False
    assert fit_boundary["scheduler_promotion_allowed_from_this_report"] is False


def test_non_authorization_statuses_remain_explicit() -> None:
    report = _load_json(REPORT_PATH)
    non_authorization = report["non_authorization"]

    assert (
        non_authorization["calibrator_promotion_status"] == "not_authorized_by_combined_diagnostic"
    )
    assert (
        non_authorization["threshold_promotion_status"] == "not_authorized_by_combined_diagnostic"
    )
    assert (
        non_authorization["scheduler_promotion_status"] == "not_authorized_by_combined_diagnostic"
    )
    assert non_authorization["public_release_status"] == "not_authorized_by_combined_diagnostic"
    assert non_authorization["production_claim_status"] == "not_authorized_by_combined_diagnostic"
    assert report["interpretation"]["diagnostic_only"] is True
