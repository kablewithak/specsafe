from __future__ import annotations

from enum import StrEnum
from math import isclose
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PromotionRecommendation(StrEnum):
    PROMOTE_CANDIDATE_CALIBRATOR = "PROMOTE_CANDIDATE_CALIBRATOR"
    KEEP_DIAGNOSTIC_ONLY = "KEEP_DIAGNOSTIC_ONLY"
    REQUIRE_ADDITIONAL_HOLDOUT_EVIDENCE = "REQUIRE_ADDITIONAL_HOLDOUT_EVIDENCE"
    REJECT_CANDIDATE_CALIBRATOR = "REJECT_CANDIDATE_CALIBRATOR"


class HoldoutReplayFailureLabel(StrEnum):
    HOLDOUT_MANIFEST_MISMATCH = "holdout_manifest_mismatch"
    HOLDOUT_PROVENANCE_MISSING = "holdout_provenance_missing"
    HOLDOUT_SPLIT_LEAKAGE = "holdout_split_leakage"
    HOLDOUT_NEGATIVE_COUNT_INSUFFICIENT = "holdout_negative_count_insufficient"
    HOLDOUT_COVERAGE_INSUFFICIENT = "holdout_coverage_insufficient"
    CALIBRATION_QUALITY_REGRESSION = "calibration_quality_regression"
    RANKING_SAFETY_REGRESSION = "ranking_safety_regression"
    THRESHOLD_PREVIEW_SPARSE_SUPPORT = "threshold_preview_sparse_support"
    CALIBRATOR_REFIT_DETECTED = "calibrator_refit_detected"
    UNSUPPORTED_PROMOTION_CLAIM = "unsupported_promotion_claim"


