"""Read-only held-out assessment for the frozen V2 bounded-Platt artifact.

This module scores one frozen calibration artifact against only the verified V2
final-evaluation manifest. It cannot refit the artifact, change fixture bytes, or
produce a scheduler decision.
"""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts.models import StrictContract, TraceDataRole, TraceSourceType, TraceSplit
from specsafe.traces.bounded_platt_scaling import BoundedPlattScalingArtifact
from specsafe.traces.calibration_redesign_v2_final_manifest import (
    CalibrationRedesignV2FinalManifestedFixtureSet,
    load_calibration_redesign_v2_final_evaluation_manifested_fixture_set,
)

_ARTIFACT_ID = "bounded-platt-scaling-v1"
_PROTOCOL_ID = "bounded-platt-scaling-heldout-fitness-v1"
_NUMERIC_TOLERANCE = 1e-12


class BoundedPlattHeldOutAssessmentViolationCode(StrEnum):
    """Machine-readable reasons the V2 held-out assessment may be rejected."""

    UNTRUSTED_FINAL_FIXTURE_SET = "untrusted_final_fixture_set"
    UNTRUSTED_CALIBRATION_ARTIFACT = "untrusted_calibration_artifact"
    ARTIFACT_PROVENANCE_MISMATCH = "artifact_provenance_mismatch"
    FINAL_EVALUATION_BOUNDARY_VIOLATION = "final_evaluation_boundary_violation"
    NON_FINITE_CONFIDENCE = "non_finite_confidence"
    ASSESSMENT_SCHEMA_ERROR = "assessment_schema_error"


