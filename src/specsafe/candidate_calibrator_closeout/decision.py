from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from specsafe.candidate_calibrator_closeout.models import (
    CandidateCalibratorPromotionCloseoutDecision,
    CandidateDisposition,
    CloseoutGateChecks,
    CloseoutOutcome,
    MetricSummary,
    PromotionAttemptStatus,
)

SOURCE_REPLAY_REPORT = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/"
    "candidate_calibrator_holdout_replay_report.json"
)
OUTPUT_PATH = SOURCE_REPLAY_REPORT.with_name(
    "candidate_calibrator_promotion_closeout_decision.json"
)
EXPECTED_REPLAY_REPORT_SHA256 = "402df4475b05eead800a5ba7f6b4ae96587fd5bfbe83f20966ac180888e1467f"
EXPECTED_REPLAY_REPORT_ID = "v5-qwen-candidate-calibrator-independent-holdout-replay-v1"
EXPECTED_REPLAY_RUN_ID = "v5-qwen-candidate-calibrator-independent-holdout-replay-run-001"
EXPECTED_CALIBRATOR_ID = "v5-qwen-combined-fixed-bin-isotonic-calibrator-v1"
EXPECTED_FAILURE_LABEL = "ranking_safety_regression"
DECISION_CREATED_AT = "2026-07-10T19:55:56Z"
DECISION_SOURCE_COMMIT = "cd1780f"


