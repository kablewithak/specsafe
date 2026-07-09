from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from specsafe.kaggle_trace_replay.expanded_archive_replay import (
    THRESHOLDS,
    build_replay_report,
    write_replay_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
REPORT_PATH = ATTEMPT_DIR / "trace_replay_report.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _threshold_rows(report: dict[str, Any]) -> dict[float, dict[str, Any]]:
    return {row["threshold"]: row for row in report["threshold_replay"]["threshold_reports"]}


def test_replay_report_regenerates_deterministically() -> None:
    expected = _load_json(REPORT_PATH)
    actual = build_replay_report(ATTEMPT_DIR)

    assert actual == expected


def test_replay_writer_preserves_retained_report() -> None:
    temp_path = REPORT_PATH.with_suffix(".tmp.json")
    try:
        write_replay_report(ATTEMPT_DIR, temp_path)
        assert _load_json(temp_path) == _load_json(REPORT_PATH)
    finally:
        temp_path.unlink(missing_ok=True)


def test_record_counts_and_source_analysis_boundary_are_preserved() -> None:
    report = _load_json(REPORT_PATH)

    assert report["replay_status"] == "diagnostic_replay_only"
    assert report["source_analysis_report_id"] == (
        "v5_qwen_trace_collection_v2_attempt_001_analysis"
    )
    assert report["record_counts"] == {
        "runtime_record_count": 120,
        "expected_outcome_record_count": 120,
        "timing_record_count": 120,
        "joined_record_count": 120,
        "case_count": 30,
    }
    assert report["source_trace_summary"]["target_argmax_match_count"] == 97
    assert report["source_trace_summary"]["target_argmax_nonmatch_count"] == 23


def test_manifest_hashes_and_runtime_label_separation_hold() -> None:
    report = _load_json(REPORT_PATH)

    assert all(report["manifest_hash_status"].values())
    assert report["runtime_outcome_join_status"]["one_to_one_join_passed"] is True
    assert report["runtime_outcome_join_status"]["joined_record_count"] == 120
    assert report["runtime_outcome_join_status"]["runtime_forbidden_fields_present"] == []


def test_threshold_replay_counts_match_retained_v2_archive() -> None:
    report = _load_json(REPORT_PATH)
    rows = _threshold_rows(report)

    assert tuple(report["threshold_replay"]["thresholds"]) == THRESHOLDS

    assert rows[0.0]["selected_record_count"] == 120
    assert rows[0.0]["selected_match_count"] == 97
    assert rows[0.0]["selected_nonmatch_count"] == 23

    assert rows[0.3]["selected_record_count"] == 84
    assert rows[0.3]["selected_match_count"] == 76
    assert rows[0.3]["selected_nonmatch_count"] == 8

    assert rows[0.4]["selected_record_count"] == 73
    assert rows[0.4]["selected_match_count"] == 72
    assert rows[0.4]["selected_nonmatch_count"] == 1

    assert rows[0.5]["selected_record_count"] == 64
    assert rows[0.5]["selected_match_count"] == 64
    assert rows[0.5]["selected_nonmatch_count"] == 0

    assert rows[0.8]["selected_record_count"] == 40
    assert rows[0.8]["selected_match_count"] == 40
    assert rows[0.8]["selected_nonmatch_count"] == 0


def test_threshold_counts_are_monotonic_as_threshold_increases() -> None:
    report = _load_json(REPORT_PATH)
    rows = report["threshold_replay"]["threshold_reports"]

    selected_counts = [row["selected_record_count"] for row in rows]
    selected_nonmatches = [row["selected_nonmatch_count"] for row in rows]

    assert selected_counts == sorted(selected_counts, reverse=True)
    assert selected_nonmatches == sorted(selected_nonmatches, reverse=True)


def test_frontier_is_diagnostic_not_threshold_promotion() -> None:
    report = _load_json(REPORT_PATH)
    frontier = report["threshold_replay"]["frontier_summary"]

    assert frontier["first_zero_nonmatch_threshold"] == 0.5
    assert frontier["zero_nonmatch_thresholds"] == [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    assert frontier["threshold_with_maximum_selected_match_rate"] is None
    assert frontier["threshold_promotion_status"] == "not_authorized_by_replay"


def test_stratified_diagnostic_threshold_is_present_but_not_promoted() -> None:
    report = _load_json(REPORT_PATH)
    stratified = report["threshold_replay"]["stratified_at_diagnostic_threshold"]

    assert report["threshold_replay"]["diagnostic_threshold_for_stratification"] == 0.5
    assert set(stratified["by_split"]) == {
        "adversarial_regression",
        "calibration",
        "development",
        "final_evaluation",
    }
    assert set(stratified["by_workload_type"]) == {
        "code",
        "open_ended_chat",
        "structured_text",
    }
    assert set(stratified["by_block_position_index"]) == {"1", "2", "3", "4"}


def test_nonclaim_boundaries_remain_blocked_after_replay() -> None:
    report = _load_json(REPORT_PATH)

    assert report["diagnostic_findings"]["replay_signal_status"] == (
        "directionally_supportive_not_promoted"
    )
    assert report["nonclaim_boundaries"] == {
        "calibration_fit_status": "not_authorized_by_replay",
        "threshold_promotion_status": "not_authorized_by_replay",
        "scheduler_promotion_status": "not_authorized_by_replay",
        "production_claim_status": "not_authorized",
        "public_release_status": "not_authorized_by_replay",
    }
    assert report["next_safe_gate"] == "v2_calibration_diagnostic_readiness_gate"
