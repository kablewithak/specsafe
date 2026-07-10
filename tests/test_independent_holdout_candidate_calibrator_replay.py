from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsafe.independent_holdout_replay import (
    IndependentHoldoutReplayError,
    PromotionRecommendation,
    build_independent_holdout_replay_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_ROOT = PROJECT_ROOT / (
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4"
)
RETAINED_REPORT_PATH = HOLDOUT_ROOT / "candidate_calibrator_holdout_replay_report.json"
MODEL_PATH = PROJECT_ROOT / (
    "evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case/calibrator_model.json"
)


def test_replay_report_rebuild_is_byte_deterministic() -> None:
    report = build_independent_holdout_replay_report(
        root=PROJECT_ROOT,
        write_output=False,
    )
    rebuilt = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    assert rebuilt.encode("utf-8") == RETAINED_REPORT_PATH.read_bytes()


def test_replay_retains_no_refit_and_independent_holdout_identity() -> None:
    report = build_independent_holdout_replay_report(
        root=PROJECT_ROOT,
        write_output=False,
    )
    assert report.calibrator_artifact_hash == (
        "e799e4c1e5db8798120b73e0c7e33b86e0f4f220b6360ad010cd0a5feb55ec36"
    )
    assert report.holdout_trace_archive_hash == (
        "3ab63ecd516be39ead9901ccc99d1d7a90f09bb2dcde5ca01bd5e258dfa03279"
    )
    assert report.holdout_trace_archive_id not in report.calibrator_fit_pool_archive_ids
    assert report.gate_checks.candidate_artifact_integrity_passed is True
    assert report.gate_checks.no_refit_passed is True


def test_replay_retains_probability_improvement_and_ranking_regression() -> None:
    report = build_independent_holdout_replay_report(
        root=PROJECT_ROOT,
        write_output=False,
    )
    assert report.holdout_record_count == 192
    assert report.holdout_positive_count == 136
    assert report.holdout_negative_count == 56
    assert report.brier_delta == pytest.approx(0.03811936896716564)
    assert report.fixed_bin_ece_delta == pytest.approx(0.10713044469407718)
    assert report.auroc_delta == pytest.approx(-0.024356617647058765)
    assert report.gate_checks.brier_improvement_passed is True
    assert report.gate_checks.fixed_bin_ece_improvement_passed is True
    assert report.gate_checks.ranking_safety_passed is False
    assert report.promotion_recommendation is PromotionRecommendation.KEEP_DIAGNOSTIC_ONLY
    assert report.calibrator_promotion_status == "not_authorized_ranking_safety_regression"


def test_replay_preserves_coverage_and_diagnostic_threshold_boundary() -> None:
    report = build_independent_holdout_replay_report(
        root=PROJECT_ROOT,
        write_output=False,
    )
    assert {key: value.record_count for key, value in report.coverage_by_workload.items()} == {
        "code": 64,
        "open_ended_chat": 64,
        "structured_text": 64,
    }
    assert {key: value.record_count for key, value in report.coverage_by_position.items()} == {
        "1": 48,
        "2": 48,
        "3": 48,
        "4": 48,
    }
    assert [item.threshold for item in report.threshold_preview] == [
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        0.95,
    ]
    assert all(item.coverage_warning is False for item in report.threshold_preview)
    assert report.threshold_promotion_status == "not_authorized"
    assert report.scheduler_promotion_status == "not_authorized"


def test_replay_fails_closed_when_candidate_artifact_changes(tmp_path: Path) -> None:
    project = tmp_path / "p"
    model_target = project / MODEL_PATH.relative_to(PROJECT_ROOT)
    model_target.parent.mkdir(parents=True)
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    model["calibrator_blocks"][0]["calibrated_probability"] = 0.5
    model_target.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(IndependentHoldoutReplayError, match="artifact hash mismatch"):
        build_independent_holdout_replay_report(root=project, write_output=False)