class BoundedPlattHeldOutAssessmentError(ValueError):
    """Typed error raised when the held-out evidence boundary is violated."""

    def __init__(self, code: BoundedPlattHeldOutAssessmentViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class BoundedPlattHeldOutAssessmentStatus(StrEnum):
    """Terminal status for the one frozen-artifact V2 held-out assessment."""

    INSUFFICIENT_HELD_OUT_DATA = "insufficient_held_out_data"
    CALIBRATOR_REGRESSION = "calibrator_regression"
    CALIBRATOR_NO_STRICT_IMPROVEMENT = "calibrator_no_strict_improvement"
    PASSES_HELD_OUT_FITNESS = "passes_held_out_fitness"


class BoundedPlattHeldOutPromotionDecision(StrEnum):
    """Non-runtime decision produced by the fixed V2 held-out gate."""

    NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA = "not_promoted_insufficient_final_evidence"
    NOT_PROMOTED_CALIBRATOR_REGRESSION = "not_promoted_calibrator_regression"
    NOT_PROMOTED_NO_STRICT_IMPROVEMENT = "not_promoted_no_strict_improvement"
    ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH = "eligible_for_causal_adaptive_policy_research"


class BoundedPlattAdaptivePolicyResearchEligibility(StrEnum):
    """Whether only later scheduler research design may proceed after this assessment."""

    BLOCKED_INSUFFICIENT_HELD_OUT_DATA = "blocked_insufficient_final_evidence"
    BLOCKED_HELD_OUT_CALIBRATION_REGRESSION = "blocked_held_out_calibration_regression"
    BLOCKED_NO_STRICT_IMPROVEMENT = "blocked_no_strict_improvement"
    ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH = "eligible_for_causal_adaptive_policy_research"


class BoundedPlattConfidenceOrderingStatus(StrEnum):
    """Whether the frozen positive-slope transform preserves confidence order."""

    PRESERVED = "preserved"
    VIOLATED = "violated"


class BoundedPlattHeldOutAssessmentProtocol(StrictContract):
    """Predeclared V2 scoring and promotion rules for one read-only assessment."""

    schema_version: Literal["bounded-platt-scaling-heldout-assessment-protocol-v1"]
    protocol_id: Literal["bounded-platt-scaling-heldout-fitness-v1"]
    minimum_observation_count: int = Field(ge=1)
    equal_width_bin_count: int = Field(ge=2, le=100)
    require_strict_brier_improvement: Literal[True]
    require_strict_expected_calibration_error_improvement: Literal[True]
    require_monotonic_transform: Literal[True]
    require_complete_artifact_provenance: Literal[True]
    require_complete_manifest_provenance: Literal[True]
    require_no_split_leakage: Literal[True]
    require_complete_report_provenance: Literal[True]


DEFAULT_BOUNDED_PLATT_HELD_OUT_ASSESSMENT_PROTOCOL = BoundedPlattHeldOutAssessmentProtocol(
    schema_version="bounded-platt-scaling-heldout-assessment-protocol-v1",
    protocol_id=_PROTOCOL_ID,
    minimum_observation_count=30,
    equal_width_bin_count=10,
    require_strict_brier_improvement=True,
    require_strict_expected_calibration_error_improvement=True,
    require_monotonic_transform=True,
    require_complete_artifact_provenance=True,
    require_complete_manifest_provenance=True,
    require_no_split_leakage=True,
    require_complete_report_provenance=True,
)


class BoundedPlattHeldOutCalibrationBin(StrictContract):
    """One fixed reliability bin without retaining individual held-out labels."""

    lower_bound: float = Field(ge=0.0, le=1.0)
    upper_bound: float = Field(ge=0.0, le=1.0)
    observation_count: int = Field(ge=0)
    mean_predicted_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float = Field(ge=0.0)
    weighted_calibration_gap: float = Field(ge=0.0)

    @field_validator("absolute_calibration_gap", "weighted_calibration_gap")
    @classmethod
    def validate_finite_gaps(cls, value: float) -> float:
        """Reject non-finite retained diagnostics."""

        if not isfinite(value):
            raise ValueError("held-out calibration-bin gaps must be finite")
        return value

    @model_validator(mode="after")
    def validate_bin_shape(self) -> BoundedPlattHeldOutCalibrationBin:
        """Keep empty and populated bins unambiguous in the retained report."""

        if self.lower_bound >= self.upper_bound:
            raise ValueError("calibration-bin lower_bound must be less than upper_bound")
        if self.observation_count == 0:
            if (
                self.mean_predicted_probability is not None
                or self.observed_acceptance_rate is not None
                or self.absolute_calibration_gap != 0.0
                or self.weighted_calibration_gap != 0.0
            ):
                raise ValueError("empty calibration bins must retain null means and zero gaps")
        elif self.mean_predicted_probability is None or self.observed_acceptance_rate is None:
            raise ValueError("populated calibration bins require retained mean values")
        return self


class BoundedPlattHeldOutMetricSummary(StrictContract):
    """Aggregate held-out probability metrics using one fixed bin configuration."""

    brier_score: float = Field(ge=0.0)
    expected_calibration_error: float = Field(ge=0.0)
    bins: tuple[BoundedPlattHeldOutCalibrationBin, ...] = Field(min_length=2)

    @field_validator("brier_score", "expected_calibration_error")
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        """Reject non-finite retained metrics."""

        if not isfinite(value):
            raise ValueError("held-out probability metrics must be finite")
        return value


class BoundedPlattHeldOutAssessmentResult(StrictContract):
    """Retained read-only assessment of one unchanged V2 calibration artifact."""

    schema_version: Literal["bounded-platt-scaling-heldout-assessment-result-v1"]
    protocol: BoundedPlattHeldOutAssessmentProtocol
    artifact: BoundedPlattScalingArtifact
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_byte_count: int = Field(gt=0)
    final_evaluation_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evaluation_fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    final_evaluation_fixture_set_version: Literal["1.0.0"]
    assessed_case_ids: tuple[str, ...] = Field(min_length=1)
    assessed_trace_ids: tuple[str, ...] = Field(min_length=1)
    assessed_scenario_family_ids: tuple[str, ...] = Field(min_length=1)
    observation_count: int = Field(gt=0)
    raw_metrics: BoundedPlattHeldOutMetricSummary
    calibrated_metrics: BoundedPlattHeldOutMetricSummary
    brier_improvement: float
    expected_calibration_error_improvement: float
    confidence_ordering_status: BoundedPlattConfidenceOrderingStatus
    artifact_provenance_complete: Literal[True]
    manifest_provenance_complete: Literal[True]
    no_split_leakage: Literal[True]
    report_provenance_complete: Literal[True]
    status: BoundedPlattHeldOutAssessmentStatus
    promotion_decision: BoundedPlattHeldOutPromotionDecision
    adaptive_policy_research_eligibility: BoundedPlattAdaptivePolicyResearchEligibility
    final_evaluation_accessed: Literal[True]
    artifact_refit: Literal[False]
    artifact_mutated: Literal[False]
    assessment_attempt_count: Literal[1]
    runtime_control_eligibility: Literal["not_eligible_pending_adaptive_policy_evaluation"]

    @field_validator("brier_improvement", "expected_calibration_error_improvement")
    @classmethod
    def validate_finite_improvements(cls, value: float) -> float:
        """Reject non-finite signed changes before report retention."""

        if not isfinite(value):
            raise ValueError("held-out metric improvements must be finite")
        return value

    @model_validator(mode="after")
    def validate_result_alignment(self) -> BoundedPlattHeldOutAssessmentResult:
        """Keep status, decisions, provenance, and frozen-artifact boundaries aligned."""

        if self.artifact.final_evaluation_accessed is not False:
            raise ValueError("retained artifact must remain calibration-only")
        if self.artifact.runtime_control_eligible is not False:
            raise ValueError("retained artifact must remain runtime-control ineligible")
        if self.artifact_refit is not False or self.artifact_mutated is not False:
            raise ValueError("held-out assessment must not refit or mutate the artifact")
        if len(set(self.assessed_case_ids)) != len(self.assessed_case_ids):
            raise ValueError("assessed_case_ids must be unique")
        if len(set(self.assessed_trace_ids)) != len(self.assessed_trace_ids):
            raise ValueError("assessed_trace_ids must be unique")
        if len(set(self.assessed_scenario_family_ids)) != len(self.assessed_scenario_family_ids):
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
        if abs(self.brier_improvement - expected_brier_improvement) > _NUMERIC_TOLERANCE:
            raise ValueError("brier_improvement must equal raw minus calibrated Brier score")
        if (
            abs(self.expected_calibration_error_improvement - expected_ece_improvement)
            > _NUMERIC_TOLERANCE
        ):
            raise ValueError(
                "expected_calibration_error_improvement must equal raw minus calibrated ECE"
            )
        if self.confidence_ordering_status is not BoundedPlattConfidenceOrderingStatus.PRESERVED:
            raise ValueError("a positive-slope bounded-Platt artifact must preserve ordering")
        expected_decision, expected_eligibility = _decision_for_status(self.status)
        if self.promotion_decision is not expected_decision:
            raise ValueError("promotion decision must match assessment status")
        if self.adaptive_policy_research_eligibility is not expected_eligibility:
            raise ValueError("adaptive-policy eligibility must match assessment status")
        return self


def assess_bounded_platt_scaling_heldout(
    fixture_set: CalibrationRedesignV2FinalManifestedFixtureSet,
    artifact: BoundedPlattScalingArtifact,
    *,
    artifact_sha256: str,
    artifact_byte_count: int,
    protocol: BoundedPlattHeldOutAssessmentProtocol = (
        DEFAULT_BOUNDED_PLATT_HELD_OUT_ASSESSMENT_PROTOCOL
    ),
) -> BoundedPlattHeldOutAssessmentResult:
    """Assess one frozen V2 artifact against the verified final corpus exactly once."""

    _validate_assessment_inputs(
        fixture_set, artifact, artifact_sha256, artifact_byte_count, protocol
    )
    raw_probabilities, labels = _extract_final_evaluation_samples(fixture_set)
    calibrated_probabilities = tuple(artifact.calibrate(value) for value in raw_probabilities)
    raw_metrics = _build_metric_summary(raw_probabilities, labels, protocol.equal_width_bin_count)
    calibrated_metrics = _build_metric_summary(
        calibrated_probabilities,
        labels,
        protocol.equal_width_bin_count,
    )
    brier_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    expected_calibration_error_improvement = (
        raw_metrics.expected_calibration_error - calibrated_metrics.expected_calibration_error
    )
    confidence_ordering_status = _confidence_ordering_status(artifact)
    status = _assess_status(
        observation_count=len(labels),
        brier_improvement=brier_improvement,
        expected_calibration_error_improvement=expected_calibration_error_improvement,
        confidence_ordering_status=confidence_ordering_status,
        protocol=protocol,
    )
    promotion_decision, adaptive_policy_research_eligibility = _decision_for_status(status)
    manifest = fixture_set.manifest
    cases = tuple(sorted(fixture_set.cases, key=lambda item: item.runtime_input.case_id))
    return BoundedPlattHeldOutAssessmentResult(
        schema_version="bounded-platt-scaling-heldout-assessment-result-v1",
        protocol=protocol,
        artifact=artifact,
        artifact_sha256=artifact_sha256,
        artifact_byte_count=artifact_byte_count,
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
        confidence_ordering_status=confidence_ordering_status,
        artifact_provenance_complete=True,
        manifest_provenance_complete=True,
        no_split_leakage=True,
        report_provenance_complete=True,
        status=status,
        promotion_decision=promotion_decision,
        adaptive_policy_research_eligibility=adaptive_policy_research_eligibility,
        final_evaluation_accessed=True,
        artifact_refit=False,
        artifact_mutated=False,
        assessment_attempt_count=1,
        runtime_control_eligibility="not_eligible_pending_adaptive_policy_evaluation",
    )


def load_bounded_platt_scaling_artifact(
    artifact_path: Path,
) -> tuple[BoundedPlattScalingArtifact, str, int]:
    """Load one frozen artifact and retain byte-level provenance for the assessment report."""

    try:
        artifact_bytes = artifact_path.read_bytes()
    except OSError as error:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.UNTRUSTED_CALIBRATION_ARTIFACT,
            f"unable to read frozen bounded-Platt artifact: {artifact_path}",
        ) from error
    try:
        payload: Any = json.loads(artifact_bytes)
    except json.JSONDecodeError as error:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            f"invalid JSON in frozen bounded-Platt artifact: {error.msg}",
        ) from error
    try:
        artifact = BoundedPlattScalingArtifact.model_validate(payload)
    except ValidationError as error:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            f"frozen bounded-Platt artifact schema validation failed: {error}",
        ) from error
    return artifact, sha256(artifact_bytes).hexdigest(), len(artifact_bytes)


