"""Held-out assessment for the frozen calibration-only temperature-scaling artifact."""

from __future__ import annotations

import json
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts import TraceDataRole, TraceSourceType, TraceSplit
from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_redesign_final_manifest import (
    CalibrationRedesignFinalManifestedFixtureSet,
    load_calibration_redesign_final_evaluation_manifested_fixture_set,
)
from specsafe.traces.logit_temperature_scaling import LogitTemperatureScalingArtifact

_ARTIFACT_ID = "logit-temperature-scaling-v1"
_PROTOCOL_ID = "logit-temperature-scaling-heldout-fitness-v1"
_NUMERIC_TOLERANCE = 1e-12


class HeldOutTemperatureScalingAssessmentViolationCode(StrEnum):
    """Machine-readable reasons a held-out assessment boundary may reject evidence."""

    UNTRUSTED_FINAL_FIXTURE_SET = "untrusted_final_fixture_set"
    UNTRUSTED_CALIBRATION_ARTIFACT = "untrusted_calibration_artifact"
    ARTIFACT_PROVENANCE_MISMATCH = "artifact_provenance_mismatch"
    FINAL_EVALUATION_BOUNDARY_VIOLATION = "final_evaluation_boundary_violation"
    NON_FINITE_CONFIDENCE = "non_finite_confidence"
    ASSESSMENT_SCHEMA_ERROR = "assessment_schema_error"