class CandidateCalibratorBlock(StrictModel):
    lower_bound: float = Field(ge=0.0, le=1.0)
    upper_bound: float = Field(gt=0.0, le=1.000000001)
    record_count: int = Field(gt=0)
    match_count: int = Field(ge=0)
    nonmatch_count: int = Field(ge=0)
    calibrated_probability: float = Field(ge=0.0, le=1.0)
    source_bin_indexes: tuple[int, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_counts(self) -> CandidateCalibratorBlock:
        if self.match_count + self.nonmatch_count != self.record_count:
            raise ValueError("calibrator block counts must sum to record_count")
        if self.lower_bound >= self.upper_bound:
            raise ValueError("calibrator block lower_bound must be below upper_bound")
        return self


class CandidateCalibratorArtifact(StrictModel):
    model_schema_version: Literal["kaggle_calibrator_model_v1"]
    model_id: Literal["v5-qwen-combined-fixed-bin-isotonic-calibrator-v1"]
    calibration_evidence_id: Literal["v5-qwen-combined-v2-negative-case"]
    calibrator_type: Literal["fixed_bin_laplace_isotonic_v1"]
    input_feature: Literal["raw_confidence"]
    output_feature: Literal["calibrated_acceptance_probability"]
    fit_record_count: Literal[184]
    fit_positive_count: Literal[148]
    fit_negative_count: Literal[36]
    bin_edges: tuple[float, ...] = Field(min_length=8, max_length=8)
    laplace_alpha: Literal[1.0]
    laplace_beta: Literal[1.0]
    calibrator_blocks: tuple[CandidateCalibratorBlock, ...] = Field(min_length=1)
    missing_or_out_of_range_input_policy: Literal["fail_closed"]
    calibrator_fit_status: Literal["fit_retained"]
    calibrator_promotion_status: Literal["not_authorized"]
    threshold_promotion_status: Literal["not_authorized"]
    scheduler_promotion_status: Literal["not_authorized"]
    public_release_status: Literal["not_authorized"]
    production_claim_status: Literal["not_authorized"]
    source_archives: tuple[
        Literal[
            "v5-qwen-governed-trace-collection-v2/attempt-001-t4",
            "v5-qwen-negative-case-expansion-v1/attempt-001-t4",
        ],
        ...,
    ] = Field(min_length=2, max_length=2)
    source_diagnostic_report: str
    evidence_boundary: str

    @model_validator(mode="after")
    def validate_artifact(self) -> CandidateCalibratorArtifact:
        if self.fit_positive_count + self.fit_negative_count != self.fit_record_count:
            raise ValueError("artifact fit counts must sum to fit_record_count")
        expected_sources = {
            "v5-qwen-governed-trace-collection-v2/attempt-001-t4",
            "v5-qwen-negative-case-expansion-v1/attempt-001-t4",
        }
        if set(self.source_archives) != expected_sources:
            raise ValueError("candidate artifact must retain the frozen fit-pool sources")
        expected_lower = 0.0
        last_probability = 0.0
        for block in self.calibrator_blocks:
            if not isclose(block.lower_bound, expected_lower, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError("calibrator blocks must be contiguous")
            if block.calibrated_probability < last_probability:
                raise ValueError("calibrator blocks must be monotonic")
            expected_lower = block.upper_bound
            last_probability = block.calibrated_probability
        if expected_lower < 1.0:
            raise ValueError("calibrator blocks must cover the full unit interval")
        return self


class HoldoutReplayProtocol(StrictModel):
    protocol_id: Literal["candidate-calibrator-independent-holdout-promotion-protocol-v1"]
    expected_calibrator_artifact_sha256: Literal[
        "e799e4c1e5db8798120b73e0c7e33b86e0f4f220b6360ad010cd0a5feb55ec36"
    ]
    expected_holdout_collection_id: Literal["v5-qwen-candidate-calibrator-independent-holdout-v1"]
    expected_holdout_attempt_id: Literal["attempt-001-t4"]
    minimum_holdout_record_count: Literal[160]
    minimum_holdout_negative_count: Literal[30]
    minimum_brier_improvement: Literal[0.005]
    minimum_fixed_bin_ece_improvement: Literal[0.01]
    maximum_auroc_degradation: Literal[0.001]
    minimum_threshold_preview_selected_count: Literal[30]
    threshold_preview_values: tuple[float, ...] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_thresholds(self) -> HoldoutReplayProtocol:
        if self.threshold_preview_values != (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
            raise ValueError("threshold previews must match the frozen holdout plan")
        return self


class ProbabilityMetrics(StrictModel):
    brier_score: float = Field(ge=0.0, le=1.0)
    fixed_bin_ece: float = Field(ge=0.0, le=1.0)
    auroc: float = Field(ge=0.0, le=1.0)


class CoverageMetrics(StrictModel):
    record_count: int = Field(gt=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    brier_improvement: float

    @model_validator(mode="after")
    def validate_coverage(self) -> CoverageMetrics:
        if self.positive_count + self.negative_count != self.record_count:
            raise ValueError("coverage counts must sum to record_count")
        expected = self.raw_brier_score - self.calibrated_brier_score
        if not isclose(self.brier_improvement, expected, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("coverage brier_improvement must match retained metrics")
        return self


class CalibratorBlockReplay(StrictModel):
    lower_bound: float
    upper_bound: float
    calibrated_probability: float = Field(ge=0.0, le=1.0)
    record_count: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    empirical_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float | None = Field(default=None, ge=0.0, le=1.0)


class ThresholdPreview(StrictModel):
    threshold: float = Field(ge=0.0, le=1.0)
    selected_count: int = Field(ge=0)
    match_count: int = Field(ge=0)
    nonmatch_count: int = Field(ge=0)
    selection_rate: float = Field(ge=0.0, le=1.0)
    nonmatch_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    coverage_warning: bool

    @model_validator(mode="after")
    def validate_counts(self) -> ThresholdPreview:
        if self.match_count + self.nonmatch_count != self.selected_count:
            raise ValueError("threshold preview counts must sum to selected_count")
        return self


class HoldoutReplayGateChecks(StrictModel):
    holdout_provenance_complete: bool
    holdout_independence_documented: bool
    manifest_hashes_match: bool
    analysis_replay_ready: bool
    holdout_record_coverage_sufficient: bool
    holdout_negative_coverage_sufficient: bool
    candidate_artifact_integrity_passed: bool
    no_refit_passed: bool
    brier_improvement_passed: bool
    fixed_bin_ece_improvement_passed: bool
    ranking_safety_passed: bool
    threshold_preview_support_passed: bool
    bounded_claims_passed: bool


class IndependentHoldoutReplayReport(StrictModel):
    schema_version: Literal["candidate_calibrator_independent_holdout_replay_report_v1"]
    report_id: Literal["v5-qwen-candidate-calibrator-independent-holdout-replay-v1"]
    run_id: Literal["v5-qwen-candidate-calibrator-independent-holdout-replay-run-001"]
    source_commit: str = Field(min_length=7)
    created_at: str
    protocol: HoldoutReplayProtocol
    calibrator_artifact_id: Literal["v5-qwen-combined-fixed-bin-isotonic-calibrator-v1"]
    calibrator_artifact_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibrator_fit_pool_archive_ids: tuple[str, ...] = Field(min_length=2, max_length=2)
    holdout_trace_archive_id: Literal[
        "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4"
    ]
    holdout_trace_archive_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_analysis_report_id: Literal[
        "v5-qwen-candidate-calibrator-independent-holdout-analysis-v1"
    ]
    holdout_analysis_report_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_record_count: int = Field(gt=0)
    holdout_positive_count: int = Field(ge=0)
    holdout_negative_count: int = Field(ge=0)
    coverage_by_workload: dict[str, CoverageMetrics]
    coverage_by_position: dict[str, CoverageMetrics]
    raw_metrics: ProbabilityMetrics
    calibrated_metrics: ProbabilityMetrics
    brier_delta: float
    fixed_bin_ece_delta: float
    auroc_delta: float
    calibrator_block_replay: tuple[CalibratorBlockReplay, ...]
    threshold_preview: tuple[ThresholdPreview, ...]
    gate_checks: HoldoutReplayGateChecks
    failure_labels: tuple[HoldoutReplayFailureLabel, ...]
    promotion_recommendation: PromotionRecommendation
    holdout_replay_status: Literal["completed_with_ranking_safety_regression"]
    calibrator_promotion_status: Literal["not_authorized_ranking_safety_regression"]
    threshold_promotion_status: Literal["not_authorized"]
    scheduler_promotion_status: Literal["not_authorized"]
    public_release_status: Literal["not_authorized"]
    production_claim_status: Literal["not_authorized"]
    claims_permitted: tuple[str, ...]
    claims_forbidden: tuple[str, ...]
    next_authorized_step: Literal["candidate_calibrator_promotion_closeout_decision"]

    @model_validator(mode="after")
    def validate_report(self) -> IndependentHoldoutReplayReport:
        if self.holdout_positive_count + self.holdout_negative_count != self.holdout_record_count:
            raise ValueError("holdout counts must sum to holdout_record_count")
        expected_deltas = (
            self.raw_metrics.brier_score - self.calibrated_metrics.brier_score,
            self.raw_metrics.fixed_bin_ece - self.calibrated_metrics.fixed_bin_ece,
            self.calibrated_metrics.auroc - self.raw_metrics.auroc,
        )
        for actual, expected, name in zip(
            (self.brier_delta, self.fixed_bin_ece_delta, self.auroc_delta),
            expected_deltas,
            ("brier_delta", "fixed_bin_ece_delta", "auroc_delta"),
            strict=True,
        ):
            if not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"{name} must match retained metrics")
        if self.promotion_recommendation is not PromotionRecommendation.KEEP_DIAGNOSTIC_ONLY:
            raise ValueError("ranking-safety regression must keep the candidate diagnostic-only")
        if self.failure_labels != (HoldoutReplayFailureLabel.RANKING_SAFETY_REGRESSION,):
            raise ValueError("this retained replay must identify only ranking_safety_regression")
        if self.gate_checks.ranking_safety_passed:
            raise ValueError("retained replay cannot pass ranking safety")
        required_true_checks = (
            self.gate_checks.holdout_provenance_complete,
            self.gate_checks.holdout_independence_documented,
            self.gate_checks.manifest_hashes_match,
            self.gate_checks.analysis_replay_ready,
            self.gate_checks.holdout_record_coverage_sufficient,
            self.gate_checks.holdout_negative_coverage_sufficient,
            self.gate_checks.candidate_artifact_integrity_passed,
            self.gate_checks.no_refit_passed,
            self.gate_checks.brier_improvement_passed,
            self.gate_checks.fixed_bin_ece_improvement_passed,
            self.gate_checks.threshold_preview_support_passed,
            self.gate_checks.bounded_claims_passed,
        )
        if not all(required_true_checks):
            raise ValueError("retained replay must pass every gate except ranking safety")
        return self
