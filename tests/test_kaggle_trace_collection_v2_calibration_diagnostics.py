from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from specsafe.kaggle_trace_calibration.expanded_archive_diagnostics import (
    build_calibration_diagnostic_report,
    write_json_lf,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
REPORT_PATH = ATTEMPT_DIR / "trace_calibration_diagnostic_report.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_calibration_diagnostic_report_regenerates_deterministically(
    tmp_path: Path,
) -> None:
    expected = _load_json(REPORT_PATH)
    actual = build_calibration_diagnostic_report(ATTEMPT_DIR)

    assert actual == expected

    written = tmp_path / "trace_calibration_diagnostic_report.json"
    write_json_lf(written, actual)
    assert _load_json(written) == expected
    assert written.read_bytes().endswith(b"\n")


def test_calibration_readiness_blocks_fit_on_negative_count() -> None:
    report = _load_json(REPORT_PATH)
    readiness = report["calibration_fit_readiness"]

    assert readiness["minimum_record_count_for_calibration_fit"] == 100
    assert readiness["minimum_positive_count_for_calibration_fit"] == 30
    assert readiness["minimum_negative_count_for_calibration_fit"] == 30
    assert readiness["observed_record_count"] == 120
    assert readiness["observed_positive_count"] == 97
    assert readiness["observed_negative_count"] == 23
    assert (
        readiness["calibration_fit_readiness_status"]
        == "insufficient_negative_count_for_calibration_fit_signal_supportive"
    )
    assert readiness["calibration_fit_authorized"] is False
    assert readiness["calibration_fit_status"] == "not_authorized_by_diagnostic"
    assert (
        readiness["next_authorized_step"] == "expand_negative_case_coverage_before_calibration_fit"
    )


def test_signal_diagnostics_are_directionally_supportive_but_not_fit_authorizing() -> None:
    report = _load_json(REPORT_PATH)
    diagnostics = report["calibration_diagnostics"]

    assert diagnostics["signal_diagnostic_passed"] is True
    assert diagnostics["raw_confidence_roc_auc_diagnostic"] == 0.8655311519497983
    assert diagnostics["raw_draft_probability_brier_diagnostic"] == 0.18776377614415718
    assert diagnostics["fixed_bin_expected_calibration_error"] == 0.2469890072320898
    assert diagnostics["fixed_bin_maximum_calibration_error"] == 0.44021765887737274


def test_fixed_bin_reports_preserve_coverage_and_observed_rates() -> None:
    report = _load_json(REPORT_PATH)
    bins = report["calibration_diagnostics"]["fixed_bin_reports"]

    assert [bin_report["record_count"] for bin_report in bins] == [24, 23, 16, 17, 40]
    assert [bin_report["match_count"] for bin_report in bins] == [13, 12, 15, 17, 40]
    assert [bin_report["nonmatch_count"] for bin_report in bins] == [11, 11, 1, 0, 0]
    assert bins[0]["observed_match_rate"] == 0.5416666666666666
    assert bins[2]["observed_match_rate"] == 0.9375
    assert bins[4]["observed_match_rate"] == 1.0


def test_runtime_outcome_boundary_and_manifest_hashes_remain_clean() -> None:
    report = _load_json(REPORT_PATH)

    assert report["runtime_outcome_join_status"]["one_to_one_join_passed"] is True
    assert report["runtime_outcome_join_status"]["joined_record_count"] == 120
    assert report["runtime_outcome_join_status"]["runtime_forbidden_fields_present"] == []
    assert all(report["manifest_hash_status"].values())
    assert report["source_analysis_report_id"] == "v5_qwen_trace_collection_v2_attempt_001_analysis"
    assert report["source_replay_report_id"] == "v5_qwen_trace_collection_v2_attempt_001_replay"


def test_non_authorization_statuses_are_explicit() -> None:
    report = _load_json(REPORT_PATH)
    non_authorization = report["non_authorization"]

    assert (
        non_authorization["threshold_promotion_status"]
        == "not_authorized_by_calibration_diagnostic"
    )
    assert (
        non_authorization["scheduler_promotion_status"]
        == "not_authorized_by_calibration_diagnostic"
    )
    assert non_authorization["public_release_status"] == "not_authorized_by_calibration_diagnostic"
    assert (
        non_authorization["production_claim_status"] == "not_authorized_by_calibration_diagnostic"
    )
    assert report["interpretation"]["diagnostic_only"] is True
    assert report["interpretation"]["stronger_claims_blocked"] is True