class HeldOutTemperatureScalingAssessmentError(ValueError):
    """Typed error raised when held-out assessment inputs violate their evidence boundary."""

    def __init__(
        self,
        code: HeldOutTemperatureScalingAssessmentViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class HeldOutTemperatureScalingAssessmentStatus(StrEnum):
    """Terminal state for one frozen-artifact held-out assessment."""

    INSUFFICIENT_HELD_OUT_DATA = "insufficient_held_out_data"
    CALIBRATOR_REGRESSION = "calibrator_regression"
    NO_MATERIAL_HELD_OUT_IMPROVEMENT = "no_material_held_out_improvement"
    PASSES_HELD_OUT_FITNESS = "passes_held_out_fitness"


class HeldOutTemperatureScalingPromotionDecision(StrEnum):
    """Non-runtime promotion result derived from the fixed held-out protocol."""

    NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA = "not_promoted_insufficient_held_out_data"
    NOT_PROMOTED_CALIBRATOR_REGRESSION = "not_promoted_calibrator_regression"
    NOT_PROMOTED_NO_MATERIAL_HELD_OUT_IMPROVEMENT = (
        "not_promoted_no_material_held_out_improvement"
    )
    ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH = (
        "eligible_for_causal_adaptive_policy_research"
    )


class HeldOutTemperatureScalingAdaptivePolicyResearchEligibility(StrEnum):
    """Whether only the next research-design boundary may proceed after assessment."""

    BLOCKED_INSUFFICIENT_HELD_OUT_DATA = "blocked_insufficient_held_out_data"
    BLOCKED_HELD_OUT_CALIBRATION_REGRESSION = "blocked_held_out_calibration_regression"
    BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT = (
        "blocked_no_material_held_out_improvement"
    )
    ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH = (
        "eligible_for_causal_adaptive_policy_research"
    )


class HeldOutTemperatureScalingAssessmentProtocol(StrictContract):
    """Frozen scoring and promotion rules for one final-evaluation assessment."""

    schema_version: Literal["heldout-temperature-scaling-assessment-protocol-v1"]
    protocol_id: Literal["logit-temperature-scaling-heldout-fitness-v1"]
    minimum_observation_count: int = Field(ge=1)
    equal_width_bin_count: int = Field(ge=2, le=100)
    minimum_brier_improvement: float = Field(ge=0.0)
    minimum_expected_calibration_error_improvement: float = Field(ge=0.0)

    @field_validator(
        "minimum_brier_improvement",
        "minimum_expected_calibration_error_improvement",
    )
    @classmethod
    def validate_finite_thresholds(cls, value: float) -> float:
        """Reject non-finite promotion requirements before assessment begins."""

        if not isfinite(value):
            raise ValueError("held-out promotion thresholds must be finite")
        return value


DEFAULT_HELD_OUT_TEMPERATURE_SCALING_ASSESSMENT_PROTOCOL = (
    HeldOutTemperatureScalingAssessmentProtocol(
        schema_version="heldout-temperature-scaling-assessment-protocol-v1",
        protocol_id=_PROTOCOL_ID,
        minimum_observation_count=16,
        equal_width_bin_count=10,
        minimum_brier_improvement=0.0,
        minimum_expected_calibration_error_improvement=0.0,
    )
)


class HeldOutTemperatureScalingCalibrationBin(StrictContract):
    """One fixed equal-width reliability bin without retaining per-observation labels."""

    lower_bound: float = Field(ge=0.0, le=1.0)
    upper_bound: float = Field(ge=0.0, le=1.0)
    observation_count: int = Field(ge=0)
    mean_predicted_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float = Field(ge=0.0)
    weighted_calibration_gap: float = Field(ge=0.0)

    @field_validator(
        "absolute_calibration_gap",
        "weighted_calibration_gap",
    )
    @classmethod
    def validate_finite_gaps(cls, value: float) -> float:
        """Reject non-finite retained calibration diagnostics."""

        if not isfinite(value):
            raise ValueError("calibration-bin gaps must be finite")
        return value

    @model_validator(mode="after")
    def validate_bin_shape(self) -> HeldOutTemperatureScalingCalibrationBin:
        """Require empty and populated bins to retain unambiguous summary fields."""

        if self.lower_bound >= self.upper_bound:
            raise ValueError(
                "calibration-bin lower_bound must be less than upper_bound"
            )
        if self.observation_count == 0:
            if (
                self.mean_predicted_probability is not None
                or self.observed_acceptance_rate is not None
                or self.absolute_calibration_gap != 0.0
                or self.weighted_calibration_gap != 0.0
            ):
                raise ValueError(
                    "empty calibration bins must retain null means and zero gaps"
                )
        elif (
            self.mean_predicted_probability is None
            or self.observed_acceptance_rate is None
        ):
            raise ValueError("populated calibration bins require retained mean values")
        return self


class HeldOutTemperatureScalingMetricSummary(StrictContract):
    """Aggregate error metrics and fixed-bin summaries for one probability representation."""

    brier_score: float = Field(ge=0.0)
    expected_calibration_error: float = Field(ge=0.0)
    bins: tuple[HeldOutTemperatureScalingCalibrationBin, ...] = Field(min_length=2)

    @field_validator("brier_score", "expected_calibration_error")
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        """Reject non-finite probability metrics before report retention."""

        if not isfinite(value):
            raise ValueError("held-out calibration metrics must be finite")
        return value


class HeldOutTemperatureScalingAssessmentResult(StrictContract):
    """Retained post-hoc assessment of an unchanged frozen calibration artifact."""

    schema_version: Literal["heldout-temperature-scaling-assessment-result-v1"]
    protocol: HeldOutTemperatureScalingAssessmentProtocol
    artifact: LogitTemperatureScalingArtifact
    final_evaluation_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evaluation_fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    final_evaluation_fixture_set_version: str = Field(min_length=1, max_length=64)
    assessed_case_ids: tuple[str, ...] = Field(min_length=1)
    assessed_trace_ids: tuple[str, ...] = Field(min_length=1)
    assessed_scenario_family_ids: tuple[str, ...] = Field(min_length=2)
    observation_count: int = Field(gt=0)
    raw_metrics: HeldOutTemperatureScalingMetricSummary
    calibrated_metrics: HeldOutTemperatureScalingMetricSummary
    brier_improvement: float
    expected_calibration_error_improvement: float
    status: HeldOutTemperatureScalingAssessmentStatus
    promotion_decision: HeldOutTemperatureScalingPromotionDecision
    adaptive_policy_research_eligibility: (
        HeldOutTemperatureScalingAdaptivePolicyResearchEligibility
    )
    final_evaluation_accessed: Literal[True]
    artifact_refit: Literal[False]
    artifact_mutated: Literal[False]
    runtime_control_eligibility: Literal[
        "not_eligible_pending_adaptive_policy_evaluation"
    ]

    @field_validator(
        "brier_improvement",
        "expected_calibration_error_improvement",
    )
    @classmethod
    def validate_finite_improvements(cls, value: float) -> float:
        """Reject non-finite signed improvement values before assessment retention."""

        if not isfinite(value):
            raise ValueError("held-out signed improvement values must be finite")
        return value

    @model_validator(mode="after")
    def validate_result_alignment(self) -> HeldOutTemperatureScalingAssessmentResult:
        """Keep status, decision, retained metrics, and artifact boundary coherent."""

        if self.artifact.final_evaluation_accessed is not False:
            raise ValueError("the retained artifact must remain calibration-only")
        if self.artifact.runtime_control_eligible is not False:
            raise ValueError(
                "the retained artifact must remain runtime-control ineligible"
            )
        if self.artifact_refit is not False or self.artifact_mutated is not False:
            raise ValueError(
                "held-out assessment must not refit or mutate the frozen artifact"
            )
        if len(set(self.assessed_case_ids)) != len(self.assessed_case_ids):
            raise ValueError("assessed_case_ids must be unique")
        if len(set(self.assessed_trace_ids)) != len(self.assessed_trace_ids):
            raise ValueError("assessed_trace_ids must be unique")
        if len(set(self.assessed_scenario_family_ids)) != len(
            self.assessed_scenario_family_ids
        ):
            raise ValueError("assessed_scenario_family_ids must be unique")
        if len(self.raw_metrics.bins) != self.protocol.equal_width_bin_count:
            raise ValueError("raw metrics must use the protocol fixed bin count")
        if len(self.calibrated_metrics.bins) != self.protocol.equal_width_bin_count:
            raise ValueError("calibrated metrics must use the protocol fixed bin count")
        expected_brier_improvement = (
            self.raw_metrics.brier_score - self.calibrated_metrics.brier_score
        )
        expected_ece_improvement = (
            self.raw_metrics.expected_calibration_error
            - self.calibrated_metrics.expected_calibration_error
        )
        if (
            abs(self.brier_improvement - expected_brier_improvement)
            > _NUMERIC_TOLERANCE
        ):
            raise ValueError(
                "brier_improvement must equal raw minus calibrated Brier score"
            )
        if (
            abs(self.expected_calibration_error_improvement - expected_ece_improvement)
            > _NUMERIC_TOLERANCE
        ):
            raise ValueError(
                "expected_calibration_error_improvement must equal raw minus calibrated ECE"
            )
        expected_decision, expected_eligibility = _decision_for_status(self.status)
        if self.promotion_decision is not expected_decision:
            raise ValueError("promotion decision must match the assessment status")
        if self.adaptive_policy_research_eligibility is not expected_eligibility:
            raise ValueError(
                "adaptive-policy eligibility must match the assessment status"
            )
        return self


def assess_logit_temperature_scaling_heldout(
    fixture_set: CalibrationRedesignFinalManifestedFixtureSet,
    artifact: LogitTemperatureScalingArtifact,
    protocol: HeldOutTemperatureScalingAssessmentProtocol = (
        DEFAULT_HELD_OUT_TEMPERATURE_SCALING_ASSESSMENT_PROTOCOL
    ),
) -> HeldOutTemperatureScalingAssessmentResult:
    """Assess one frozen calibration artifact against verified quarantined final evidence."""

    _validate_assessment_inputs(fixture_set, artifact, protocol)
    raw_probabilities, labels = _extract_final_evaluation_samples(fixture_set)
    calibrated_probabilities = tuple(
        artifact.calibrate(value) for value in raw_probabilities
    )
    raw_metrics = _build_metric_summary(
        raw_probabilities,
        labels,
        protocol.equal_width_bin_count,
    )
    calibrated_metrics = _build_metric_summary(
        calibrated_probabilities,
        labels,
        protocol.equal_width_bin_count,
    )
    brier_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    expected_calibration_error_improvement = (
        raw_metrics.expected_calibration_error
        - calibrated_metrics.expected_calibration_error
    )
    status = _assess_status(
        observation_count=len(labels),
        brier_improvement=brier_improvement,
        expected_calibration_error_improvement=expected_calibration_error_improvement,
        protocol=protocol,
    )
    promotion_decision, adaptive_policy_research_eligibility = _decision_for_status(
        status
    )
    manifest = fixture_set.manifest
    cases = tuple(
        sorted(fixture_set.cases, key=lambda case: case.runtime_input.case_id)
    )
    return HeldOutTemperatureScalingAssessmentResult(
        schema_version="heldout-temperature-scaling-assessment-result-v1",
        protocol=protocol,
        artifact=artifact,
        final_evaluation_manifest_aggregate_sha256=manifest.aggregate_sha256,
        final_evaluation_fixture_set_id=manifest.fixture_set_id,
        final_evaluation_fixture_set_version=manifest.fixture_set_version,
        assessed_case_ids=tuple(case.runtime_input.case_id for case in cases),
        assessed_trace_ids=tuple(case.runtime_input.trace_id for case in cases),
        assessed_scenario_family_ids=tuple(
            sorted({case.runtime_input.scenario_family_id for case in cases})
        ),
        observation_count=len(labels),
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        brier_improvement=brier_improvement,
        expected_calibration_error_improvement=expected_calibration_error_improvement,
        status=status,
        promotion_decision=promotion_decision,
        adaptive_policy_research_eligibility=adaptive_policy_research_eligibility,
        final_evaluation_accessed=True,
        artifact_refit=False,
        artifact_mutated=False,
        runtime_control_eligibility="not_eligible_pending_adaptive_policy_evaluation",
    )


def load_logit_temperature_scaling_artifact(
    artifact_path: Path,
) -> LogitTemperatureScalingArtifact:
    """Load a frozen calibration-only artifact without a permissive fallback path."""

    try:
        payload: Any = json.loads(artifact_path.read_bytes())
    except OSError as error:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.UNTRUSTED_CALIBRATION_ARTIFACT,
            f"unable to read frozen calibration artifact: {artifact_path}",
        ) from error
    except json.JSONDecodeError as error:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            f"invalid JSON in frozen calibration artifact: {error.msg}",
        ) from error
    try:
        return LogitTemperatureScalingArtifact.model_validate(payload)
    except ValidationError as error:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            f"frozen calibration artifact schema validation failed: {error}",
        ) from error


