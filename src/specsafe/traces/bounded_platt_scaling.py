"""Deterministic calibration-only fitting for the frozen V2 bounded-Platt candidate.

This module consumes only a verified V2 calibration manifest. It cannot load final-evaluation
assets, emit scheduler actions, or make a promotion decision.
"""

from __future__ import annotations

import json
from enum import StrEnum
from math import exp, isfinite, log, sqrt
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from specsafe.contracts.models import StrictContract, TraceDataRole, TraceSourceType, TraceSplit
from specsafe.traces.calibration_redesign_v2_manifest import (
    CalibrationRedesignV2CalibrationManifestedFixtureSet,
    load_calibration_redesign_v2_calibration_manifested_fixture_set,
)

_ARTIFACT_ID = "bounded-platt-scaling-v1"
_ARTIFACT_VERSION = "1.0.0"
_EPSILON = 0.000001
_SLOPE_LOWER_BOUND = 0.25
_SLOPE_UPPER_BOUND = 4.0
_INTERCEPT_LOWER_BOUND = -4.0
_INTERCEPT_UPPER_BOUND = 4.0
_REGULARIZATION_STRENGTH = 0.01
_INITIAL_SLOPE = 1.0
_INITIAL_INTERCEPT = 0.0
_LEARNING_RATE = 0.05
_MAXIMUM_ITERATIONS = 4000
_CONVERGENCE_TOLERANCE = 0.0000000001
_GRADIENT_NORM_TOLERANCE = 0.00000001
_OPTIMIZER_ID = "deterministic_projected_gradient_descent_v1"
_ARTIFACT_FILENAME = "artifact.json"
_FIT_REPORT_FILENAME = "fit_report.json"


class BoundedPlattScalingViolationCode(StrEnum):
    """Machine-readable reasons the V2 calibration-only fit may be rejected."""

    UNTRUSTED_FIXTURE_SET = "untrusted_fixture_set"
    NON_CALIBRATION_EVIDENCE = "non_calibration_evidence"
    INSUFFICIENT_CALIBRATION_SAMPLES = "insufficient_calibration_samples"
    DEGENERATE_LABEL_DISTRIBUTION = "degenerate_label_distribution"
    NON_FINITE_CONFIDENCE = "non_finite_confidence"
    ARTIFACT_SCHEMA_ERROR = "artifact_schema_error"
    INVALID_DESTINATION = "invalid_destination"