def write_bounded_platt_scaling_heldout_assessment(
    fixture_root: Path,
    artifact_path: Path,
    output_path: Path,
    *,
    protocol: BoundedPlattHeldOutAssessmentProtocol = (
        DEFAULT_BOUNDED_PLATT_HELD_OUT_ASSESSMENT_PROTOCOL
    ),
) -> BoundedPlattHeldOutAssessmentResult:
    """Write one deterministic held-out result without modifying artifact or fixture inputs."""

    fixture_set = load_calibration_redesign_v2_final_evaluation_manifested_fixture_set(fixture_root)
    artifact, artifact_sha256, artifact_byte_count = load_bounded_platt_scaling_artifact(
        artifact_path
    )
    result = assess_bounded_platt_scaling_heldout(
        fixture_set,
        artifact,
        artifact_sha256=artifact_sha256,
        artifact_byte_count=artifact_byte_count,
        protocol=protocol,
    )
    if output_path.suffix != ".json":
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            "held-out assessment destination must be a JSON file",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_pretty_json_bytes(result.model_dump(mode="json")))
    return result


def _validate_assessment_inputs(
    fixture_set: CalibrationRedesignV2FinalManifestedFixtureSet,
    artifact: BoundedPlattScalingArtifact,
    artifact_sha256: str,
    artifact_byte_count: int,
    protocol: BoundedPlattHeldOutAssessmentProtocol,
) -> None:
    """Reject unverified evidence before final outcomes are joined for scoring."""

    if type(fixture_set) is not CalibrationRedesignV2FinalManifestedFixtureSet:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.UNTRUSTED_FINAL_FIXTURE_SET,
            "held-out assessment requires an exact verified V2 final manifested fixture set",
        )
    if type(artifact) is not BoundedPlattScalingArtifact:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.UNTRUSTED_CALIBRATION_ARTIFACT,
            "held-out assessment requires an exact frozen bounded-Platt artifact type",
        )
    if type(protocol) is not BoundedPlattHeldOutAssessmentProtocol:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            "held-out assessment requires the frozen typed assessment protocol",
        )
    if len(artifact_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in artifact_sha256
    ):
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen bounded-Platt artifact hash must be a SHA-256 digest",
        )
    if artifact_byte_count <= 0:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen bounded-Platt artifact byte count must be positive",
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
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen bounded-Platt artifact does not match V2 fixture-set identity",
        )
    if (
        artifact.final_evaluation_accessed is not False
        or artifact.runtime_control_eligible is not False
    ):
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen bounded-Platt artifact must remain calibration-only and runtime-ineligible",
        )
    if artifact.slope <= 0.0:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "bounded-Platt artifact must retain a positive global slope",
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
            raise BoundedPlattHeldOutAssessmentError(
                BoundedPlattHeldOutAssessmentViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
                "held-out assessment may consume only quarantined V2 final-evaluation evidence",
            )
        final_case_ids.add(runtime.case_id)
    if final_case_ids & set(artifact.fit_case_ids):
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH,
            "frozen artifact fit cases must be disjoint from V2 held-out case IDs",
        )