def write_logit_temperature_scaling_heldout_assessment(
    fixture_root: Path,
    artifact_path: Path,
    output_path: Path,
    protocol: HeldOutTemperatureScalingAssessmentProtocol = (
        DEFAULT_HELD_OUT_TEMPERATURE_SCALING_ASSESSMENT_PROTOCOL
    ),
) -> HeldOutTemperatureScalingAssessmentResult:
    """Write a retained held-out report without changing final fixtures or the artifact."""

    fixture_set = load_calibration_redesign_final_evaluation_manifested_fixture_set(
        fixture_root
    )
    artifact = load_logit_temperature_scaling_artifact(artifact_path)
    result = assess_logit_temperature_scaling_heldout(fixture_set, artifact, protocol)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        (
            json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=False) + "\n"
        ).encode("utf-8")
    )
    return result


def _validate_assessment_inputs(
    fixture_set: CalibrationRedesignFinalManifestedFixtureSet,
    artifact: LogitTemperatureScalingArtifact,
    protocol: HeldOutTemperatureScalingAssessmentProtocol,
) -> None:
    """Recheck final-quarantine and frozen-artifact invariants before labels are read."""

    if type(fixture_set) is not CalibrationRedesignFinalManifestedFixtureSet:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.UNTRUSTED_FINAL_FIXTURE_SET,
            "held-out assessment requires an exact verified final manifested fixture-set type",
        )
    if type(artifact) is not LogitTemperatureScalingArtifact:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.UNTRUSTED_CALIBRATION_ARTIFACT,
            "held-out assessment requires an exact frozen temperature-scaling artifact type",
        )
    if type(protocol) is not HeldOutTemperatureScalingAssessmentProtocol:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            "held-out assessment requires an exact frozen assessment protocol type",
        )
    manifest = fixture_set.manifest
    if (
        artifact.artifact_id != _ARTIFACT_ID
        or artifact.fixture_set_id != manifest.fixture_set_id
        or artifact.fixture_set_version != manifest.fixture_set_version
        or artifact.source_type is not TraceSourceType.SYNTHETIC
        or artifact.fit_split is not TraceSplit.CALIBRATION
        or artifact.fit_data_role is not TraceDataRole.CALIBRATION
    ):
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen calibration artifact does not match the governed fixture-set identity",
        )
    if (
        artifact.final_evaluation_accessed is not False
        or artifact.runtime_control_eligible is not False
    ):
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen calibration artifact must remain calibration-only and runtime-ineligible",
        )
    final_case_ids: set[str] = set()
    for replay_case in fixture_set.cases:
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes
        if (
            runtime.split is not TraceSplit.FINAL_EVALUATION
            or outcomes.split is not TraceSplit.FINAL_EVALUATION
            or runtime.data_role is not TraceDataRole.HELD_OUT_EVALUATION
            or outcomes.data_role is not TraceDataRole.HELD_OUT_EVALUATION
            or runtime.source_type is not TraceSourceType.SYNTHETIC
            or outcomes.source_type is not TraceSourceType.SYNTHETIC
        ):
            raise HeldOutTemperatureScalingAssessmentError(
                HeldOutTemperatureScalingAssessmentViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
                (
                    "held-out assessment may consume only synthetic quarantined "
                    "final-evaluation evidence"
                ),
            )
        final_case_ids.add(runtime.case_id)
    if final_case_ids & set(artifact.fitted_case_ids):
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen artifact fitted-case inventory must be disjoint from final-evaluation cases",
        )


