from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.candidate_calibrator_closeout import (
    CandidateCalibratorCloseoutError,
    CandidateDisposition,
    CloseoutOutcome,
    PromotionAttemptStatus,
    build_candidate_calibrator_promotion_closeout,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_ROOT = PROJECT_ROOT / (
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4"
)
SOURCE_REPLAY_PATH = HOLDOUT_ROOT / "candidate_calibrator_holdout_replay_report.json"
RETAINED_DECISION_PATH = HOLDOUT_ROOT / "candidate_calibrator_promotion_closeout_decision.json"


def test_closeout_decision_rebuild_is_byte_deterministic() -> None:
    decision = build_candidate_calibrator_promotion_closeout(
        root=PROJECT_ROOT,
        write_output=False,
    )
    rebuilt = json.dumps(decision.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    assert rebuilt.encode("utf-8") == RETAINED_DECISION_PATH.read_bytes()


def test_closeout_adopts_replay_recommendation_and_closes_promotion() -> None:
    decision = build_candidate_calibrator_promotion_closeout(
        root=PROJECT_ROOT,
        write_output=False,
    )
    assert decision.decision_outcome is CloseoutOutcome.KEEP_DIAGNOSTIC_ONLY
    assert decision.candidate_disposition is (
        CandidateDisposition.RETAINED_DIAGNOSTIC_NEGATIVE_EVIDENCE
    )
    assert decision.promotion_attempt_status is PromotionAttemptStatus.CLOSED_NOT_PROMOTED
    assert decision.calibrator_promotion_status == (
        "not_authorized_closed_ranking_safety_regression"
    )
    assert decision.failure_labels == ("ranking_safety_regression",)
    assert decision.gate_checks.current_candidate_promotion_closed is True


def test_closeout_preserves_metrics_and_conservative_fallback_boundary() -> None:
    decision = build_candidate_calibrator_promotion_closeout(
        root=PROJECT_ROOT,
        write_output=False,
    )
    assert decision.holdout_record_count == 192
    assert decision.holdout_positive_count == 136
    assert decision.holdout_negative_count == 56
    assert decision.metrics.brier_improvement == pytest.approx(0.03811936896716564)
    assert decision.metrics.fixed_bin_ece_improvement == pytest.approx(0.10713044469407718)
    assert decision.metrics.auroc_delta == pytest.approx(-0.024356617647058765)
    assert decision.metrics.maximum_allowed_auroc_degradation == pytest.approx(0.001)
    assert decision.gate_checks.probability_quality_improved is True
    assert decision.gate_checks.ranking_safety_failed is True
    assert decision.automated_scheduling_confidence_status == ("unfit_use_conservative_fallback")


def test_closeout_blocks_holdout_reuse_thresholds_and_scheduler_promotion() -> None:
    decision = build_candidate_calibrator_promotion_closeout(
        root=PROJECT_ROOT,
        write_output=False,
    )
    assert "do_not_refit_current_candidate_from_holdout" in decision.holdout_reuse_policy
    assert "do_not_tune_thresholds_from_holdout" in decision.holdout_reuse_policy
    assert "do_not_merge_holdout_into_future_fit_pool" in decision.holdout_reuse_policy
    assert decision.threshold_promotion_status == "not_authorized"
    assert decision.scheduler_promotion_status == "not_authorized"
    assert decision.public_release_status == "bounded_negative_evidence_only"
    assert decision.production_claim_status == "not_authorized"


def test_closeout_fails_closed_when_source_replay_changes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    target = project / SOURCE_REPLAY_PATH.relative_to(PROJECT_ROOT)
    target.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE_REPLAY_PATH, target)
    report = json.loads(target.read_text(encoding="utf-8"))
    report["promotion_recommendation"] = "PROMOTE_CANDIDATE_CALIBRATOR"
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(CandidateCalibratorCloseoutError, match="hash mismatch"):
        build_candidate_calibrator_promotion_closeout(root=project, write_output=False)