class BoundedPlattScalingFitError(ValueError):
    """Typed error raised when the frozen V2 fitting boundary is violated."""

    def __init__(self, code: BoundedPlattScalingViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class BoundedPlattScalingFitProtocol(StrictContract):
    """Frozen optimizer and transform configuration selected before V2 fixture authoring."""

    optimizer_id: Literal["deterministic_projected_gradient_descent_v1"] = _OPTIMIZER_ID
    regularization_strength: float = Field(default=_REGULARIZATION_STRENGTH, ge=0.0)
    confidence_clipping_epsilon: float = Field(default=_EPSILON, gt=0.0, lt=0.5)
    slope_lower_bound: float = Field(default=_SLOPE_LOWER_BOUND, gt=0.0)
    slope_upper_bound: float = Field(default=_SLOPE_UPPER_BOUND, gt=0.0)
    intercept_lower_bound: float = Field(default=_INTERCEPT_LOWER_BOUND)
    intercept_upper_bound: float = Field(default=_INTERCEPT_UPPER_BOUND)
    initial_slope: float = Field(default=_INITIAL_SLOPE)
    initial_intercept: float = Field(default=_INITIAL_INTERCEPT)
    learning_rate: float = Field(default=_LEARNING_RATE, gt=0.0)
    maximum_iterations: int = Field(default=_MAXIMUM_ITERATIONS, gt=0)
    convergence_tolerance: float = Field(default=_CONVERGENCE_TOLERANCE, gt=0.0)
    gradient_norm_tolerance: float = Field(default=_GRADIENT_NORM_TOLERANCE, gt=0.0)

    @model_validator(mode="after")
    def validate_bounds_and_initial_values(self) -> BoundedPlattScalingFitProtocol:
        """Keep the predeclared bounds and initialization internally coherent."""

        if self.slope_lower_bound >= self.slope_upper_bound:
            raise ValueError("slope lower bound must be less than slope upper bound")
        if self.intercept_lower_bound >= self.intercept_upper_bound:
            raise ValueError("intercept lower bound must be less than intercept upper bound")
        if not self.slope_lower_bound <= self.initial_slope <= self.slope_upper_bound:
            raise ValueError("initial_slope must be inside the declared slope bounds")
        if not self.intercept_lower_bound <= self.initial_intercept <= self.intercept_upper_bound:
            raise ValueError("initial_intercept must be inside the declared intercept bounds")
        return self


DEFAULT_BOUNDED_PLATT_SCALING_FIT_PROTOCOL = BoundedPlattScalingFitProtocol()


class BoundedPlattScalingArtifact(StrictContract):
    """Immutable V2 artifact fitted from the verified calibration corpus only."""

    schema_version: Literal["bounded-platt-scaling-artifact-v1"]
    artifact_id: Literal["bounded-platt-scaling-v1"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_type: Literal[TraceSourceType.SYNTHETIC]
    fit_split: Literal[TraceSplit.CALIBRATION]
    fit_data_role: Literal[TraceDataRole.CALIBRATION]
    fit_case_ids: tuple[str, ...] = Field(min_length=1)
    fit_scenario_family_ids: tuple[str, ...] = Field(min_length=1)
    sample_count: int = Field(gt=0)
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    slope: float
    intercept: float
    objective_value: float = Field(ge=0.0)
    raw_negative_log_likelihood: float = Field(ge=0.0)
    calibrated_negative_log_likelihood: float = Field(ge=0.0)
    optimizer_id: Literal["deterministic_projected_gradient_descent_v1"]
    regularization_strength: float = Field(ge=0.0)
    confidence_clipping_epsilon: float = Field(gt=0.0, lt=0.5)
    slope_lower_bound: float = Field(gt=0.0)
    slope_upper_bound: float = Field(gt=0.0)
    intercept_lower_bound: float
    intercept_upper_bound: float
    initial_slope: float
    initial_intercept: float
    learning_rate: float = Field(gt=0.0)
    maximum_iterations: int = Field(gt=0)
    convergence_tolerance: float = Field(gt=0.0)
    gradient_norm_tolerance: float = Field(gt=0.0)
    fit_iteration_count: int = Field(ge=0)
    converged: bool
    final_evaluation_accessed: Literal[False]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "slope",
        "intercept",
        "objective_value",
        "raw_negative_log_likelihood",
        "calibrated_negative_log_likelihood",
    )
    @classmethod
    def validate_finite_values(cls, value: float) -> float:
        """Reject non-finite artifact metrics and parameters."""

        if not isfinite(value):
            raise ValueError("bounded-Platt artifact values must be finite")
        return value

    @model_validator(mode="after")
    def validate_counts_and_bounds(self) -> BoundedPlattScalingArtifact:
        """Keep artifact provenance, counts, and bounds internally consistent."""

        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("label counts must sum to sample_count")
        if self.slope_lower_bound >= self.slope_upper_bound:
            raise ValueError("artifact slope bounds are invalid")
        if self.intercept_lower_bound >= self.intercept_upper_bound:
            raise ValueError("artifact intercept bounds are invalid")
        if not self.slope_lower_bound <= self.slope <= self.slope_upper_bound:
            raise ValueError("artifact slope must remain inside its bounds")
        if not self.intercept_lower_bound <= self.intercept <= self.intercept_upper_bound:
            raise ValueError("artifact intercept must remain inside its bounds")
        return self

    def calibrate(self, raw_confidence: float) -> float:
        """Apply the frozen monotonic transform with the declared clipping boundary."""

        return _bounded_platt_probability(
            raw_confidence=raw_confidence,
            slope=self.slope,
            intercept=self.intercept,
            epsilon=self.confidence_clipping_epsilon,
        )


class BoundedPlattScalingFitReport(StrictContract):
    """Retained calibration-only fit record with no promotion outcome."""

    schema_version: Literal["bounded-platt-scaling-fit-report-v1"]
    artifact_id: Literal["bounded-platt-scaling-v1"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fit_scope: Literal["calibration_split_only"]
    objective: Literal["mean_binary_negative_log_likelihood_plus_l2_regularization"]
    optimizer_id: Literal["deterministic_projected_gradient_descent_v1"]
    regularization_strength: float = Field(ge=0.0)
    sample_count: int = Field(gt=0)
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    initial_slope: float
    initial_intercept: float
    final_slope: float
    final_intercept: float
    objective_value: float = Field(ge=0.0)
    raw_negative_log_likelihood: float = Field(ge=0.0)
    calibrated_negative_log_likelihood: float = Field(ge=0.0)
    fit_iteration_count: int = Field(ge=0)
    converged: bool
    failure_status: Literal["none"]
    final_evaluation_accessed: Literal[False]
    promotion_status: Literal["not_assessed"]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "initial_slope",
        "initial_intercept",
        "final_slope",
        "final_intercept",
        "objective_value",
        "raw_negative_log_likelihood",
        "calibrated_negative_log_likelihood",
    )
    @classmethod
    def validate_finite_values(cls, value: float) -> float:
        """Reject non-finite fit report values before evidence is retained."""

        if not isfinite(value):
            raise ValueError("bounded-Platt fit-report values must be finite")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> BoundedPlattScalingFitReport:
        """Keep reported sample counts internally consistent."""

        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("label counts must sum to sample_count")
        return self


class BoundedPlattScalingFitResult(StrictContract):
    """Typed pairing of one immutable V2 artifact and calibration-only fit report."""

    artifact: BoundedPlattScalingArtifact
    report: BoundedPlattScalingFitReport

    @model_validator(mode="after")
    def validate_artifact_report_alignment(self) -> BoundedPlattScalingFitResult:
        """Prevent a retained fit report from drifting away from its artifact."""

        aligned_fields = (
            "artifact_id",
            "artifact_version",
            "fixture_set_id",
            "fixture_set_version",
            "calibration_manifest_aggregate_sha256",
            "sample_count",
            "positive_label_count",
            "negative_label_count",
            "objective_value",
            "raw_negative_log_likelihood",
            "calibrated_negative_log_likelihood",
            "fit_iteration_count",
            "converged",
            "final_evaluation_accessed",
            "runtime_control_eligible",
        )
        for field_name in aligned_fields:
            artifact_value = getattr(self.artifact, field_name)
            report_value = getattr(self.report, field_name)
            if artifact_value != report_value:
                raise ValueError(f"artifact and fit report disagree on {field_name}")
        if self.report.final_slope != self.artifact.slope:
            raise ValueError("fit report final_slope must match artifact slope")
        if self.report.final_intercept != self.artifact.intercept:
            raise ValueError("fit report final_intercept must match artifact intercept")
        return self


def fit_bounded_platt_scaling(
    fixture_set: CalibrationRedesignV2CalibrationManifestedFixtureSet,
    *,
    protocol: BoundedPlattScalingFitProtocol = DEFAULT_BOUNDED_PLATT_SCALING_FIT_PROTOCOL,
) -> BoundedPlattScalingFitResult:
    """Fit the predeclared global bounded-Platt transform on verified calibration evidence only."""

    _validate_calibration_only_fixture_set(fixture_set)
    if not isinstance(protocol, BoundedPlattScalingFitProtocol):
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.ARTIFACT_SCHEMA_ERROR,
            "bounded-Platt fitting requires the frozen typed fit protocol",
        )

    probabilities, labels = _extract_fit_samples(fixture_set)
    sample_count = len(probabilities)
    positive_label_count = sum(labels)
    negative_label_count = sample_count - positive_label_count
    if sample_count < 2:
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.INSUFFICIENT_CALIBRATION_SAMPLES,
            "bounded-Platt scaling requires at least two calibration samples",
        )
    if positive_label_count == 0 or negative_label_count == 0:
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.DEGENERATE_LABEL_DISTRIBUTION,
            "bounded-Platt scaling requires both accepted and rejected calibration labels",
        )

    slope, intercept, objective_value, fit_iteration_count, converged = _fit_parameters(
        probabilities,
        labels,
        protocol,
    )
    raw_negative_log_likelihood = _mean_negative_log_likelihood(
        probabilities,
        labels,
        slope=1.0,
        intercept=0.0,
        epsilon=protocol.confidence_clipping_epsilon,
    )
    calibrated_negative_log_likelihood = _mean_negative_log_likelihood(
        probabilities,
        labels,
        slope=slope,
        intercept=intercept,
        epsilon=protocol.confidence_clipping_epsilon,
    )
    manifest = fixture_set.manifest
    fit_case_ids = tuple(sorted(case.runtime_input.case_id for case in fixture_set.cases))
    fit_scenario_family_ids = tuple(
        sorted({case.runtime_input.scenario_family_id for case in fixture_set.cases})
    )

    artifact = BoundedPlattScalingArtifact(
        schema_version="bounded-platt-scaling-artifact-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=manifest.fixture_set_id,
        fixture_set_version=manifest.fixture_set_version,
        calibration_manifest_aggregate_sha256=manifest.aggregate_sha256,
        source_type=TraceSourceType.SYNTHETIC,
        fit_split=TraceSplit.CALIBRATION,
        fit_data_role=TraceDataRole.CALIBRATION,
        fit_case_ids=fit_case_ids,
        fit_scenario_family_ids=fit_scenario_family_ids,
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        slope=slope,
        intercept=intercept,
        objective_value=objective_value,
        raw_negative_log_likelihood=raw_negative_log_likelihood,
        calibrated_negative_log_likelihood=calibrated_negative_log_likelihood,
        optimizer_id=protocol.optimizer_id,
        regularization_strength=protocol.regularization_strength,
        confidence_clipping_epsilon=protocol.confidence_clipping_epsilon,
        slope_lower_bound=protocol.slope_lower_bound,
        slope_upper_bound=protocol.slope_upper_bound,
        intercept_lower_bound=protocol.intercept_lower_bound,
        intercept_upper_bound=protocol.intercept_upper_bound,
        initial_slope=protocol.initial_slope,
        initial_intercept=protocol.initial_intercept,
        learning_rate=protocol.learning_rate,
        maximum_iterations=protocol.maximum_iterations,
        convergence_tolerance=protocol.convergence_tolerance,
        gradient_norm_tolerance=protocol.gradient_norm_tolerance,
        fit_iteration_count=fit_iteration_count,
        converged=converged,
        final_evaluation_accessed=False,
        runtime_control_eligible=False,
    )
    report = BoundedPlattScalingFitReport(
        schema_version="bounded-platt-scaling-fit-report-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=manifest.fixture_set_id,
        fixture_set_version=manifest.fixture_set_version,
        calibration_manifest_aggregate_sha256=manifest.aggregate_sha256,
        fit_scope="calibration_split_only",
        objective="mean_binary_negative_log_likelihood_plus_l2_regularization",
        optimizer_id=protocol.optimizer_id,
        regularization_strength=protocol.regularization_strength,
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        initial_slope=protocol.initial_slope,
        initial_intercept=protocol.initial_intercept,
        final_slope=slope,
        final_intercept=intercept,
        objective_value=objective_value,
        raw_negative_log_likelihood=raw_negative_log_likelihood,
        calibrated_negative_log_likelihood=calibrated_negative_log_likelihood,
        fit_iteration_count=fit_iteration_count,
        converged=converged,
        failure_status="none",
        final_evaluation_accessed=False,
        promotion_status="not_assessed",
        runtime_control_eligible=False,
    )
    return BoundedPlattScalingFitResult(artifact=artifact, report=report)


