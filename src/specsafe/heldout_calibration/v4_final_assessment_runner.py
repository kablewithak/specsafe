"""One-time execution of the V4 held-out calibration gate.

This module consumes only frozen V4 provenance, the already-fitted calibration artifact, and
separate held-out outcomes. It does not fit a calibrator, invoke a scheduler, compare baselines,
or authorize runtime control.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from specsafe.heldout_calibration.v4_final_assessment import (
    DEFAULT_V4_FINAL_ASSESSMENT_PROTOCOL,
    V4AdaptivePolicyResearchEligibility,
    V4ConservativeFallbackRecord,
    V4FinalAssessmentError,
    V4FinalAssessmentGateChecks,
    V4FinalAssessmentProtocol,
    V4FinalHeldOutAssessmentResult,
    V4FinalHeldOutAssessmentStatus,
    V4FinalPositionMetrics,
    V4FinalProbabilityMetrics,
    calculate_tie_aware_auroc,
    canonical_v4_final_assessment_json,
    derive_v4_final_assessment_status,
    write_v4_final_assessment_result,
)
from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4ScenarioFamilyRegistry,
    load_calibration_redesign_v4_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v4_final_manifest import (
    CalibrationRedesignV4FinalManifestedFixtureSet,
    load_calibration_redesign_v4_final_manifested_fixture_set,
)
from specsafe.traces.calibration_redesign_v4_manifest import (
    CalibrationRedesignV4CalibrationManifest,
    load_calibration_redesign_v4_calibration_manifest,
)
from specsafe.traces.regularized_isotonic_calibration_v4 import (
    RegularizedIsotonicCalibrationV4Artifact,
    RegularizedIsotonicCalibrationV4FitReport,
    RegularizedIsotonicCalibrationV4FitResult,
)

_ARTIFACT_RELATIVE_PATH = (
    "evidence/calibration/regularized-isotonic-calibration-v4/artifact.json"
)
_FIT_REPORT_RELATIVE_PATH = (
    "evidence/calibration/regularized-isotonic-calibration-v4/fit_report.json"
)
_RESULT_RELATIVE_PATH = (
    "evidence/heldout-calibration/v4-final-heldout-calibration-assessment-v1/result.json"
)
_EXPECTED_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(201, 237))
_EXPECTED_POSITION_INDICES = (1, 2, 3, 4)


class V4FinalHeldOutAssessmentExecutionErrorCode(StrEnum):
    """Machine-readable execution failures around the otherwise frozen result contract."""

    INVALID_PROTOCOL = "v4_final_heldout_assessment_invalid_protocol"
    FROZEN_PROVENANCE_MISMATCH = "v4_final_heldout_assessment_frozen_provenance_mismatch"
    ARTIFACT_SCHEMA_ERROR = "v4_final_heldout_assessment_artifact_schema_error"
    ARTIFACT_HASH_MISMATCH = "v4_final_heldout_assessment_artifact_hash_mismatch"
    OBSERVATION_ALIGNMENT_ERROR = "v4_final_heldout_assessment_observation_alignment_error"
    DESTINATION_ALREADY_EXISTS = "v4_final_heldout_assessment_destination_exists"
    REGISTRY_TRANSITION_ERROR = "v4_final_heldout_assessment_registry_transition_error"
    CANONICAL_SERIALIZATION_ERROR = "v4_final_heldout_assessment_canonical_serialization_error"


class V4FinalHeldOutAssessmentExecutionError(ValueError):
    """Raised when frozen V4 final evidence cannot produce a trustworthy result."""

    def __init__(
        self,
        code: V4FinalHeldOutAssessmentExecutionErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class _HeldOutObservation:
    """One post-hoc held-out observation, never exposed to a runtime policy."""

    case_id: str
    trace_id: str
    block_position_index: int
    raw_probability: float
    calibrated_probability: float
    observed_acceptance: bool


def _build_v4_final_heldout_calibration_result(
    fixture_root: Path,
    *,
    protocol: V4FinalAssessmentProtocol = DEFAULT_V4_FINAL_ASSESSMENT_PROTOCOL,
) -> V4FinalHeldOutAssessmentResult:
    """Score the frozen calibrator against frozen held-out evidence without persistence.

    Persistence belongs to :func:`run_v4_final_heldout_calibration_assessment_once`, which
    performs the destination precheck and registry transition around this deterministic result.
    """

    if type(protocol) is not V4FinalAssessmentProtocol:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.INVALID_PROTOCOL,
            "V4 held-out assessment requires the exact frozen assessment protocol",
        )

    root = fixture_root.resolve()
    final_fixture_set, calibration_manifest, registry = _load_frozen_inputs(root)
    artifact, fit_report = _load_frozen_calibration_evidence(root, registry)
    _validate_cross_boundary_provenance(
        final_fixture_set=final_fixture_set,
        calibration_manifest=calibration_manifest,
        registry=registry,
        artifact=artifact,
        fit_report=fit_report,
    )

    observations = _collect_heldout_observations(final_fixture_set, artifact)
    if len(observations) != protocol.expected_final_observation_count:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V4 held-out assessment must retain exactly 144 observations",
        )

    raw_metrics = _build_probability_metrics(
        probabilities=tuple(item.raw_probability for item in observations),
        labels=tuple(item.observed_acceptance for item in observations),
    )
    calibrated_metrics = _build_probability_metrics(
        probabilities=tuple(item.calibrated_probability for item in observations),
        labels=tuple(item.observed_acceptance for item in observations),
    )
    position_metrics = _build_position_metrics(observations)
    brier_score_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_10_bin_improvement = raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
    auroc_delta = calibrated_metrics.auroc - raw_metrics.auroc

    gate_checks = V4FinalAssessmentGateChecks(
        manifest_integrity_passed=True,
        provenance_alignment_passed=True,
        observation_coverage_passed=(
            len(final_fixture_set.cases) == protocol.expected_final_case_count
            and len(observations) == protocol.expected_final_observation_count
        ),
        per_position_coverage_passed=all(
            item.observation_count == protocol.expected_observations_per_position
            for item in position_metrics
        ),
        brier_improvement_passed=(
            brier_score_improvement >= protocol.minimum_brier_score_improvement
        ),
        ece_improvement_passed=(
            ece_10_bin_improvement >= protocol.minimum_ece_10_bin_improvement
        ),
        ranking_safety_passed=(
            calibrated_metrics.auroc
            >= raw_metrics.auroc - protocol.maximum_auroc_degradation
        ),
        no_refit_passed=True,
        no_policy_execution_passed=True,
        write_once_precheck_passed=True,
        canonical_serialization_passed=True,
    )
    status = derive_v4_final_assessment_status(gate_checks)
    fallback = (
        None
        if status is V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
        else V4ConservativeFallbackRecord()
    )
    result = V4FinalHeldOutAssessmentResult(
        protocol=protocol,
        fixture_set_id=final_fixture_set.manifest.fixture_set_id,
        fixture_set_version=final_fixture_set.manifest.fixture_set_version,
        final_manifest_aggregate_sha256=final_fixture_set.manifest.aggregate_sha256,
        final_evidence_index_sha256=final_fixture_set.manifest.final_evidence_index_sha256,
        calibration_registry_sha256=artifact.calibration_registry_sha256,
        calibration_manifest_sha256=artifact.calibration_manifest_sha256,
        calibration_manifest_aggregate_sha256=(
            artifact.calibration_manifest_aggregate_sha256
        ),
        calibration_artifact_sha256=registry.calibration_artifact_sha256,
        calibration_fit_report_sha256=registry.calibration_fit_report_sha256,
        calibration_artifact_id=artifact.artifact_id,
        calibration_artifact_version=artifact.artifact_version,
        assessment_case_ids=tuple(
            case.runtime_input.case_id for case in final_fixture_set.cases
        ),
        assessment_trace_ids=tuple(
            case.runtime_input.trace_id for case in final_fixture_set.cases
        ),
        case_count=len(final_fixture_set.cases),
        observation_count=len(observations),
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        position_metrics=position_metrics,
        brier_score_improvement=brier_score_improvement,
        ece_10_bin_improvement=ece_10_bin_improvement,
        auroc_delta=auroc_delta,
        gate_checks=gate_checks,
        status=status,
        adaptive_policy_research_eligibility=(
            V4AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
            if status
            is V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
            else V4AdaptivePolicyResearchEligibility.BLOCKED
        ),
        fallback=fallback,
        calibration_refit_performed=False,
        scheduler_or_policy_execution_performed=False,
    )
    _assert_canonical_serialization(result)
    return result


def run_v4_final_heldout_calibration_assessment_once(
    fixture_root: Path,
    destination: Path,
) -> tuple[V4FinalHeldOutAssessmentResult, Path]:
    """Write the one permitted held-out result, then atomically advance its registry stage."""

    resolved_root = fixture_root.resolve()
    resolved_destination = destination.resolve()
    if resolved_destination.exists():
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V4 held-out assessment is write-once and already exists: {resolved_destination}",
        )

    result = _build_v4_final_heldout_calibration_result(resolved_root)
    try:
        result_path = write_v4_final_assessment_result(result, resolved_destination)
        _advance_registry_after_assessment(
            root=resolved_root,
            result=result,
            result_path=result_path,
        )
    except V4FinalAssessmentError as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.DESTINATION_ALREADY_EXISTS,
            str(error),
        ) from error
    except Exception:
        try:
            resolved_destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return result, result_path


def _load_frozen_inputs(
    root: Path,
) -> tuple[
    CalibrationRedesignV4FinalManifestedFixtureSet,
    CalibrationRedesignV4CalibrationManifest,
    CalibrationRedesignV4ScenarioFamilyRegistry,
]:
    try:
        final_fixture_set = load_calibration_redesign_v4_final_manifested_fixture_set(root)
        calibration_manifest = load_calibration_redesign_v4_calibration_manifest(root)
        registry = load_calibration_redesign_v4_scenario_family_registry(
            root / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=True,
        )
    except ValueError as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            f"unable to verify frozen V4 assessment inputs: {error}",
        ) from error

    if registry.registry_status != "final_evaluation_manifest_frozen":
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V4 held-out assessment requires the pre-assessment registry stage",
        )
    if registry.v4_final_heldout_calibration_assessment_authored:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V4 held-out assessment registry already records immutable assessment evidence",
        )
    return final_fixture_set, calibration_manifest, registry


def _load_frozen_calibration_evidence(
    root: Path,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
) -> tuple[
    RegularizedIsotonicCalibrationV4Artifact,
    RegularizedIsotonicCalibrationV4FitReport,
]:
    project_root = root.parents[2]
    artifact_path = project_root / _ARTIFACT_RELATIVE_PATH
    report_path = project_root / _FIT_REPORT_RELATIVE_PATH
    try:
        artifact_bytes = artifact_path.read_bytes()
        report_bytes = report_path.read_bytes()
        artifact = RegularizedIsotonicCalibrationV4Artifact.model_validate_json(
            artifact_bytes
        )
        report = RegularizedIsotonicCalibrationV4FitReport.model_validate_json(report_bytes)
        RegularizedIsotonicCalibrationV4FitResult(artifact=artifact, report=report)
    except (OSError, ValidationError, ValueError) as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.ARTIFACT_SCHEMA_ERROR,
            f"unable to load frozen V4 calibration artifact or fit report: {error}",
        ) from error

    if _sha256(artifact_bytes) != registry.calibration_artifact_sha256:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.ARTIFACT_HASH_MISMATCH,
            "frozen V4 calibration artifact bytes do not match the active registry",
        )
    if _sha256(report_bytes) != registry.calibration_fit_report_sha256:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.ARTIFACT_HASH_MISMATCH,
            "frozen V4 calibration fit-report bytes do not match the active registry",
        )
    return artifact, report


def _validate_cross_boundary_provenance(
    *,
    final_fixture_set: CalibrationRedesignV4FinalManifestedFixtureSet,
    calibration_manifest: CalibrationRedesignV4CalibrationManifest,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
    artifact: RegularizedIsotonicCalibrationV4Artifact,
    fit_report: RegularizedIsotonicCalibrationV4FitReport,
) -> None:
    if final_fixture_set.manifest.case_ids != _EXPECTED_CASE_IDS:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V4 final manifest must retain exactly CRV4-201 through CRV4-236",
        )
    if final_fixture_set.manifest.observation_count != 144:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V4 final manifest must retain exactly 144 held-out observations",
        )
    if (
        final_fixture_set.manifest.frozen_final_evaluation_registry_sha256
        != registry.frozen_final_evaluation_registry_sha256
    ):
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 final manifest does not retain the frozen final-registry hash",
        )
    if (
        final_fixture_set.manifest.final_evidence_index_sha256
        != registry.final_evidence_index_sha256
    ):
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 final evidence index hash does not match the active registry",
        )
    if artifact.calibration_manifest_sha256 != registry.frozen_calibration_manifest_sha256:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 artifact does not retain the frozen calibration-manifest hash",
        )
    if artifact.calibration_registry_sha256 != registry.frozen_calibration_registry_sha256:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 artifact does not retain the frozen calibration-registry hash",
        )
    if artifact.calibration_manifest_aggregate_sha256 != calibration_manifest.aggregate_sha256:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 artifact does not match the verified calibration-manifest aggregate",
        )
    if fit_report.calibration_manifest_aggregate_sha256 != calibration_manifest.aggregate_sha256:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 fit report does not match the verified calibration-manifest aggregate",
        )
    if (
        artifact.fixture_set_id != final_fixture_set.manifest.fixture_set_id
        or artifact.fixture_set_version != final_fixture_set.manifest.fixture_set_version
        or fit_report.fixture_set_id != final_fixture_set.manifest.fixture_set_id
        or fit_report.fixture_set_version != final_fixture_set.manifest.fixture_set_version
    ):
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V4 assessment inputs disagree on fixture-set identity or version",
        )


def _collect_heldout_observations(
    fixture_set: CalibrationRedesignV4FinalManifestedFixtureSet,
    artifact: RegularizedIsotonicCalibrationV4Artifact,
) -> tuple[_HeldOutObservation, ...]:
    observations: list[_HeldOutObservation] = []
    for replay_case in fixture_set.cases:
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in replay_case.expected_outcomes.outcomes
        }
        for context in replay_case.runtime_input.contexts:
            key = (context.decode_round, context.block_position_index)
            outcome = outcomes_by_key.get(key)
            if outcome is None:
                raise V4FinalHeldOutAssessmentExecutionError(
                    V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                    (
                        "V4 final assessment is missing an outcome for "
                        f"{replay_case.runtime_input.case_id}"
                    ),
                )
            raw_probability = context.conditional_survival_confidence
            if not isfinite(raw_probability) or not 0.0 <= raw_probability <= 1.0:
                raise V4FinalHeldOutAssessmentExecutionError(
                    V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                    "V4 final raw confidence must be finite and inside the unit interval",
                )
            observations.append(
                _HeldOutObservation(
                    case_id=replay_case.runtime_input.case_id,
                    trace_id=replay_case.runtime_input.trace_id,
                    block_position_index=context.block_position_index,
                    raw_probability=raw_probability,
                    calibrated_probability=artifact.calibrate(raw_probability),
                    observed_acceptance=outcome.observed_acceptance,
                )
            )
    return tuple(observations)


def _build_position_metrics(
    observations: tuple[_HeldOutObservation, ...],
) -> tuple[V4FinalPositionMetrics, ...]:
    metrics: list[V4FinalPositionMetrics] = []
    for position_index in _EXPECTED_POSITION_INDICES:
        position_observations = tuple(
            item for item in observations if item.block_position_index == position_index
        )
        if len(position_observations) != 36:
            raise V4FinalHeldOutAssessmentExecutionError(
                V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                f"V4 final position {position_index} must retain exactly 36 observations",
            )
        raw_metrics = _build_probability_metrics(
            probabilities=tuple(item.raw_probability for item in position_observations),
            labels=tuple(item.observed_acceptance for item in position_observations),
        )
        calibrated_metrics = _build_probability_metrics(
            probabilities=tuple(
                item.calibrated_probability for item in position_observations
            ),
            labels=tuple(item.observed_acceptance for item in position_observations),
        )
        metrics.append(
            V4FinalPositionMetrics(
                block_position_index=position_index,
                observation_count=len(position_observations),
                raw_metrics=raw_metrics,
                calibrated_metrics=calibrated_metrics,
                brier_score_improvement=(
                    raw_metrics.brier_score - calibrated_metrics.brier_score
                ),
                ece_10_bin_improvement=(
                    raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
                ),
                auroc_delta=calibrated_metrics.auroc - raw_metrics.auroc,
            )
        )
    return tuple(metrics)


def _build_probability_metrics(
    *,
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
) -> V4FinalProbabilityMetrics:
    if len(probabilities) != len(labels) or len(probabilities) < 2:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V4 probability metrics require equally sized probability and label sequences",
        )
    if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in probabilities):
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V4 probability metrics require finite probabilities in the unit interval",
        )
    brier_score = sum(
        (probability - float(label)) ** 2
        for probability, label in zip(probabilities, labels, strict=True)
    ) / len(probabilities)
    return V4FinalProbabilityMetrics(
        brier_score=brier_score,
        ece_10_bin=_ece_10_bin(probabilities, labels),
        auroc=calculate_tie_aware_auroc(probabilities, labels),
    )


def _ece_10_bin(probabilities: tuple[float, ...], labels: tuple[bool, ...]) -> float:
    weighted_gap = 0.0
    sample_count = len(probabilities)
    for bin_index in range(10):
        lower_bound = bin_index / 10
        upper_bound = (bin_index + 1) / 10
        member_indices = tuple(
            index
            for index, probability in enumerate(probabilities)
            if lower_bound <= probability < upper_bound
            or (bin_index == 9 and lower_bound <= probability <= upper_bound)
        )
        if not member_indices:
            continue
        mean_probability = sum(probabilities[index] for index in member_indices) / len(
            member_indices
        )
        observed_rate = sum(labels[index] for index in member_indices) / len(member_indices)
        weighted_gap += (len(member_indices) / sample_count) * abs(
            mean_probability - observed_rate
        )
    return weighted_gap


def _assert_canonical_serialization(result: V4FinalHeldOutAssessmentResult) -> None:
    try:
        first_bytes = canonical_v4_final_assessment_json(result)
        round_trip = V4FinalHeldOutAssessmentResult.model_validate_json(first_bytes)
        if canonical_v4_final_assessment_json(round_trip) != first_bytes:
            raise ValueError("canonical JSON bytes changed after schema round-trip")
    except (V4FinalAssessmentError, ValidationError, ValueError) as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.CANONICAL_SERIALIZATION_ERROR,
            f"V4 final assessment canonical serialization failed: {error}",
        ) from error


def _advance_registry_after_assessment(
    *,
    root: Path,
    result: V4FinalHeldOutAssessmentResult,
    result_path: Path,
) -> None:
    registry_path = root / "scenario_family_registry.json"
    try:
        raw_bytes = registry_path.read_bytes()
        payload: Any = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            f"unable to read the V4 pre-assessment registry: {error}",
        ) from error
    if not isinstance(payload, dict):
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V4 pre-assessment registry must be a JSON object",
        )
    required_values = {
        "registry_status": "final_evaluation_manifest_frozen",
        "v4_final_heldout_calibration_assessment_authored": False,
        "next_authorized_artifact": "v4-final-heldout-calibration-assessment",
    }
    for field_name, expected_value in required_values.items():
        actual_value = payload.get(field_name, False if expected_value is False else None)
        if actual_value != expected_value:
            raise V4FinalHeldOutAssessmentExecutionError(
                V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
                f"V4 pre-assessment registry must retain {field_name}={expected_value!r}",
            )

    project_root = root.parents[2]
    try:
        relative_result_path = result_path.resolve().relative_to(project_root).as_posix()
    except ValueError as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V4 assessment result must be retained under the project root",
        ) from error
    if relative_result_path != _RESULT_RELATIVE_PATH:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V4 assessment result must use the governed held-out evidence path",
        )

    gate_passed = (
        result.status
        is V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
    )
    payload.update(
        {
            "registry_status": "final_heldout_calibration_assessed",
            "v4_final_heldout_calibration_assessment_authored": True,
            "final_heldout_calibration_assessment_sha256": _sha256(
                result_path.read_bytes()
            ),
            "final_heldout_calibration_assessment_relative_path": relative_result_path,
            "final_heldout_calibration_status": result.status.value,
            "next_authorized_artifact": (
                "v4-policy-and-baseline-comparison"
                if gate_passed
                else "v4-calibration-remediation-decision"
            ),
        }
    )
    obsolete_exclusions = {
        "No V4 final-evaluation held-out assessment or result is present.",
        "No V4 held-out calibration, policy, or runtime claim is made.",
        (
            "V4 final-evaluation manifest freeze does not author an assessment, "
            "baseline, or policy result."
        ),
    }
    exclusions = [
        item for item in payload.get("explicit_exclusions", []) if item not in obsolete_exclusions
    ]
    status_exclusion = (
        "V4 runtime control remains prohibited pending policy and baseline evidence."
        if gate_passed
        else (
            "V4 policy, baseline, replay, and runtime-control work remain "
            "blocked pending remediation."
        )
    )
    for exclusion in (
        "V4 held-out calibration assessment is write-once evidence.",
        "V4 held-out calibration evidence does not establish production performance.",
        status_exclusion,
    ):
        if exclusion not in exclusions:
            exclusions.append(exclusion)
    payload["explicit_exclusions"] = exclusions

    try:
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            f"V4 post-assessment registry does not satisfy the typed contract: {error}",
        ) from error

    temporary_path = registry_path.with_name("scenario_family_registry.json.assessment-tmp")
    try:
        with temporary_path.open("xb") as file_handle:
            file_handle.write(_pretty_json_bytes(payload))
        temporary_path.replace(registry_path)
    except OSError as error:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise V4FinalHeldOutAssessmentExecutionError(
            V4FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            f"unable to advance V4 registry after held-out assessment: {error}",
        ) from error


def _sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def _pretty_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
