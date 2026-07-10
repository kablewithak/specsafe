from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CloseoutOutcome(StrEnum):
    KEEP_DIAGNOSTIC_ONLY = "KEEP_DIAGNOSTIC_ONLY"


class CandidateDisposition(StrEnum):
    RETAINED_DIAGNOSTIC_NEGATIVE_EVIDENCE = "retained_diagnostic_negative_evidence"


class PromotionAttemptStatus(StrEnum):
    CLOSED_NOT_PROMOTED = "closed_not_promoted"


class MetricSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    brier_improvement: float
    raw_fixed_bin_ece: float = Field(ge=0.0, le=1.0)
    calibrated_fixed_bin_ece: float = Field(ge=0.0, le=1.0)
    fixed_bin_ece_improvement: float
    raw_auroc: float = Field(ge=0.0, le=1.0)
    calibrated_auroc: float = Field(ge=0.0, le=1.0)
    auroc_delta: float
    maximum_allowed_auroc_degradation: float = Field(ge=0.0)


class CloseoutGateChecks(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_replay_integrity_passed: bool
    source_replay_completed: bool
    no_refit_passed: bool
    probability_quality_improved: bool
    ranking_safety_failed: bool
    replay_recommendation_adopted: bool
    current_candidate_promotion_closed: bool
    threshold_promotion_blocked: bool
    scheduler_promotion_blocked: bool
    holdout_reuse_blocked: bool
    bounded_publication_only: bool


class CandidateCalibratorPromotionCloseoutDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    decision_id: str
    created_at: str
    source_commit: str
    source_replay_report: str
    source_replay_report_sha256: str
    source_replay_report_id: str
    source_replay_run_id: str
    calibrator_artifact_id: str
    calibrator_artifact_hash: str
    holdout_trace_archive_id: str
    holdout_trace_archive_hash: str
    holdout_record_count: int = Field(ge=0)
    holdout_positive_count: int = Field(ge=0)
    holdout_negative_count: int = Field(ge=0)
    failure_labels: tuple[str, ...]
    metrics: MetricSummary
    gate_checks: CloseoutGateChecks
    decision_outcome: CloseoutOutcome
    candidate_disposition: CandidateDisposition
    promotion_attempt_status: PromotionAttemptStatus
    calibrator_promotion_status: str
    automated_scheduling_confidence_status: str
    threshold_promotion_status: str
    scheduler_promotion_status: str
    public_release_status: str
    production_claim_status: str
    holdout_reuse_policy: tuple[str, ...]
    authorized_future_work: tuple[str, ...]
    blocked_work: tuple[str, ...]
    claims_permitted: tuple[str, ...]
    claims_forbidden: tuple[str, ...]
    next_authorized_step: str