def write_bounded_platt_scaling_fit(
    fixture_root: Path,
    output_directory: Path,
) -> BoundedPlattScalingFitResult:
    """Write deterministic V2 calibration-only artifact and report evidence files."""

    fixture_set = load_calibration_redesign_v2_calibration_manifested_fixture_set(fixture_root)
    result = fit_bounded_platt_scaling(fixture_set)
    output_directory.mkdir(parents=True, exist_ok=True)
    artifact_path = output_directory / _ARTIFACT_FILENAME
    report_path = output_directory / _FIT_REPORT_FILENAME
    if artifact_path.suffix != ".json" or report_path.suffix != ".json":
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.INVALID_DESTINATION,
            "bounded-Platt fit evidence destinations must be JSON files",
        )
    _write_json(artifact_path, result.artifact.model_dump(mode="json"))
    _write_json(report_path, result.report.model_dump(mode="json"))
    return result


def project_bounded_platt_parameters(
    *,
    slope: float,
    intercept: float,
    protocol: BoundedPlattScalingFitProtocol = DEFAULT_BOUNDED_PLATT_SCALING_FIT_PROTOCOL,
) -> tuple[float, float]:
    """Project candidate parameters into the fixed V2 bounds for deterministic testing."""

    if not isfinite(slope) or not isfinite(intercept):
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.ARTIFACT_SCHEMA_ERROR,
            "bounded-Platt parameter projection requires finite values",
        )
    return (
        min(max(slope, protocol.slope_lower_bound), protocol.slope_upper_bound),
        min(max(intercept, protocol.intercept_lower_bound), protocol.intercept_upper_bound),
    )


