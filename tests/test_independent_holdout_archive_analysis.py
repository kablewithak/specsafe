from __future__ import annotations

import json
from pathlib import Path

from specsafe.independent_holdout_analysis import (
    AnalysisStatus,
    analyze_independent_holdout,
    write_analysis_report,
)

ARCHIVE_DIR = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/"
    "attempt-001-t4"
)
REPORT_PATH = ARCHIVE_DIR / "independent_holdout_analysis_report.json"
SOURCE_COMMIT = "9b03855"


def test_analysis_confirms_complete_replay_alignment() -> None:
    report = analyze_independent_holdout(ARCHIVE_DIR, source_commit=SOURCE_COMMIT)

    assert report.analysis_status is AnalysisStatus.REPLAY_READY
    assert report.runtime_record_count == 192
    assert report.expected_outcome_record_count == 192
    assert report.timing_record_count == 192
    assert report.unique_trace_count == 192
    assert report.case_count == 48
    assert report.joined_record_count == 192
    assert report.duplicate_join_key_count == 0
    assert report.missing_runtime_outcome_count == 0
    assert report.missing_runtime_timing_count == 0
    assert report.replay_blockers == ()


def test_analysis_preserves_workload_and_position_coverage() -> None:
    report = analyze_independent_holdout(ARCHIVE_DIR, source_commit=SOURCE_COMMIT)

    assert report.coverage_by_workload["code"].model_dump() == {
        "record_count": 64,
        "positive_count": 55,
        "negative_count": 9,
        "positive_rate": 0.859375,
        "mean_raw_confidence": 0.5969283755403012,
    }
    assert report.coverage_by_workload["open_ended_chat"].negative_count == 19
    assert report.coverage_by_workload["structured_text"].negative_count == 28
    assert report.coverage_by_position["1"].negative_count == 26
    assert report.coverage_by_position["4"].positive_count == 38


def test_analysis_exposes_exact_no_refit_replay_field_map() -> None:
    report = analyze_independent_holdout(ARCHIVE_DIR, source_commit=SOURCE_COMMIT)

    assert report.replay_field_map.join_key == (
        "trace_id",
        "decode_round",
        "block_position_index",
    )
    assert report.replay_field_map.calibrator_input_field == "raw_confidence"
    assert report.replay_field_map.diagnostic_label_field == "observed_acceptance"
    assert "refit_candidate_calibrator_from_holdout_archive" in (
        report.replay_field_map.forbidden_fit_actions
    )
    assert report.calibrator_promotion_status.value == (
        "not_authorized_pending_independent_holdout_replay"
    )
    assert report.threshold_promotion_status == "not_authorized"
    assert report.scheduler_promotion_status == "not_authorized"


def test_retained_analysis_report_is_canonical_and_matches_recomputation(tmp_path: Path) -> None:
    generated_path = tmp_path / "analysis.json"
    generated = write_analysis_report(
        ARCHIVE_DIR,
        generated_path,
        source_commit=SOURCE_COMMIT,
    )
    retained = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert retained == generated.model_dump(mode="json")
    assert generated.raw_brier_diagnostic == 0.18747805218884495
    assert generated.raw_discrimination_auc == 0.881827731092437
    assert generated.raw_prompt_text_retained is False