def _extract_final_evaluation_samples(
    fixture_set: CalibrationRedesignV2FinalManifestedFixtureSet,
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Join runtime confidence with post-hoc labels only after boundary validation."""

    probabilities: list[float] = []
    labels: list[int] = []
    for replay_case in sorted(fixture_set.cases, key=lambda item: item.runtime_input.case_id):
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in replay_case.runtime_input.contexts
        }
        for outcome in replay_case.expected_outcomes.outcomes:
            context = contexts_by_key[(outcome.decode_round, outcome.block_position_index)]
            confidence = context.conditional_survival_confidence
            if not isfinite(confidence):
                raise BoundedPlattHeldOutAssessmentError(
                    BoundedPlattHeldOutAssessmentViolationCode.NON_FINITE_CONFIDENCE,
                    "V2 final-evaluation confidence must be finite",
                )
            probabilities.append(confidence)
            labels.append(int(outcome.observed_acceptance))
    return tuple(probabilities), tuple(labels)


def _build_metric_summary(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
    bin_count: int,
) -> BoundedPlattHeldOutMetricSummary:
    """Calculate Brier score and fixed-bin ECE without retaining individual labels."""

    if len(probabilities) != len(labels) or not probabilities:
        raise BoundedPlattHeldOutAssessmentError(
            BoundedPlattHeldOutAssessmentViolationCode.ASSESSMENT_SCHEMA_ERROR,
            "held-out probabilities and labels must be non-empty and aligned",
        )
    observation_count = len(probabilities)
    brier_score = (
        sum(
            (probability - label) ** 2
            for probability, label in zip(probabilities, labels, strict=True)
        )
        / observation_count
    )
    bins: list[BoundedPlattHeldOutCalibrationBin] = []
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
                BoundedPlattHeldOutCalibrationBin(
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
        observed_acceptance_rate = sum(labels[position] for position in selected_indices) / len(
            selected_indices
        )
        absolute_calibration_gap = abs(mean_predicted_probability - observed_acceptance_rate)
        weighted_calibration_gap = (
            len(selected_indices) / observation_count * absolute_calibration_gap
        )
        expected_calibration_error += weighted_calibration_gap
        bins.append(
            BoundedPlattHeldOutCalibrationBin(
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                observation_count=len(selected_indices),
                mean_predicted_probability=mean_predicted_probability,
                observed_acceptance_rate=observed_acceptance_rate,
                absolute_calibration_gap=absolute_calibration_gap,
                weighted_calibration_gap=weighted_calibration_gap,
            )
        )
    return BoundedPlattHeldOutMetricSummary(
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        bins=tuple(bins),
    )


def _confidence_ordering_status(
    artifact: BoundedPlattScalingArtifact,
) -> BoundedPlattConfidenceOrderingStatus:
    """Validate monotonic ordering from the fixed positive-slope transform."""

    grid = tuple(index / 100 for index in range(101))
    calibrated = tuple(artifact.calibrate(value) for value in grid)
    if all(left <= right for left, right in zip(calibrated, calibrated[1:])):
        return BoundedPlattConfidenceOrderingStatus.PRESERVED
    return BoundedPlattConfidenceOrderingStatus.VIOLATED


def _assess_status(
    *,
    observation_count: int,
    brier_improvement: float,
    expected_calibration_error_improvement: float,
    confidence_ordering_status: BoundedPlattConfidenceOrderingStatus,
    protocol: BoundedPlattHeldOutAssessmentProtocol,
) -> BoundedPlattHeldOutAssessmentStatus:
    """Apply the predeclared V2 gate without changing final evidence or fitting behavior."""

    if observation_count < protocol.minimum_observation_count:
        return BoundedPlattHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_DATA
    if confidence_ordering_status is not BoundedPlattConfidenceOrderingStatus.PRESERVED:
        return BoundedPlattHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    if (
        brier_improvement < -_NUMERIC_TOLERANCE
        or expected_calibration_error_improvement < -_NUMERIC_TOLERANCE
    ):
        return BoundedPlattHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    if (
        brier_improvement <= _NUMERIC_TOLERANCE
        or expected_calibration_error_improvement <= _NUMERIC_TOLERANCE
    ):
        return BoundedPlattHeldOutAssessmentStatus.CALIBRATOR_NO_STRICT_IMPROVEMENT
    return BoundedPlattHeldOutAssessmentStatus.PASSES_HELD_OUT_FITNESS


def _decision_for_status(
    status: BoundedPlattHeldOutAssessmentStatus,
) -> tuple[BoundedPlattHeldOutPromotionDecision, BoundedPlattAdaptivePolicyResearchEligibility]:
    """Map one terminal assessment status to the only permitted next-step posture."""

    outcomes = {
        BoundedPlattHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_DATA: (
            BoundedPlattHeldOutPromotionDecision.NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA,
            BoundedPlattAdaptivePolicyResearchEligibility.BLOCKED_INSUFFICIENT_HELD_OUT_DATA,
        ),
        BoundedPlattHeldOutAssessmentStatus.CALIBRATOR_REGRESSION: (
            BoundedPlattHeldOutPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION,
            BoundedPlattAdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION,
        ),
        BoundedPlattHeldOutAssessmentStatus.CALIBRATOR_NO_STRICT_IMPROVEMENT: (
            BoundedPlattHeldOutPromotionDecision.NOT_PROMOTED_NO_STRICT_IMPROVEMENT,
            BoundedPlattAdaptivePolicyResearchEligibility.BLOCKED_NO_STRICT_IMPROVEMENT,
        ),
        BoundedPlattHeldOutAssessmentStatus.PASSES_HELD_OUT_FITNESS: (
            BoundedPlattHeldOutPromotionDecision.ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
            BoundedPlattAdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
        ),
    }
    return outcomes[status]


def _pretty_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize retained evidence identically on Windows and Unix-like systems."""

    return (json.dumps(payload, indent=2, sort_keys=False) + "\n").encode("utf-8")