def _validate_calibration_only_fixture_set(
    fixture_set: Any,
) -> CalibrationRedesignV2CalibrationManifestedFixtureSet:
    """Reject foreign, V1, held-out, or non-calibration objects before outcome labels are read."""

    if not isinstance(fixture_set, CalibrationRedesignV2CalibrationManifestedFixtureSet):
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.UNTRUSTED_FIXTURE_SET,
            "bounded-Platt fitting requires a verified V2 calibration manifested fixture set",
        )
    manifest = fixture_set.manifest
    if (
        manifest.fixture_set_id != "synthetic-calibration-redesign-v2"
        or manifest.candidate_artifact_id != _ARTIFACT_ID
    ):
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.UNTRUSTED_FIXTURE_SET,
            "bounded-Platt fitting requires the frozen V2 candidate manifest",
        )
    for case in fixture_set.cases:
        runtime = case.runtime_input
        outcomes = case.expected_outcomes
        if (
            runtime.split is not TraceSplit.CALIBRATION
            or runtime.data_role is not TraceDataRole.CALIBRATION
            or outcomes.split is not TraceSplit.CALIBRATION
            or outcomes.data_role is not TraceDataRole.CALIBRATION
        ):
            raise BoundedPlattScalingFitError(
                BoundedPlattScalingViolationCode.NON_CALIBRATION_EVIDENCE,
                "bounded-Platt fitting accepts calibration evidence only",
            )
    return fixture_set


