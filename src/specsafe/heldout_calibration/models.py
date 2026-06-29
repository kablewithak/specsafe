"""Typed contracts for held-out calibration fitness and promotion evidence."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.calibration import FrozenCalibratorArtifact
from specsafe.contracts import TraceSplit
from specsafe.contracts.models import StrictContract


class HeldOutCalibrationFitnessStatus(StrEnum):
    """Fitness status from the separately governed final-evaluation boundary."""

    PASSES_HELD_OUT_FITNESS = "passes_held_out_fitness"
    INSUFFICIENT_HELD_OUT_DATA = "insufficient_held_out_data"
    CALIBRATOR_REGRESSION = "calibrator_regression"
    NO_MATERIAL_HELD_OUT_IMPROVEMENT = "no_material_held_out_improvement"


class CalibrationPromotionDecision(StrEnum):
    """Decision that controls whether causal adaptive-policy research may begin."""

    PROMOTED_TO_CAUSAL_ADAPTIVE_POLICY_RESEARCH = (
        "promoted_to_causal_adaptive_policy_research"
    )
    NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA = "not_promoted_insufficient_held_out_data"
    NOT_PROMOTED_CALIBRATOR_REGRESSION = "not_promoted_calibrator_regression"
    NOT_PROMOTED_NO_MATERIAL_HELD_OUT_IMPROVEMENT = (
        "not_promoted_no_material_held_out_improvement"
    )


class AdaptivePolicyResearchEligibility(StrEnum):
    """Whether held-out calibration evidence permits the next research boundary."""

    ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH = (
        "eligible_for_causal_adaptive_policy_research"
    )
    BLOCKED_INSUFFICIENT_HELD_OUT_FITNESS = "blocked_insufficient_held_out_fitness"
    BLOCKED_HELD_OUT_CALIBRATION_REGRESSION = "blocked_held_out_calibration_regression"
    BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT = (
        "blocked_no_material_held_out_improvement"
    )


class RuntimeControlEligibility(StrEnum):
    """Hard boundary: this evidence never authorizes a runtime policy directly."""

    NOT_ELIGIBLE_PENDING_ADAPTIVE_POLICY_EVALUATION = (
        "not_eligible_pending_adaptive_policy_evaluation"
    )


class HeldOutFitnessErrorCode(StrEnum):
    """Machine-readable failures for held-out calibration assessment and persistence."""

    INVALID_FIXTURE_SET = "invalid_fixture_set"
    INVALID_CALIBRATOR_ARTIFACT = "invalid_calibrator_artifact"
    ARTIFACT_FIXTURE_MISMATCH = "artifact_fixture_mismatch"
    NO_FINAL_EVALUATION_CASES = "no_final_evaluation_cases"
    INVALID_DESTINATION = "invalid_destination"


class HeldOutCalibrationFitnessProtocol(StrictContract):
    """Predeclared held-out comparison and promotion-gate configuration."""

    protocol_id: str = Field(
        default="heldout-calibration-fitness-v1",
        min_length=1,
        max_length=128,
    )
    assessment_split: Literal[TraceSplit.FINAL_EVALUATION] = TraceSplit.FINAL_EVALUATION
    minimum_observation_count: int = Field(default=4, ge=1)
    diagnostic_bin_count: int = Field(default=4, ge=2, le=20)
    minimum_brier_score_improvement: float = Field(default=0.0, ge=0.0, le=1.0)
    minimum_expected_calibration_error_improvement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )
    require_strict_improvement: Literal[True] = True


class HeldOutCalibrationBin(StrictContract):
    """One fixed-width held-out diagnostic bin for raw or calibrated probabilities."""

    bin_index: int = Field(ge=0)
    lower_probability_bound: float = Field(ge=0.0, le=1.0)
    upper_probability_bound: float = Field(gt=0.0, le=1.0)
    observation_count: int = Field(ge=0)
    mean_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bin_evidence(self) -> HeldOutCalibrationBin:
        """Prevent empty bins from carrying invented diagnostic evidence."""

        if self.lower_probability_bound >= self.upper_probability_bound:
            raise ValueError("held-out bin lower bound must be below upper bound")
        evidence_fields = (
            self.mean_probability,
            self.observed_acceptance_rate,
            self.absolute_calibration_gap,
        )
        if self.observation_count == 0 and any(value is not None for value in evidence_fields):
            raise ValueError("empty held-out bins must not carry diagnostic evidence")
        if self.observation_count > 0 and any(value is None for value in evidence_fields):
            raise ValueError("populated held-out bins require complete diagnostic evidence")
        return self


class ProbabilityFitnessMetrics(StrictContract):
    """Brier, ECE, and fixed-bin evidence for one probability representation."""

    brier_score: float = Field(ge=0.0, le=1.0)
    expected_calibration_error: float = Field(ge=0.0, le=1.0)
    bins: tuple[HeldOutCalibrationBin, ...] = Field(min_length=2)


class HeldOutCalibrationFitnessResult(StrictContract):
    """Immutable final-evaluation calibration report and promotion decision."""

    schema_version: Literal["heldout-calibration-fitness-v1"] = (
        "heldout-calibration-fitness-v1"
    )
    protocol: HeldOutCalibrationFitnessProtocol
    calibrator_artifact: FrozenCalibratorArtifact
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    assessment_split: Literal[TraceSplit.FINAL_EVALUATION] = TraceSplit.FINAL_EVALUATION
    assessment_case_ids: tuple[str, ...] = Field(min_length=1)
    assessment_trace_ids: tuple[str, ...] = Field(min_length=1)
    observation_count: int = Field(ge=1)
    raw_metrics: ProbabilityFitnessMetrics
    calibrated_metrics: ProbabilityFitnessMetrics
    brier_score_improvement: float
    expected_calibration_error_improvement: float
    status: HeldOutCalibrationFitnessStatus
    promotion_decision: CalibrationPromotionDecision
    adaptive_policy_research_eligibility: AdaptivePolicyResearchEligibility
    runtime_control_eligibility: Literal[
        RuntimeControlEligibility.NOT_ELIGIBLE_PENDING_ADAPTIVE_POLICY_EVALUATION
    ] = RuntimeControlEligibility.NOT_ELIGIBLE_PENDING_ADAPTIVE_POLICY_EVALUATION

    @model_validator(mode="after")
    def validate_report_evidence_and_gate(self) -> HeldOutCalibrationFitnessResult:
        """Bind promotion posture to retained final-evaluation evidence."""

        if self.fixture_set_id != self.calibrator_artifact.fixture_set_id:
            raise ValueError("held-out report fixture_set_id must match calibrator artifact")
        if self.fixture_set_version != self.calibrator_artifact.fixture_set_version:
            raise ValueError("held-out report fixture_set_version must match calibrator artifact")
        if len(set(self.assessment_case_ids)) != len(self.assessment_case_ids):
            raise ValueError("assessment_case_ids must not contain duplicates")
        if len(set(self.assessment_trace_ids)) != len(self.assessment_trace_ids):
            raise ValueError("assessment_trace_ids must not contain duplicates")
        for metrics in (self.raw_metrics, self.calibrated_metrics):
            if len(metrics.bins) != self.protocol.diagnostic_bin_count:
                raise ValueError("held-out metric bins must match protocol diagnostic_bin_count")
            if sum(bin_summary.observation_count for bin_summary in metrics.bins) != (
                self.observation_count
            ):
                raise ValueError("held-out metric bin counts must match observation_count")
            expected_indices = tuple(range(self.protocol.diagnostic_bin_count))
            actual_indices = tuple(bin_summary.bin_index for bin_summary in metrics.bins)
            if actual_indices != expected_indices:
                raise ValueError("held-out metric bins must cover each protocol bin index")
        expected_brier_improvement = (
            self.raw_metrics.brier_score - self.calibrated_metrics.brier_score
        )
        expected_ece_improvement = (
            self.raw_metrics.expected_calibration_error
            - self.calibrated_metrics.expected_calibration_error
        )
        if self.brier_score_improvement != expected_brier_improvement:
            raise ValueError("brier_score_improvement must match retained metric values")
        if self.expected_calibration_error_improvement != expected_ece_improvement:
            raise ValueError(
                "expected_calibration_error_improvement must match retained metric values"
            )
        expected_pairs = {
            HeldOutCalibrationFitnessStatus.PASSES_HELD_OUT_FITNESS: (
                CalibrationPromotionDecision.PROMOTED_TO_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
                AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
            ),
            HeldOutCalibrationFitnessStatus.INSUFFICIENT_HELD_OUT_DATA: (
                CalibrationPromotionDecision.NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA,
                AdaptivePolicyResearchEligibility.BLOCKED_INSUFFICIENT_HELD_OUT_FITNESS,
            ),
            HeldOutCalibrationFitnessStatus.CALIBRATOR_REGRESSION: (
                CalibrationPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION,
                AdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION,
            ),
            HeldOutCalibrationFitnessStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT: (
                CalibrationPromotionDecision.NOT_PROMOTED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
                AdaptivePolicyResearchEligibility.BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
            ),
        }
        if expected_pairs[self.status] != (
            self.promotion_decision,
            self.adaptive_policy_research_eligibility,
        ):
            raise ValueError("held-out status must match its promotion decision and eligibility")
        return self