def _extract_final_evaluation_samples(
    fixture_set: CalibrationRedesignFinalManifestedFixtureSet,
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Join visible confidence with post-hoc acceptance only after boundary validation."""

    probabilities: list[float] = []
    labels: list[int] = []
    for replay_case in sorted(
        fixture_set.cases,
        key=lambda case: case.runtime_input.case_id,
    ):
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in replay_case.runtime_input.contexts
        }
        for outcome in replay_case.expected_outcomes.outcomes:
            context = contexts_by_key[
                (outcome.decode_round, outcome.block_position_index)
            ]
            confidence = context.conditional_survival_confidence
            if not isfinite(confidence):
                raise HeldOutTemperatureScalingAssessmentError(
                    HeldOutTemperatureScalingAssessmentViolationCode.NON_FINITE_CONFIDENCE,
                    "final-evaluation confidence must be finite",
                )
            probabilities.append(confidence)
            labels.append(int(outcome.observed_acceptance))
    return tuple(probabilities), tuple(labels)


def _build_metric_summary(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
    bin_count: int,
) -> HeldOutTemperatureScalingMetricSummary:
    """Calculate Brier score and fixed-bin ECE without retaining individual outcomes."""

    if len(probabilities) != len(labels) or not probabilities:
        raise HeldOutTemperatureScalingAssessmentError(
            HeldOutTemperatureScalingAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            "held-out probability and label arrays must be non-empty and aligned",
        )
    observation_count = len(probabilities)
    brier_score = (
        sum(
            (probability - label) ** 2
            for probability, label in zip(probabilities, labels, strict=True)
        )
        / observation_count
    )
    bins: list[HeldOutTemperatureScalingCalibrationBin] = []
    expected_calibration_error = 0.0
    for index in range(bin_count):
        lower_bound = index / bin_count
        upper_bound = (index + 1) / bin_count
        selected_indices = [
            position
            for position, probability in enumerate(probabilities)
            if lower_bound <= probability < upper_bound
            or (index == bin_count - 1 and lower_bound <= probability <= upper_bound)
        ]
        if not selected_indices:
            bins.append(
                HeldOutTemperatureScalingCalibrationBin(
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    observation_count=0,
                    mean_predicted_probability=None,
                    observed_acceptance_rate=None,
                    absolute_calibration_gap=0.0,
                    weighted_calibration_gap=0.0,
                )
            )
            continue
        mean_predicted_probability = sum(
            probabilities[position] for position in selected_indices
        ) / len(selected_indices)
        observed_acceptance_rate = sum(
            labels[position] for position in selected_indices
        ) / len(selected_indices)
        absolute_calibration_gap = abs(
            mean_predicted_probability - observed_acceptance_rate
        )
        weighted_calibration_gap = (
            len(selected_indices) / observation_count * absolute_calibration_gap
        )
        expected_calibration_error += weighted_calibration_gap
        bins.append(
            HeldOutTemperatureScalingCalibrationBin(
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                observation_count=len(selected_indices),
                mean_predicted_probability=mean_predicted_probability,
                observed_acceptance_rate=observed_acceptance_rate,
                absolute_calibration_gap=absolute_calibration_gap,
                weighted_calibration_gap=weighted_calibration_gap,
            )
        )
    return HeldOutTemperatureScalingMetricSummary(
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        bins=tuple(bins),
    )


def _assess_status(
    observation_count: int,
    brier_improvement: float,
    expected_calibration_error_improvement: float,
    protocol: HeldOutTemperatureScalingAssessmentProtocol,
) -> HeldOutTemperatureScalingAssessmentStatus:
    """Apply the frozen gate without altering the artifact or the final evidence."""

    if observation_count < protocol.minimum_observation_count:
        return HeldOutTemperatureScalingAssessmentStatus.INSUFFICIENT_HELD_OUT_DATA
    if (
        brier_improvement < -_NUMERIC_TOLERANCE
        or expected_calibration_error_improvement < -_NUMERIC_TOLERANCE
    ):
        return HeldOutTemperatureScalingAssessmentStatus.CALIBRATOR_REGRESSION
    if (
        brier_improvement <= protocol.minimum_brier_improvement + _NUMERIC_TOLERANCE
        or expected_calibration_error_improvement
        <= protocol.minimum_expected_calibration_error_improvement + _NUMERIC_TOLERANCE
    ):
        return (
            HeldOutTemperatureScalingAssessmentStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT
        )
    return HeldOutTemperatureScalingAssessmentStatus.PASSES_HELD_OUT_FITNESS


def _decision_for_status(
    status: HeldOutTemperatureScalingAssessmentStatus,
) -> tuple[
    HeldOutTemperatureScalingPromotionDecision,
    HeldOutTemperatureScalingAdaptivePolicyResearchEligibility,
]:
    """Map the assessment state to its exact non-runtime decision and next-step posture."""

    outcomes = {
        HeldOutTemperatureScalingAssessmentStatus.INSUFFICIENT_HELD_OUT_DATA: (
            HeldOutTemperatureScalingPromotionDecision.NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA,
            HeldOutTemperatureScalingAdaptivePolicyResearchEligibility.BLOCKED_INSUFFICIENT_HELD_OUT_DATA,
        ),
        HeldOutTemperatureScalingAssessmentStatus.CALIBRATOR_REGRESSION: (
            HeldOutTemperatureScalingPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION,
            HeldOutTemperatureScalingAdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION,
        ),
        HeldOutTemperatureScalingAssessmentStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT: (
            HeldOutTemperatureScalingPromotionDecision.NOT_PROMOTED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
            HeldOutTemperatureScalingAdaptivePolicyResearchEligibility.BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
        ),
        HeldOutTemperatureScalingAssessmentStatus.PASSES_HELD_OUT_FITNESS: (
            HeldOutTemperatureScalingPromotionDecision.ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
            HeldOutTemperatureScalingAdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
        ),
    }
    return outcomes[status]