def _extract_fit_samples(
    fixture_set: CalibrationRedesignV2CalibrationManifestedFixtureSet,
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Join validated runtime confidence and post-hoc labels only after boundary checks pass."""

    probabilities: list[float] = []
    labels: list[int] = []
    for replay_case in fixture_set.cases:
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in replay_case.runtime_input.contexts
        }
        for outcome in replay_case.expected_outcomes.outcomes:
            context = contexts_by_key[(outcome.decode_round, outcome.block_position_index)]
            confidence = context.conditional_survival_confidence
            if not isfinite(confidence):
                raise BoundedPlattScalingFitError(
                    BoundedPlattScalingViolationCode.NON_FINITE_CONFIDENCE,
                    "bounded-Platt fitting received a non-finite confidence",
                )
            probabilities.append(confidence)
            labels.append(int(outcome.observed_acceptance))
    return tuple(probabilities), tuple(labels)


def _fit_parameters(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
    protocol: BoundedPlattScalingFitProtocol,
) -> tuple[float, float, float, int, bool]:
    """Run fixed-step projected gradient descent with deterministic tie handling."""

    slope = protocol.initial_slope
    intercept = protocol.initial_intercept
    best_slope = slope
    best_intercept = intercept
    best_objective, _, _ = _objective_and_gradients(
        probabilities,
        labels,
        slope,
        intercept,
        protocol,
    )
    converged = False
    fit_iteration_count = 0

    for iteration in range(1, protocol.maximum_iterations + 1):
        current_objective, slope_gradient, intercept_gradient = _objective_and_gradients(
            probabilities,
            labels,
            slope,
            intercept,
            protocol,
        )
        gradient_norm = sqrt(slope_gradient**2 + intercept_gradient**2)
        if gradient_norm <= protocol.gradient_norm_tolerance:
            converged = True
            fit_iteration_count = iteration - 1
            break

        candidate_slope, candidate_intercept = project_bounded_platt_parameters(
            slope=slope - protocol.learning_rate * slope_gradient,
            intercept=intercept - protocol.learning_rate * intercept_gradient,
            protocol=protocol,
        )
        candidate_objective, _, _ = _objective_and_gradients(
            probabilities,
            labels,
            candidate_slope,
            candidate_intercept,
            protocol,
        )
        fit_iteration_count = iteration
        if candidate_objective < best_objective - protocol.convergence_tolerance:
            best_slope = candidate_slope
            best_intercept = candidate_intercept
            best_objective = candidate_objective
        objective_change = abs(candidate_objective - current_objective)
        slope = candidate_slope
        intercept = candidate_intercept
        if objective_change <= protocol.convergence_tolerance:
            converged = True
            break

    return best_slope, best_intercept, best_objective, fit_iteration_count, converged


def _objective_and_gradients(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
    slope: float,
    intercept: float,
    protocol: BoundedPlattScalingFitProtocol,
) -> tuple[float, float, float]:
    """Return mean NLL plus fixed regularization and analytic gradients."""

    total_negative_log_likelihood = 0.0
    slope_gradient = 0.0
    intercept_gradient = 0.0
    for probability, label in zip(probabilities, labels, strict=True):
        clipped_probability = _clip_probability(probability, protocol.confidence_clipping_epsilon)
        logit = log(clipped_probability / (1.0 - clipped_probability))
        calibrated_probability = _sigmoid(slope * logit + intercept)
        total_negative_log_likelihood += _binary_negative_log_likelihood(
            calibrated_probability,
            label,
        )
        residual = calibrated_probability - label
        slope_gradient += residual * logit
        intercept_gradient += residual
    sample_count = len(probabilities)
    mean_negative_log_likelihood = total_negative_log_likelihood / sample_count
    mean_slope_gradient = slope_gradient / sample_count
    mean_intercept_gradient = intercept_gradient / sample_count
    regularization = protocol.regularization_strength * ((slope - 1.0) ** 2 + intercept**2)
    return (
        mean_negative_log_likelihood + regularization,
        mean_slope_gradient + 2.0 * protocol.regularization_strength * (slope - 1.0),
        mean_intercept_gradient + 2.0 * protocol.regularization_strength * intercept,
    )


def _mean_negative_log_likelihood(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
    *,
    slope: float,
    intercept: float,
    epsilon: float,
) -> float:
    """Compute unregularized mean binary NLL for raw or calibrated probabilities."""

    total = 0.0
    for probability, label in zip(probabilities, labels, strict=True):
        calibrated_probability = _bounded_platt_probability(
            raw_confidence=probability,
            slope=slope,
            intercept=intercept,
            epsilon=epsilon,
        )
        total += _binary_negative_log_likelihood(calibrated_probability, label)
    return total / len(probabilities)


def _bounded_platt_probability(
    *,
    raw_confidence: float,
    slope: float,
    intercept: float,
    epsilon: float,
) -> float:
    """Apply clipping, logit, and a stable sigmoid while preserving finite open probabilities."""

    if not isfinite(raw_confidence) or not 0.0 <= raw_confidence <= 1.0:
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.NON_FINITE_CONFIDENCE,
            "raw_confidence must be finite and inside the closed interval [0, 1]",
        )
    clipped_probability = _clip_probability(raw_confidence, epsilon)
    logit = log(clipped_probability / (1.0 - clipped_probability))
    return _sigmoid(slope * logit + intercept)


def _clip_probability(raw_confidence: float, epsilon: float) -> float:
    """Bound raw confidence away from zero and one before taking the logit."""

    return min(max(raw_confidence, epsilon), 1.0 - epsilon)


def _sigmoid(value: float) -> float:
    """Compute a finite sigmoid without overflow for large signed logits."""

    if value >= 0.0:
        return 1.0 / (1.0 + exp(-value))
    exponent = exp(value)
    return exponent / (1.0 + exponent)


def _binary_negative_log_likelihood(probability: float, label: int) -> float:
    """Compute binary NLL after the transform already guarantees an open probability."""

    if label not in (0, 1):
        raise BoundedPlattScalingFitError(
            BoundedPlattScalingViolationCode.ARTIFACT_SCHEMA_ERROR,
            "bounded-Platt labels must be zero or one",
        )
    if label == 1:
        return -log(probability)
    return -log(1.0 - probability)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic reviewable evidence without embedding raw fixture payloads."""

    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