class CandidateCalibratorCloseoutError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidateCalibratorCloseoutError(f"expected JSON object: {path}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateCalibratorCloseoutError(message)


def _validate_source_replay(report: dict[str, Any], report_sha256: str) -> None:
    _require(
        report_sha256 == EXPECTED_REPLAY_REPORT_SHA256,
        "source replay report hash mismatch",
    )
    _require(
        report.get("report_id") == EXPECTED_REPLAY_REPORT_ID,
        "unexpected source replay report id",
    )
    _require(
        report.get("run_id") == EXPECTED_REPLAY_RUN_ID,
        "unexpected source replay run id",
    )
    _require(
        report.get("calibrator_artifact_id") == EXPECTED_CALIBRATOR_ID,
        "unexpected calibrator artifact id",
    )
    _require(
        report.get("holdout_replay_status") == "completed_with_ranking_safety_regression",
        "source replay is not at the required closeout boundary",
    )
    _require(
        report.get("promotion_recommendation") == CloseoutOutcome.KEEP_DIAGNOSTIC_ONLY,
        "source replay recommendation is not KEEP_DIAGNOSTIC_ONLY",
    )
    failure_labels = report.get("failure_labels")
    _require(
        isinstance(failure_labels, list) and EXPECTED_FAILURE_LABEL in failure_labels,
        "source replay does not retain the ranking safety failure",
    )
    gate_checks = report.get("gate_checks")
    _require(isinstance(gate_checks, dict), "source replay gate checks missing")
    _require(gate_checks.get("no_refit_passed") is True, "source replay no-refit gate failed")
    _require(
        gate_checks.get("brier_improvement_passed") is True,
        "source replay Brier gate did not pass",
    )
    _require(
        gate_checks.get("fixed_bin_ece_improvement_passed") is True,
        "source replay fixed-bin ECE gate did not pass",
    )
    _require(
        gate_checks.get("ranking_safety_passed") is False,
        "closeout requires a retained ranking safety failure",
    )
    for status_field in (
        "threshold_promotion_status",
        "scheduler_promotion_status",
        "public_release_status",
        "production_claim_status",
    ):
        _require(
            report.get(status_field) == "not_authorized",
            f"source replay unexpectedly authorizes {status_field}",
        )


def build_candidate_calibrator_promotion_closeout(
    *,
    root: Path | str = Path("."),
    write_output: bool = True,
) -> CandidateCalibratorPromotionCloseoutDecision:
    repo_root = Path(root)
    replay_path = repo_root / SOURCE_REPLAY_REPORT
    if not replay_path.exists():
        raise FileNotFoundError(replay_path)

    report_sha256 = _sha256_file(replay_path)
    report = _read_json(replay_path)
    _validate_source_replay(report, report_sha256)

    raw_metrics = report["raw_metrics"]
    calibrated_metrics = report["calibrated_metrics"]
    protocol = report["protocol"]
    decision = CandidateCalibratorPromotionCloseoutDecision(
        schema_version="candidate_calibrator_promotion_closeout_decision_v1",
        decision_id="v5-qwen-candidate-calibrator-promotion-closeout-v1",
        created_at=DECISION_CREATED_AT,
        source_commit=DECISION_SOURCE_COMMIT,
        source_replay_report=str(SOURCE_REPLAY_REPORT).replace("\\", "/"),
        source_replay_report_sha256=report_sha256,
        source_replay_report_id=str(report["report_id"]),
        source_replay_run_id=str(report["run_id"]),
        calibrator_artifact_id=str(report["calibrator_artifact_id"]),
        calibrator_artifact_hash=str(report["calibrator_artifact_hash"]),
        holdout_trace_archive_id=str(report["holdout_trace_archive_id"]),
        holdout_trace_archive_hash=str(report["holdout_trace_archive_hash"]),
        holdout_record_count=int(report["holdout_record_count"]),
        holdout_positive_count=int(report["holdout_positive_count"]),
        holdout_negative_count=int(report["holdout_negative_count"]),
        failure_labels=tuple(str(value) for value in report["failure_labels"]),
        metrics=MetricSummary(
            raw_brier_score=float(raw_metrics["brier_score"]),
            calibrated_brier_score=float(calibrated_metrics["brier_score"]),
            brier_improvement=float(report["brier_delta"]),
            raw_fixed_bin_ece=float(raw_metrics["fixed_bin_ece"]),
            calibrated_fixed_bin_ece=float(calibrated_metrics["fixed_bin_ece"]),
            fixed_bin_ece_improvement=float(report["fixed_bin_ece_delta"]),
            raw_auroc=float(raw_metrics["auroc"]),
            calibrated_auroc=float(calibrated_metrics["auroc"]),
            auroc_delta=float(report["auroc_delta"]),
            maximum_allowed_auroc_degradation=float(protocol["maximum_auroc_degradation"]),
        ),
        gate_checks=CloseoutGateChecks(
            source_replay_integrity_passed=True,
            source_replay_completed=True,
            no_refit_passed=True,
            probability_quality_improved=True,
            ranking_safety_failed=True,
            replay_recommendation_adopted=True,
            current_candidate_promotion_closed=True,
            threshold_promotion_blocked=True,
            scheduler_promotion_blocked=True,
            holdout_reuse_blocked=True,
            bounded_publication_only=True,
        ),
        decision_outcome=CloseoutOutcome.KEEP_DIAGNOSTIC_ONLY,
        candidate_disposition=CandidateDisposition.RETAINED_DIAGNOSTIC_NEGATIVE_EVIDENCE,
        promotion_attempt_status=PromotionAttemptStatus.CLOSED_NOT_PROMOTED,
        calibrator_promotion_status="not_authorized_closed_ranking_safety_regression",
        automated_scheduling_confidence_status="unfit_use_conservative_fallback",
        threshold_promotion_status="not_authorized",
        scheduler_promotion_status="not_authorized",
        public_release_status="bounded_negative_evidence_only",
        production_claim_status="not_authorized",
        holdout_reuse_policy=(
            "do_not_refit_current_candidate_from_holdout",
            "do_not_tune_thresholds_from_holdout",
            "do_not_merge_holdout_into_future_fit_pool",
            "preserve_holdout_as_consumed_promotion_evidence",
        ),
        authorized_future_work=(
            "retain_current_candidate_as_diagnostic_negative_evidence",
            "use_conservative_fallback_for_probability_driven_automation",
            "design_a_new_candidate_under_a_separate_predeclared_protocol",
            "collect_fresh_fit_and_independent_holdout_evidence_for_any_new_candidate",
            "package_this_negative_result_publicly_with_explicit_non_promotion_labels",
        ),
        blocked_work=(
            "promote_current_candidate_calibrator",
            "promote_thresholds_from_current_holdout",
            "run_or_promote_scheduler_using_current_candidate_as_trusted_probability",
            "claim_adaptive_policy_utility_from_current_candidate",
            "present_public_artifacts_as_positive_promotion_proof",
            "claim_production_speed_latency_throughput_cost_or_serving_readiness",
        ),
        claims_permitted=(
            "The candidate completed independent holdout replay without refit.",
            "The candidate improved aggregate Brier score and fixed-bin ECE on holdout.",
            "The candidate regressed ranking safety beyond the declared tolerance.",
            "The promotion attempt is closed and the candidate is not promoted.",
            "The retained result is diagnostic negative evidence.",
        ),
        claims_forbidden=(
            "The current candidate calibrator is promoted.",
            "The current calibrated probabilities are fit for automated scheduling.",
            "Any threshold or scheduler is promoted from the current holdout.",
            "Adaptive-policy utility improvement is proven.",
            "Public artifacts demonstrate positive promotion proof.",
            "Production speed, latency, throughput, cost, or serving readiness is proven.",
        ),
        next_authorized_step=(
            "bounded_negative_evidence_packaging_or_new_calibrator_redesign_governance"
        ),
    )

    if write_output:
        output_path = repo_root / OUTPUT_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(decision.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    return decision
