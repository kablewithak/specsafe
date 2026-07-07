"""Calibration-only deterministic fit and diagnostics for frozen V5 evidence.

The V5 fit boundary consumes the immutable V5 calibration manifest and the 48 calibration-only
case pairs it names. It writes a frozen bounded-monotone-beta artifact and a calibration-only
diagnostic report once. It cannot load V5 final assets, select thresholds, execute a policy, or
make a promotion decision.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from enum import StrEnum
from math import isfinite, log, sqrt
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract, WorkloadType
from specsafe.heldout_calibration.v5_final_assessment import (
    DEFAULT_V5_BOUNDED_MONOTONE_BETA_CALIBRATION_PROTOCOL,
    V5BoundedMonotoneBetaCalibrationArtifact,
    V5BoundedMonotoneBetaCalibrationProtocol,
    V5BoundedMonotoneBetaParameters,
    V5EvidenceRole,
    V5FrozenEvidenceManifestReference,
    calculate_tie_aware_auroc,
    calculate_v5_bounded_monotone_beta_probability,
    verify_v5_bounded_monotone_beta_monotonicity,
)
from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    load_calibration_successor_v5_scenario_family_registry,
)
from specsafe.traces.calibration_successor_v5_cases import (
    CalibrationSuccessorV5CaseContractError,
    load_calibration_successor_v5_curve_coverage_replay_case,
    load_calibration_successor_v5_mixed_reliability_contrast_replay_case,
    load_calibration_successor_v5_position_spread_replay_case,
    load_calibration_successor_v5_workload_variation_replay_case,
)
from specsafe.traces.calibration_successor_v5_manifest import (
    CalibrationSuccessorV5CalibrationManifest,
    CalibrationSuccessorV5ManifestError,
    load_calibration_successor_v5_calibration_manifest,
)

_ARTIFACT_FILENAME = "bounded_monotone_beta_calibration_artifact.json"
_DIAGNOSTICS_FILENAME = "bounded_monotone_beta_calibration_fit_diagnostics.json"
_ARTIFACT_SCHEMA_VERSION = "bounded-monotone-beta-calibration-artifact-v5"
_DIAGNOSTICS_SCHEMA_VERSION = "bounded-monotone-beta-calibration-fit-diagnostics-v1"
_DIAGNOSTICS_ID = "v5-bounded-monotone-beta-calibration-fit-diagnostics"
_EXPECTED_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(101, 149))
_EXPECTED_OBSERVATION_COUNT = 192
_BOUNDARY_INPUTS = (0.0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0)
_ECE_BIN_COUNT = 10
_DIAGNOSTIC_DECIMAL_PLACES = 12
_DIAGNOSTIC_QUANTUM = Decimal("0.000000000001")


class V5BoundedMonotoneBetaFitViolationCode(StrEnum):
    """Machine-readable failures at the V5 calibration-only fit boundary."""

    DESTINATION_ALREADY_EXISTS = "v5_bounded_monotone_beta_fit_destination_already_exists"
    ROOT_NOT_AUTHORISED = "v5_bounded_monotone_beta_fit_root_not_authorised"
    MANIFEST_INTEGRITY_FAILURE = "v5_bounded_monotone_beta_fit_manifest_integrity_failure"
    CALIBRATION_CASE_LOAD_FAILURE = "v5_bounded_monotone_beta_fit_case_load_failure"
    CALIBRATION_DATA_INVALID = "v5_bounded_monotone_beta_fit_calibration_data_invalid"
    DEGENERATE_LABEL_DISTRIBUTION = "v5_bounded_monotone_beta_fit_degenerate_label_distribution"
    ARTIFACT_SCHEMA_ERROR = "v5_bounded_monotone_beta_fit_artifact_schema_error"
    DIAGNOSTIC_SCHEMA_ERROR = "v5_bounded_monotone_beta_fit_diagnostic_schema_error"
    WRITE_ERROR = "v5_bounded_monotone_beta_fit_write_error"
    PROVENANCE_MISMATCH = "v5_bounded_monotone_beta_fit_provenance_mismatch"


class V5BoundedMonotoneBetaFitError(ValueError):
    """Raised when V5 cannot retain trustworthy calibration-only fit evidence."""

    def __init__(self, code: V5BoundedMonotoneBetaFitViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class V5CalibrationProbabilityMetrics(StrictContract):
    """Calibration-only probability diagnostics with no eligibility decision."""

    brier_score: float = Field(ge=0.0, le=1.0)
    ece_10_bin: float = Field(ge=0.0, le=1.0)
    auroc: float = Field(ge=0.0, le=1.0)
    mean_binary_negative_log_likelihood: float = Field(ge=0.0)


class V5BoundedMonotoneBetaFitDiagnostics(StrictContract):
    """One retained V5 calibration-only diagnostic report for the frozen artifact."""

    schema_version: Literal["bounded-monotone-beta-calibration-fit-diagnostics-v1"] = (
        _DIAGNOSTICS_SCHEMA_VERSION
    )
    diagnostics_id: Literal["v5-bounded-monotone-beta-calibration-fit-diagnostics"] = (
        _DIAGNOSTICS_ID
    )
    artifact_schema_version: Literal["bounded-monotone-beta-calibration-artifact-v5"] = (
        _ARTIFACT_SCHEMA_VERSION
    )
    artifact_relative_path: Literal["bounded_monotone_beta_calibration_artifact.json"] = (
        _ARTIFACT_FILENAME
    )
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    diagnostic_numeric_precision_decimal_places: Literal[12] = _DIAGNOSTIC_DECIMAL_PLACES
    calibration_manifest: V5FrozenEvidenceManifestReference
    protocol: V5BoundedMonotoneBetaCalibrationProtocol
    sample_count: Literal[192] = _EXPECTED_OBSERVATION_COUNT
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    case_ids: tuple[str, ...] = Field(min_length=48, max_length=48)
    scenario_family_ids: tuple[str, ...] = Field(min_length=4, max_length=4)
    workload_observation_counts: tuple[tuple[WorkloadType, int], ...] = Field(
        min_length=3,
        max_length=3,
    )
    initial_parameters: V5BoundedMonotoneBetaParameters
    final_parameters: V5BoundedMonotoneBetaParameters
    initial_objective_value: float = Field(ge=0.0)
    final_objective_value: float = Field(ge=0.0)
    initial_gradient_norm: float = Field(ge=0.0)
    final_gradient_norm: float = Field(ge=0.0)
    fit_iteration_count: int = Field(ge=0, le=8000)
    converged: bool
    convergence_reason: Literal[
        "objective_tolerance",
        "gradient_norm_tolerance",
        "maximum_iterations",
    ]
    raw_metrics: V5CalibrationProbabilityMetrics
    calibrated_metrics: V5CalibrationProbabilityMetrics
    brier_score_improvement: float
    ece_10_bin_improvement: float
    auroc_delta: float
    final_evaluation_accessed: Literal[False] = False
    threshold_selection_performed: Literal[False] = False
    scheduler_or_policy_execution_performed: Literal[False] = False
    promotion_status: Literal["not_assessed"] = "not_assessed"
    runtime_control_eligible: Literal[False] = False

    @model_validator(mode="after")
    def validate_diagnostics(self) -> V5BoundedMonotoneBetaFitDiagnostics:
        if self.calibration_manifest.evidence_role is not V5EvidenceRole.CALIBRATION:
            raise ValueError("V5 fit diagnostics may reference calibration evidence only")
        if type(self.protocol) is not V5BoundedMonotoneBetaCalibrationProtocol:
            raise ValueError("V5 fit diagnostics require the exact V5 protocol")
        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("V5 diagnostics label counts must sum to sample_count")
        if self.case_ids != _EXPECTED_CASE_IDS:
            raise ValueError("V5 diagnostics must retain CSV5-101 through CSV5-148")
        expected_workloads = (
            (WorkloadType.STRUCTURED_TEXT, 64),
            (WorkloadType.CODE, 64),
            (WorkloadType.OPEN_ENDED_CHAT, 64),
        )
        if self.workload_observation_counts != expected_workloads:
            raise ValueError("V5 diagnostics must retain balanced workload observation counts")
        _require_matching_float(
            actual=self.brier_score_improvement,
            expected=self.raw_metrics.brier_score - self.calibrated_metrics.brier_score,
            message="V5 calibration brier improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.ece_10_bin_improvement,
            expected=self.raw_metrics.ece_10_bin - self.calibrated_metrics.ece_10_bin,
            message="V5 calibration ECE improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.auroc_delta,
            expected=self.calibrated_metrics.auroc - self.raw_metrics.auroc,
            message="V5 calibration AUROC delta must match retained metrics",
        )
        if self.final_objective_value > self.initial_objective_value + 1e-12:
            raise ValueError("V5 projected-gradient fit must not retain a worse objective")
        return self


class V5BoundedMonotoneBetaFitResult(StrictContract):
    """In-memory calibration-only result before its canonical write-once persistence."""

    artifact: V5BoundedMonotoneBetaCalibrationArtifact
    diagnostics: V5BoundedMonotoneBetaFitDiagnostics

    @model_validator(mode="after")
    def validate_result_alignment(self) -> V5BoundedMonotoneBetaFitResult:
        if self.artifact.calibration_manifest != self.diagnostics.calibration_manifest:
            raise ValueError("V5 artifact and diagnostics must reference the same manifest")
        if self.artifact.protocol != self.diagnostics.protocol:
            raise ValueError("V5 artifact and diagnostics must retain the same protocol")
        if self.artifact.parameters != self.diagnostics.final_parameters:
            raise ValueError("V5 diagnostics must retain the artifact parameters")
        return self


@dataclass(frozen=True)
class _CalibrationObservation:
    case_id: str
    trace_id: str
    scenario_family_id: str
    workload_type: WorkloadType
    block_position_index: int
    raw_confidence: float
    observed_acceptance: bool


def fit_v5_bounded_monotone_beta_calibration(
    root: Path,
) -> V5BoundedMonotoneBetaFitResult:
    """Fit V5 exactly once in memory from the verified calibration corpus only."""

    resolved_root = root.resolve()
    _assert_fit_destinations_absent(resolved_root)
    manifest = _load_manifest_for_fit(resolved_root)
    observations = _load_calibration_observations(resolved_root)
    _validate_observations(observations)

    protocol = DEFAULT_V5_BOUNDED_MONOTONE_BETA_CALIBRATION_PROTOCOL
    fitted_parameters, fit_metadata = _fit_projected_gradient_descent(observations, protocol)
    calibration_manifest_reference = _build_calibration_manifest_reference(resolved_root, manifest)
    observed_confidences = tuple(item.raw_confidence for item in observations)
    artifact = V5BoundedMonotoneBetaCalibrationArtifact(
        protocol=protocol,
        calibration_manifest=calibration_manifest_reference,
        parameters=fitted_parameters,
        monotonicity_verification=verify_v5_bounded_monotone_beta_monotonicity(
            parameters=fitted_parameters,
            boundary_inputs=_BOUNDARY_INPUTS,
            observed_calibration_inputs=observed_confidences,
        ),
    )
    artifact_bytes = canonical_v5_bounded_monotone_beta_artifact_json(artifact)
    diagnostics = _build_diagnostics(
        observations=observations,
        artifact=artifact,
        artifact_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        fit_metadata=fit_metadata,
    )
    return V5BoundedMonotoneBetaFitResult(artifact=artifact, diagnostics=diagnostics)


def write_v5_bounded_monotone_beta_calibration_fit(
    root: Path,
) -> V5BoundedMonotoneBetaFitResult:
    """Persist V5 calibration-only artifact and diagnostics, then advance the registry."""

    resolved_root = root.resolve()
    result = fit_v5_bounded_monotone_beta_calibration(resolved_root)
    artifact_path = resolved_root / _ARTIFACT_FILENAME
    diagnostics_path = resolved_root / _DIAGNOSTICS_FILENAME
    registry_path = resolved_root / "scenario_family_registry.json"
    artifact_bytes = canonical_v5_bounded_monotone_beta_artifact_json(result.artifact)
    diagnostics_bytes = canonical_v5_bounded_monotone_beta_fit_diagnostics_json(result.diagnostics)
    registry_payload = _build_fit_retained_registry_payload(
        resolved_root=resolved_root,
        artifact_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        diagnostics_sha256=hashlib.sha256(diagnostics_bytes).hexdigest(),
    )

    try:
        _write_file_once(artifact_path, artifact_bytes)
        _write_file_once(diagnostics_path, diagnostics_bytes)
        _replace_file(registry_path, _canonical_file_bytes(registry_payload))
    except OSError as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.WRITE_ERROR,
            f"unable to persist V5 calibration-only fit evidence: {error}",
        ) from error
    return result


def load_v5_bounded_monotone_beta_calibration_fit(
    root: Path,
) -> V5BoundedMonotoneBetaFitResult:
    """Load and verify post-fit V5 calibration-only artifacts without touching final evidence."""

    resolved_root = root.resolve()
    try:
        final_evaluation_present = (resolved_root / "final_evaluation").is_dir()
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_curve_coverage_assets=final_evaluation_present,
            allow_calibration_fit_diagnostics_assets=not final_evaluation_present,
        )
        manifest = load_calibration_successor_v5_calibration_manifest(resolved_root)
    except (CalibrationSuccessorV5RegistryLoadError, CalibrationSuccessorV5ManifestError) as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.ROOT_NOT_AUTHORISED,
            f"V5 calibration fit root is not authorised: {error}",
        ) from error

    artifact_path = resolved_root / _ARTIFACT_FILENAME
    diagnostics_path = resolved_root / _DIAGNOSTICS_FILENAME
    artifact = _read_contract(
        artifact_path,
        V5BoundedMonotoneBetaCalibrationArtifact,
        V5BoundedMonotoneBetaFitViolationCode.ARTIFACT_SCHEMA_ERROR,
    )
    diagnostics = _read_contract(
        diagnostics_path,
        V5BoundedMonotoneBetaFitDiagnostics,
        V5BoundedMonotoneBetaFitViolationCode.DIAGNOSTIC_SCHEMA_ERROR,
    )
    artifact_bytes = artifact_path.read_bytes()
    diagnostics_bytes = diagnostics_path.read_bytes()
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    diagnostics_sha256 = hashlib.sha256(diagnostics_bytes).hexdigest()

    if registry.frozen_calibration_artifact_sha256 != artifact_sha256:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 registry calibration artifact SHA-256 does not match retained artifact bytes",
        )
    if registry.frozen_calibration_fit_diagnostics_sha256 != diagnostics_sha256:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 registry diagnostics SHA-256 does not match retained diagnostics bytes",
        )
    expected_manifest = _build_calibration_manifest_reference(resolved_root, manifest)
    if artifact.calibration_manifest != expected_manifest:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 artifact does not identify the frozen calibration manifest exactly",
        )
    if diagnostics.calibration_manifest != expected_manifest:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 diagnostics do not identify the frozen calibration manifest exactly",
        )
    if diagnostics.artifact_sha256 != artifact_sha256:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 diagnostics artifact SHA-256 does not match retained artifact bytes",
        )
    if canonical_v5_bounded_monotone_beta_artifact_json(artifact) != artifact_bytes:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 artifact bytes are not canonical",
        )
    if canonical_v5_bounded_monotone_beta_fit_diagnostics_json(diagnostics) != diagnostics_bytes:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            "V5 diagnostics bytes are not canonical",
        )
    try:
        return V5BoundedMonotoneBetaFitResult(artifact=artifact, diagnostics=diagnostics)
    except ValidationError as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            f"V5 retained fit artifacts disagree: {error}",
        ) from error


def canonical_v5_bounded_monotone_beta_artifact_json(
    artifact: V5BoundedMonotoneBetaCalibrationArtifact,
) -> bytes:
    """Serialize a validated V5 artifact with deterministic, hash-stable bytes."""

    if type(artifact) is not V5BoundedMonotoneBetaCalibrationArtifact:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.ARTIFACT_SCHEMA_ERROR,
            "canonical V5 artifact serialization requires the exact artifact contract",
        )
    return _canonical_file_bytes(artifact.model_dump(mode="json"))


def canonical_v5_bounded_monotone_beta_fit_diagnostics_json(
    diagnostics: V5BoundedMonotoneBetaFitDiagnostics,
) -> bytes:
    """Serialize validated V5 fit diagnostics with deterministic, hash-stable bytes."""

    if type(diagnostics) is not V5BoundedMonotoneBetaFitDiagnostics:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.DIAGNOSTIC_SCHEMA_ERROR,
            "canonical V5 diagnostics serialization requires the exact diagnostics contract",
        )
    return _canonical_file_bytes(diagnostics.model_dump(mode="json"))


def _assert_fit_destinations_absent(root: Path) -> None:
    existing = tuple(
        path.name
        for path in (root / _ARTIFACT_FILENAME, root / _DIAGNOSTICS_FILENAME)
        if path.exists()
    )
    if existing:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.DESTINATION_ALREADY_EXISTS,
            "V5 calibration fit destinations already exist and must not be rebuilt: "
            + ", ".join(existing),
        )


def _load_manifest_for_fit(root: Path) -> CalibrationSuccessorV5CalibrationManifest:
    try:
        return load_calibration_successor_v5_calibration_manifest(root)
    except CalibrationSuccessorV5ManifestError as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.MANIFEST_INTEGRITY_FAILURE,
            f"V5 bounded-monotone-beta fit requires the frozen calibration manifest: {error}",
        ) from error


def _load_calibration_observations(root: Path) -> tuple[_CalibrationObservation, ...]:
    observations: list[_CalibrationObservation] = []
    for case_id in _EXPECTED_CASE_IDS:
        replay_case = _load_case(root, case_id)
        for context, outcome in zip(
            replay_case.runtime_input.contexts,
            replay_case.expected_outcomes.outcomes,
            strict=True,
        ):
            observations.append(
                _CalibrationObservation(
                    case_id=case_id,
                    trace_id=replay_case.runtime_input.trace_id,
                    scenario_family_id=replay_case.runtime_input.scenario_family_id,
                    workload_type=context.workload_type,
                    block_position_index=context.block_position_index,
                    raw_confidence=context.conditional_survival_confidence,
                    observed_acceptance=outcome.observed_acceptance,
                )
            )
    return tuple(observations)


def _load_case(root: Path, case_id: str):
    try:
        if case_id <= "CSV5-112":
            return load_calibration_successor_v5_curve_coverage_replay_case(root, case_id)
        if case_id <= "CSV5-124":
            return load_calibration_successor_v5_position_spread_replay_case(root, case_id)
        if case_id <= "CSV5-136":
            return load_calibration_successor_v5_workload_variation_replay_case(root, case_id)
        return load_calibration_successor_v5_mixed_reliability_contrast_replay_case(root, case_id)
    except CalibrationSuccessorV5CaseContractError as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.CALIBRATION_CASE_LOAD_FAILURE,
            f"unable to load V5 calibration case {case_id}: {error}",
        ) from error


def _validate_observations(observations: tuple[_CalibrationObservation, ...]) -> None:
    if len(observations) != _EXPECTED_OBSERVATION_COUNT:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.CALIBRATION_DATA_INVALID,
            "V5 bounded-monotone-beta fit requires exactly 192 calibration observations",
        )
    labels = tuple(item.observed_acceptance for item in observations)
    if not any(labels) or all(labels):
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.DEGENERATE_LABEL_DISTRIBUTION,
            "V5 calibration labels must retain both accepted and rejected observations",
        )
    if any(
        not isfinite(item.raw_confidence) or not 0.0 <= item.raw_confidence <= 1.0
        for item in observations
    ):
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.CALIBRATION_DATA_INVALID,
            "V5 calibration raw confidences must be finite probabilities",
        )


def _fit_projected_gradient_descent(
    observations: tuple[_CalibrationObservation, ...],
    protocol: V5BoundedMonotoneBetaCalibrationProtocol,
) -> tuple[V5BoundedMonotoneBetaParameters, dict[str, object]]:
    parameters = V5BoundedMonotoneBetaParameters(
        a=protocol.initial_a,
        b=protocol.initial_b,
        c=protocol.initial_c,
    )
    initial_objective, initial_gradient = _objective_and_gradient(
        observations, parameters, protocol
    )
    current_objective = initial_objective
    current_gradient = initial_gradient
    best_parameters = parameters
    best_objective = initial_objective
    converged = False
    convergence_reason: Literal[
        "objective_tolerance",
        "gradient_norm_tolerance",
        "maximum_iterations",
    ] = "maximum_iterations"
    iteration_count = 0

    for iteration in range(1, protocol.maximum_iterations + 1):
        gradient_norm = _gradient_norm(current_gradient)
        if gradient_norm <= protocol.gradient_norm_tolerance:
            converged = True
            convergence_reason = "gradient_norm_tolerance"
            break
        candidate = _project_parameters(
            a=parameters.a - protocol.learning_rate * current_gradient[0],
            b=parameters.b - protocol.learning_rate * current_gradient[1],
            c=parameters.c - protocol.learning_rate * current_gradient[2],
            protocol=protocol,
        )
        candidate_objective, candidate_gradient = _objective_and_gradient(
            observations,
            candidate,
            protocol,
        )
        iteration_count = iteration
        objective_delta = abs(current_objective - candidate_objective)
        parameters = candidate
        current_objective = candidate_objective
        current_gradient = candidate_gradient
        if candidate_objective < best_objective:
            best_parameters = candidate
            best_objective = candidate_objective
        if objective_delta <= protocol.objective_tolerance:
            converged = True
            convergence_reason = "objective_tolerance"
            break

    final_parameters = best_parameters
    final_objective, final_gradient = _objective_and_gradient(
        observations,
        final_parameters,
        protocol,
    )
    return final_parameters, {
        "initial_objective": initial_objective,
        "initial_gradient_norm": _gradient_norm(initial_gradient),
        "final_objective": final_objective,
        "final_gradient_norm": _gradient_norm(final_gradient),
        "iteration_count": iteration_count,
        "converged": converged,
        "convergence_reason": convergence_reason,
    }


def _objective_and_gradient(
    observations: tuple[_CalibrationObservation, ...],
    parameters: V5BoundedMonotoneBetaParameters,
    protocol: V5BoundedMonotoneBetaCalibrationProtocol,
) -> tuple[float, tuple[float, float, float]]:
    probabilities: list[float] = []
    labels: list[float] = []
    feature_a: list[float] = []
    feature_b: list[float] = []
    epsilon = protocol.confidence_clipping_epsilon
    for observation in observations:
        clipped = min(max(observation.raw_confidence, epsilon), 1.0 - epsilon)
        probabilities.append(
            calculate_v5_bounded_monotone_beta_probability(observation.raw_confidence, parameters)
        )
        labels.append(1.0 if observation.observed_acceptance else 0.0)
        feature_a.append(log(clipped))
        feature_b.append(-log(1.0 - clipped))
    sample_count = len(observations)
    nll = _mean_binary_negative_log_likelihood(probabilities, labels)
    regularization = protocol.objective_regularization_weight * (
        (parameters.a - 1.0) ** 2 + (parameters.b - 1.0) ** 2 + parameters.c**2
    )
    residuals = tuple(
        probability - label for probability, label in zip(probabilities, labels, strict=True)
    )
    gradient_a = (
        sum(residual * feature for residual, feature in zip(residuals, feature_a, strict=True))
        / sample_count
    )
    gradient_b = (
        sum(residual * feature for residual, feature in zip(residuals, feature_b, strict=True))
        / sample_count
    )
    gradient_c = sum(residuals) / sample_count
    gradient_a += 2.0 * protocol.objective_regularization_weight * (parameters.a - 1.0)
    gradient_b += 2.0 * protocol.objective_regularization_weight * (parameters.b - 1.0)
    gradient_c += 2.0 * protocol.objective_regularization_weight * parameters.c
    return nll + regularization, (gradient_a, gradient_b, gradient_c)


def _project_parameters(
    *,
    a: float,
    b: float,
    c: float,
    protocol: V5BoundedMonotoneBetaCalibrationProtocol,
) -> V5BoundedMonotoneBetaParameters:
    return V5BoundedMonotoneBetaParameters(
        a=min(max(a, protocol.a_minimum), protocol.a_maximum),
        b=min(max(b, protocol.b_minimum), protocol.b_maximum),
        c=min(max(c, protocol.c_minimum), protocol.c_maximum),
    )


def _build_diagnostics(
    *,
    observations: tuple[_CalibrationObservation, ...],
    artifact: V5BoundedMonotoneBetaCalibrationArtifact,
    artifact_sha256: str,
    fit_metadata: dict[str, object],
) -> V5BoundedMonotoneBetaFitDiagnostics:
    raw_probabilities = tuple(item.raw_confidence for item in observations)
    labels = tuple(item.observed_acceptance for item in observations)
    calibrated_probabilities = tuple(
        calculate_v5_bounded_monotone_beta_probability(value, artifact.parameters)
        for value in raw_probabilities
    )
    raw_metrics = _probability_metrics(raw_probabilities, labels)
    calibrated_metrics = _probability_metrics(calibrated_probabilities, labels)
    workload_counts = tuple(
        (workload, sum(item.workload_type is workload for item in observations))
        for workload in (
            WorkloadType.STRUCTURED_TEXT,
            WorkloadType.CODE,
            WorkloadType.OPEN_ENDED_CHAT,
        )
    )
    return V5BoundedMonotoneBetaFitDiagnostics(
        artifact_sha256=artifact_sha256,
        calibration_manifest=artifact.calibration_manifest,
        protocol=artifact.protocol,
        positive_label_count=sum(labels),
        negative_label_count=len(labels) - sum(labels),
        case_ids=_EXPECTED_CASE_IDS,
        scenario_family_ids=(
            "CSV5-CAL-CURVE-COVERAGE",
            "CSV5-CAL-POSITION-SPREAD",
            "CSV5-CAL-WORKLOAD-VARIATION",
            "CSV5-CAL-MIXED-RELIABILITY-CONTRAST",
        ),
        workload_observation_counts=workload_counts,
        initial_parameters=V5BoundedMonotoneBetaParameters(a=1.0, b=1.0, c=0.0),
        final_parameters=artifact.parameters,
        initial_objective_value=_stable_diagnostic_float(float(fit_metadata["initial_objective"])),
        final_objective_value=_stable_diagnostic_float(float(fit_metadata["final_objective"])),
        initial_gradient_norm=_stable_diagnostic_float(
            float(fit_metadata["initial_gradient_norm"])
        ),
        final_gradient_norm=_stable_diagnostic_float(float(fit_metadata["final_gradient_norm"])),
        fit_iteration_count=int(fit_metadata["iteration_count"]),
        converged=bool(fit_metadata["converged"]),
        convergence_reason=str(fit_metadata["convergence_reason"]),
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        brier_score_improvement=_stable_diagnostic_float(
            raw_metrics.brier_score - calibrated_metrics.brier_score
        ),
        ece_10_bin_improvement=_stable_diagnostic_float(
            raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
        ),
        auroc_delta=_stable_diagnostic_float(calibrated_metrics.auroc - raw_metrics.auroc),
    )


def _probability_metrics(
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
) -> V5CalibrationProbabilityMetrics:
    numeric_labels = tuple(1.0 if label else 0.0 for label in labels)
    return V5CalibrationProbabilityMetrics(
        brier_score=_stable_diagnostic_float(
            sum(
                (probability - label) ** 2
                for probability, label in zip(probabilities, numeric_labels, strict=True)
            )
            / len(probabilities)
        ),
        ece_10_bin=_stable_diagnostic_float(
            _expected_calibration_error(probabilities, numeric_labels)
        ),
        auroc=_stable_diagnostic_float(calculate_tie_aware_auroc(probabilities, labels)),
        mean_binary_negative_log_likelihood=_stable_diagnostic_float(
            _mean_binary_negative_log_likelihood(probabilities, numeric_labels)
        ),
    )


def _expected_calibration_error(
    probabilities: tuple[float, ...], labels: tuple[float, ...]
) -> float:
    bin_totals = [0] * _ECE_BIN_COUNT
    bin_probability_sums = [0.0] * _ECE_BIN_COUNT
    bin_label_sums = [0.0] * _ECE_BIN_COUNT
    for probability, label in zip(probabilities, labels, strict=True):
        index = min(int(probability * _ECE_BIN_COUNT), _ECE_BIN_COUNT - 1)
        bin_totals[index] += 1
        bin_probability_sums[index] += probability
        bin_label_sums[index] += label
    sample_count = len(probabilities)
    return sum(
        (count / sample_count)
        * abs((bin_probability_sums[index] / count) - (bin_label_sums[index] / count))
        for index, count in enumerate(bin_totals)
        if count
    )


def _mean_binary_negative_log_likelihood(
    probabilities: tuple[float, ...] | list[float],
    labels: tuple[float, ...] | list[float],
) -> float:
    epsilon = 1e-15
    return -sum(
        label * log(min(max(probability, epsilon), 1.0 - epsilon))
        + (1.0 - label) * log(1.0 - min(max(probability, epsilon), 1.0 - epsilon))
        for probability, label in zip(probabilities, labels, strict=True)
    ) / len(probabilities)


def _gradient_norm(gradient: tuple[float, float, float]) -> float:
    return sqrt(sum(component * component for component in gradient))


def _build_calibration_manifest_reference(
    root: Path,
    manifest: CalibrationSuccessorV5CalibrationManifest,
) -> V5FrozenEvidenceManifestReference:
    return V5FrozenEvidenceManifestReference(
        evidence_role=V5EvidenceRole.CALIBRATION,
        manifest_schema_version=manifest.schema_version,
        manifest_relative_path="calibration_manifest.json",
        manifest_sha256=hashlib.sha256(
            (root / "calibration_manifest.json").read_bytes()
        ).hexdigest(),
        aggregate_sha256=manifest.aggregate_sha256,
        case_id_start="CSV5-101",
        case_id_end="CSV5-148",
        case_count=manifest.case_pair_count,
        observation_count=manifest.observation_count,
    )


def _build_fit_retained_registry_payload(
    *,
    resolved_root: Path,
    artifact_sha256: str,
    diagnostics_sha256: str,
) -> dict[str, object]:
    try:
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_calibration_manifest_assets=True,
        )
    except CalibrationSuccessorV5RegistryLoadError as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.ROOT_NOT_AUTHORISED,
            f"V5 registry cannot advance from the manifest stage: {error}",
        ) from error
    payload = registry.model_dump(mode="json")
    old_exclusions = {
        "No V5 calibration artifact, fit diagnostic, or final assessment result is present.",
        "No V5 fitter, threshold selection, or parameter mutation is authorized.",
    }
    payload["explicit_exclusions"] = [
        item for item in payload["explicit_exclusions"] if item not in old_exclusions
    ]
    payload["explicit_exclusions"].extend(
        (
            "V5 bounded-monotone-beta calibration artifact and fit diagnostics are retained "
            "as calibration-only evidence.",
            "No V5 final-evaluation asset, final manifest, held-out assessment, scheduler, "
            "baseline comparison, capacity profile, utility scorer, or runtime control "
            "is authorized.",
        )
    )
    payload.update(
        {
            "registry_status": "calibration_fit_diagnostics_retained",
            "v5_calibration_artifact_authored": True,
            "v5_calibration_fit_diagnostics_authored": True,
            "frozen_calibration_artifact_sha256": artifact_sha256,
            "frozen_calibration_fit_diagnostics_sha256": diagnostics_sha256,
            "next_authorized_artifact": "v5-final-evaluation-fixture-authoring",
        }
    )
    try:
        return CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload).model_dump(
            mode="json"
        )
    except ValidationError as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH,
            f"V5 fit-stage registry payload is invalid: {error}",
        ) from error


def _write_file_once(path: Path, payload: bytes) -> None:
    if path.exists():
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.DESTINATION_ALREADY_EXISTS,
            f"V5 write-once destination already exists: {path.name}",
        )
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _replace_file(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_contract(path: Path, contract_type, code: V5BoundedMonotoneBetaFitViolationCode):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return contract_type.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise V5BoundedMonotoneBetaFitError(
            code,
            f"unable to load V5 retained fit file {path.name}: {error}",
        ) from error


def _canonical_file_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _stable_diagnostic_float(value: float) -> float:
    """Quantize retained calibration-only diagnostics for cross-runtime stable bytes."""

    if not isfinite(value):
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.DIAGNOSTIC_SCHEMA_ERROR,
            "V5 retained diagnostics require finite numeric values",
        )
    try:
        return float(
            Decimal(str(value)).quantize(
                _DIAGNOSTIC_QUANTUM,
                rounding=ROUND_HALF_EVEN,
            )
        )
    except InvalidOperation as error:
        raise V5BoundedMonotoneBetaFitError(
            V5BoundedMonotoneBetaFitViolationCode.DIAGNOSTIC_SCHEMA_ERROR,
            "V5 retained diagnostics could not be normalized deterministically",
        ) from error


def _require_matching_float(*, actual: float, expected: float, message: str) -> None:
    if abs(actual - expected) > 1e-12:
        raise ValueError(message)
