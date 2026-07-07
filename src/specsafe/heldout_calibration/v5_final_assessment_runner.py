"""One-time execution of the V5 held-out calibration eligibility gate.

This module consumes only frozen V5 manifests, the retained calibration-only artifact, and
separate held-out outcomes. It never refits calibration, selects a threshold, invokes a scheduler,
compares policies, or authorizes runtime control.
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

from specsafe.contracts.models import WorkloadType
from specsafe.heldout_calibration.v5_final_assessment import (
    DEFAULT_V5_FINAL_ASSESSMENT_PROTOCOL,
    V5AdaptivePolicyResearchEligibility,
    V5ConservativeFallbackRecord,
    V5EvidenceRole,
    V5FinalAssessmentError,
    V5FinalAssessmentGateChecks,
    V5FinalAssessmentProtocol,
    V5FinalHeldOutAssessmentResult,
    V5FinalHeldOutAssessmentStatus,
    V5FinalPositionMetrics,
    V5FinalProbabilityMetrics,
    V5FinalWorkloadCoverage,
    V5FrozenEvidenceManifestReference,
    calculate_tie_aware_auroc,
    calculate_v5_bounded_monotone_beta_probability,
    canonical_v5_final_assessment_json,
    derive_v5_final_assessment_status,
    write_v5_final_assessment_result,
)
from specsafe.traces.bounded_monotone_beta_calibration_v5 import (
    V5BoundedMonotoneBetaFitError,
    V5BoundedMonotoneBetaFitResult,
    load_v5_bounded_monotone_beta_calibration_fit,
)
from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    load_calibration_successor_v5_scenario_family_registry,
)
from specsafe.traces.calibration_successor_v5_final_manifest import (
    CalibrationSuccessorV5FinalManifestedFixtureSet,
    CalibrationSuccessorV5FinalManifestError,
    load_calibration_successor_v5_final_manifested_fixture_set,
)
from specsafe.traces.calibration_successor_v5_manifest import (
    CalibrationSuccessorV5CalibrationManifest,
    CalibrationSuccessorV5ManifestError,
    load_calibration_successor_v5_calibration_manifest,
)

_ARTIFACT_FILENAME = "bounded_monotone_beta_calibration_artifact.json"
_DIAGNOSTICS_FILENAME = "bounded_monotone_beta_calibration_fit_diagnostics.json"
_RESULT_RELATIVE_PATH = (
    "evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json"
)
_EXPECTED_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(201, 237))
_EXPECTED_POSITION_INDICES = (1, 2, 3, 4)
_EXPECTED_WORKLOAD_TYPES = (
    WorkloadType.STRUCTURED_TEXT,
    WorkloadType.CODE,
    WorkloadType.OPEN_ENDED_CHAT,
)


class V5FinalHeldOutAssessmentExecutionErrorCode(StrEnum):
    """Machine-readable execution failures around frozen V5 evidence."""

    INVALID_PROTOCOL = "v5_final_heldout_assessment_invalid_protocol"
    FROZEN_PROVENANCE_MISMATCH = "v5_final_heldout_assessment_frozen_provenance_mismatch"
    ARTIFACT_LOAD_FAILURE = "v5_final_heldout_assessment_artifact_load_failure"
    OBSERVATION_ALIGNMENT_ERROR = "v5_final_heldout_assessment_observation_alignment_error"
    DESTINATION_ALREADY_EXISTS = "v5_final_heldout_assessment_destination_exists"
    REGISTRY_TRANSITION_ERROR = "v5_final_heldout_assessment_registry_transition_error"
    CANONICAL_SERIALIZATION_ERROR = "v5_final_heldout_assessment_canonical_serialization_error"


class V5FinalHeldOutAssessmentExecutionError(ValueError):
    """Raised when frozen V5 evidence cannot produce a trustworthy single result."""

    def __init__(
        self,
        code: V5FinalHeldOutAssessmentExecutionErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class _HeldOutObservation:
    """One post-hoc held-out observation, never exposed to a policy boundary."""

    case_id: str
    trace_id: str
    workload_type: WorkloadType
    block_position_index: int
    raw_probability: float
    calibrated_probability: float
    observed_acceptance: bool


def build_v5_final_heldout_calibration_result(
    fixture_root: Path,
    *,
    protocol: V5FinalAssessmentProtocol = DEFAULT_V5_FINAL_ASSESSMENT_PROTOCOL,
) -> V5FinalHeldOutAssessmentResult:
    """Score the retained V5 calibrator against frozen final evidence without persistence."""

    if type(protocol) is not V5FinalAssessmentProtocol:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.INVALID_PROTOCOL,
            "V5 held-out assessment requires the exact frozen assessment protocol",
        )

    root = fixture_root.resolve()
    final_fixture_set, calibration_manifest, registry = _load_frozen_inputs(root)
    fit = _load_frozen_calibration_evidence(root)
    _validate_cross_boundary_provenance(
        final_fixture_set=final_fixture_set,
        calibration_manifest=calibration_manifest,
        registry=registry,
        fit=fit,
    )

    observations = _collect_heldout_observations(final_fixture_set, fit)
    if len(observations) != protocol.expected_final_observation_count:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V5 held-out assessment must retain exactly 144 observations",
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
    workload_coverage = _build_workload_coverage(observations)
    brier_score_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_10_bin_improvement = raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
    auroc_delta = calibrated_metrics.auroc - raw_metrics.auroc

    checks = V5FinalAssessmentGateChecks(
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
        workload_coverage_passed=all(
            item.observation_count == protocol.expected_observations_per_workload
            for item in workload_coverage
        ),
        monotonicity_verification_passed=(
            fit.artifact.monotonicity_verification.verification_passed
        ),
        brier_improvement_passed=(
            brier_score_improvement >= protocol.minimum_brier_score_improvement
        ),
        ece_improvement_passed=(ece_10_bin_improvement >= protocol.minimum_ece_10_bin_improvement),
        ranking_safety_passed=auroc_delta >= -protocol.maximum_auroc_degradation,
        no_refit_passed=True,
        no_policy_execution_passed=True,
        write_once_precheck_passed=True,
        canonical_serialization_passed=True,
    )
    status = derive_v5_final_assessment_status(checks)
    is_pass = status is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    result = V5FinalHeldOutAssessmentResult(
        protocol=protocol,
        final_manifest=_build_final_manifest_reference(root, final_fixture_set),
        calibration_manifest=fit.artifact.calibration_manifest,
        final_evidence_index_sha256=_sha256(root / "final_evidence_index.json"),
        calibration_artifact_sha256=_sha256(root / _ARTIFACT_FILENAME),
        calibration_fit_report_sha256=_sha256(root / _DIAGNOSTICS_FILENAME),
        calibration_artifact=fit.artifact,
        assessment_case_ids=tuple(case.runtime_input.case_id for case in final_fixture_set.cases),
        assessment_trace_ids=tuple(case.runtime_input.trace_id for case in final_fixture_set.cases),
        case_count=len(final_fixture_set.cases),
        observation_count=len(observations),
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        position_metrics=position_metrics,
        workload_coverage=workload_coverage,
        brier_score_improvement=brier_score_improvement,
        ece_10_bin_improvement=ece_10_bin_improvement,
        auroc_delta=auroc_delta,
        gate_checks=checks,
        status=status,
        adaptive_policy_research_eligibility=(
            V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
            if is_pass
            else V5AdaptivePolicyResearchEligibility.BLOCKED
        ),
        fallback=None if is_pass else V5ConservativeFallbackRecord(),
        calibration_refit_performed=False,
        policy_or_replay_execution_performed=False,
    )
    _assert_canonical_serialization(result)
    return result


def run_v5_final_heldout_calibration_assessment_once(
    fixture_root: Path,
    destination: Path,
) -> tuple[V5FinalHeldOutAssessmentResult, Path]:
    """Write V5 held-out evidence once, then atomically advance its registry stage."""

    root = fixture_root.resolve()
    result_path = destination.resolve()
    if result_path.exists():
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V5 held-out assessment is write-once and already exists: {result_path}",
        )

    result = build_v5_final_heldout_calibration_result(root)
    try:
        persisted = write_v5_final_assessment_result(result, result_path)
        _advance_registry_after_assessment(root=root, result=result, result_path=persisted)
    except V5FinalAssessmentError as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.DESTINATION_ALREADY_EXISTS,
            str(error),
        ) from error
    except Exception:
        try:
            result_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return result, persisted


def _load_frozen_inputs(
    root: Path,
) -> tuple[
    CalibrationSuccessorV5FinalManifestedFixtureSet,
    CalibrationSuccessorV5CalibrationManifest,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
]:
    try:
        final_fixture_set = load_calibration_successor_v5_final_manifested_fixture_set(root)
        calibration_manifest = load_calibration_successor_v5_calibration_manifest(root)
        registry = load_calibration_successor_v5_scenario_family_registry(
            root / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=True,
        )
    except (
        CalibrationSuccessorV5FinalManifestError,
        CalibrationSuccessorV5ManifestError,
        CalibrationSuccessorV5RegistryLoadError,
    ) as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            f"unable to verify frozen V5 assessment inputs: {error}",
        ) from error
    if registry.registry_status != "final_evaluation_manifest_frozen":
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V5 held-out assessment requires the pre-assessment registry stage",
        )
    if registry.v5_final_heldout_calibration_assessment_authored:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V5 held-out assessment registry already records immutable assessment evidence",
        )
    return final_fixture_set, calibration_manifest, registry


def _load_frozen_calibration_evidence(root: Path) -> V5BoundedMonotoneBetaFitResult:
    try:
        return load_v5_bounded_monotone_beta_calibration_fit(root)
    except V5BoundedMonotoneBetaFitError as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.ARTIFACT_LOAD_FAILURE,
            f"unable to load retained V5 calibration evidence: {error}",
        ) from error


def _validate_cross_boundary_provenance(
    *,
    final_fixture_set: CalibrationSuccessorV5FinalManifestedFixtureSet,
    calibration_manifest: CalibrationSuccessorV5CalibrationManifest,
    registry: CalibrationSuccessorV5ScenarioFamilyRegistry,
    fit: V5BoundedMonotoneBetaFitResult,
) -> None:
    manifest = final_fixture_set.manifest
    if manifest.case_ids != _EXPECTED_CASE_IDS or manifest.observation_count != 144:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V5 final manifest must retain exactly CSV5-201 through CSV5-236 and 144 observations",
        )
    if registry.frozen_final_evaluation_manifest_sha256 is None:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V5 registry must retain the frozen final-manifest SHA-256",
        )
    if registry.final_evidence_index_sha256 != manifest.final_evidence_index_sha256:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V5 final manifest and registry must identify the same final evidence index",
        )
    if (
        fit.artifact.calibration_manifest.manifest_sha256
        != registry.frozen_calibration_manifest_sha256
    ):
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V5 artifact must identify the retained calibration manifest",
        )
    if fit.artifact.calibration_manifest.aggregate_sha256 != calibration_manifest.aggregate_sha256:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V5 artifact must identify the verified calibration-manifest aggregate",
        )
    if fit.diagnostics.artifact_sha256 != registry.frozen_calibration_artifact_sha256:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V5 diagnostics must identify the retained calibration artifact",
        )
    if fit.diagnostics.calibration_manifest != fit.artifact.calibration_manifest:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V5 diagnostics and artifact must identify the same calibration manifest",
        )


def _collect_heldout_observations(
    fixture_set: CalibrationSuccessorV5FinalManifestedFixtureSet,
    fit: V5BoundedMonotoneBetaFitResult,
) -> tuple[_HeldOutObservation, ...]:
    observations: list[_HeldOutObservation] = []
    for replay_case in fixture_set.cases:
        for context, outcome in zip(
            replay_case.runtime_input.contexts,
            replay_case.expected_outcomes.outcomes,
            strict=True,
        ):
            raw_probability = context.conditional_survival_confidence
            if not isfinite(raw_probability) or not 0.0 <= raw_probability <= 1.0:
                raise V5FinalHeldOutAssessmentExecutionError(
                    V5FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                    "V5 final raw confidence must be finite and inside the unit interval",
                )
            observations.append(
                _HeldOutObservation(
                    case_id=replay_case.runtime_input.case_id,
                    trace_id=replay_case.runtime_input.trace_id,
                    workload_type=context.workload_type,
                    block_position_index=context.block_position_index,
                    raw_probability=raw_probability,
                    calibrated_probability=calculate_v5_bounded_monotone_beta_probability(
                        raw_probability, fit.artifact.parameters
                    ),
                    observed_acceptance=outcome.observed_acceptance,
                )
            )
    return tuple(observations)


def _build_probability_metrics(
    *,
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
) -> V5FinalProbabilityMetrics:
    if len(probabilities) != len(labels) or len(probabilities) < 2:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V5 probability metrics require equally sized probability and label sequences",
        )
    if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in probabilities):
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V5 probability metrics require finite probabilities in the unit interval",
        )
    brier_score = sum(
        (probability - float(label)) ** 2
        for probability, label in zip(probabilities, labels, strict=True)
    ) / len(probabilities)
    return V5FinalProbabilityMetrics(
        brier_score=brier_score,
        ece_10_bin=_ece_10_bin(probabilities, labels),
        auroc=calculate_tie_aware_auroc(probabilities, labels),
    )


def _build_position_metrics(
    observations: tuple[_HeldOutObservation, ...],
) -> tuple[V5FinalPositionMetrics, ...]:
    metrics: list[V5FinalPositionMetrics] = []
    for position_index in _EXPECTED_POSITION_INDICES:
        grouped = tuple(
            item for item in observations if item.block_position_index == position_index
        )
        if len(grouped) != 36:
            raise V5FinalHeldOutAssessmentExecutionError(
                V5FinalHeldOutAssessmentExecutionErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                f"V5 final position {position_index} must retain exactly 36 observations",
            )
        raw_metrics = _build_probability_metrics(
            probabilities=tuple(item.raw_probability for item in grouped),
            labels=tuple(item.observed_acceptance for item in grouped),
        )
        calibrated_metrics = _build_probability_metrics(
            probabilities=tuple(item.calibrated_probability for item in grouped),
            labels=tuple(item.observed_acceptance for item in grouped),
        )
        metrics.append(
            V5FinalPositionMetrics(
                block_position_index=position_index,
                observation_count=len(grouped),
                raw_metrics=raw_metrics,
                calibrated_metrics=calibrated_metrics,
                brier_score_improvement=raw_metrics.brier_score - calibrated_metrics.brier_score,
                ece_10_bin_improvement=(raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin),
                auroc_delta=calibrated_metrics.auroc - raw_metrics.auroc,
            )
        )
    return tuple(metrics)


def _build_workload_coverage(
    observations: tuple[_HeldOutObservation, ...],
) -> tuple[V5FinalWorkloadCoverage, ...]:
    coverage: list[V5FinalWorkloadCoverage] = []
    for workload_type in _EXPECTED_WORKLOAD_TYPES:
        count = sum(item.workload_type is workload_type for item in observations)
        coverage.append(
            V5FinalWorkloadCoverage(
                workload_type=workload_type,
                observation_count=count,
            )
        )
    return tuple(coverage)


def _build_final_manifest_reference(
    root: Path,
    fixture_set: CalibrationSuccessorV5FinalManifestedFixtureSet,
) -> V5FrozenEvidenceManifestReference:
    manifest = fixture_set.manifest
    return V5FrozenEvidenceManifestReference(
        evidence_role=V5EvidenceRole.FINAL_EVALUATION,
        manifest_schema_version=manifest.schema_version,
        manifest_relative_path="final_evaluation_manifest.json",
        manifest_sha256=_sha256(root / "final_evaluation_manifest.json"),
        aggregate_sha256=manifest.aggregate_sha256,
        case_id_start="CSV5-201",
        case_id_end="CSV5-236",
        case_count=manifest.case_pair_count,
        observation_count=manifest.observation_count,
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
        weighted_gap += (len(member_indices) / sample_count) * abs(mean_probability - observed_rate)
    return weighted_gap


def _assert_canonical_serialization(result: V5FinalHeldOutAssessmentResult) -> None:
    try:
        encoded = canonical_v5_final_assessment_json(result)
        round_trip = V5FinalHeldOutAssessmentResult.model_validate_json(encoded)
        if canonical_v5_final_assessment_json(round_trip) != encoded:
            raise ValueError("canonical JSON bytes changed after schema round-trip")
    except (V5FinalAssessmentError, ValidationError, ValueError) as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.CANONICAL_SERIALIZATION_ERROR,
            f"V5 final assessment canonical serialization failed: {error}",
        ) from error


def _advance_registry_after_assessment(
    *,
    root: Path,
    result: V5FinalHeldOutAssessmentResult,
    result_path: Path,
) -> None:
    registry_path = root / "scenario_family_registry.json"
    try:
        payload: Any = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            f"unable to read the V5 pre-assessment registry: {error}",
        ) from error
    if not isinstance(payload, dict):
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V5 pre-assessment registry must be a JSON object",
        )
    required = {
        "registry_status": "final_evaluation_manifest_frozen",
        "v5_final_heldout_calibration_assessment_authored": False,
        "next_authorized_artifact": "v5-final-heldout-calibration-assessment",
    }
    for field_name, expected_value in required.items():
        if payload.get(field_name) != expected_value:
            raise V5FinalHeldOutAssessmentExecutionError(
                V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
                f"V5 pre-assessment registry must retain {field_name}={expected_value!r}",
            )
    project_root = root.parents[2]
    try:
        relative_path = result_path.resolve().relative_to(project_root).as_posix()
    except ValueError as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V5 assessment result must be retained under the project root",
        ) from error
    if relative_path != _RESULT_RELATIVE_PATH:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            "V5 assessment result must use the governed held-out evidence path",
        )
    gate_passed = (
        result.status is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    )
    exclusions = list(payload.get("explicit_exclusions", []))
    obsolete = {
        (
            "V5 final-evaluation manifest freeze does not author an assessment, "
            "baseline, or policy result."
        ),
        (
            "No V5 held-out assessment, scheduler, baseline comparison, capacity "
            "profile, utility scorer, or runtime control is authorized."
        ),
        (
            "No V5 scheduler, baseline comparison, capacity profile, utility scorer, "
            "or runtime control is authorized."
        ),
    }
    exclusions = [item for item in exclusions if item not in obsolete]
    new_exclusions = [
        "V5 held-out calibration assessment is write-once evidence.",
        (
            "V5 held-out calibration evidence is synthetic and does not establish "
            "production performance."
        ),
        "No V5 runtime control is authorized.",
        (
            (
                "V5 adaptive policy research is eligible only under controlled "
                "frozen-evidence evaluation; no scheduler, baseline comparison, "
                "capacity profile, or utility result is present."
            )
            if gate_passed
            else (
                "V5 policy, baseline, replay, and runtime-control work remain "
                "blocked pending remediation."
            )
        ),
    ]
    for item in new_exclusions:
        if item not in exclusions:
            exclusions.append(item)
    payload.update(
        {
            "registry_status": "final_heldout_calibration_assessed",
            "v5_final_heldout_calibration_assessment_authored": True,
            "final_heldout_calibration_assessment_sha256": _sha256(result_path),
            "final_heldout_calibration_assessment_relative_path": relative_path,
            "final_heldout_calibration_status": result.status.value,
            "explicit_exclusions": exclusions,
            "next_authorized_artifact": (
                "v5-calibrated-causal-load-aware-policy-foundation"
                if gate_passed
                else "v5-calibration-remediation-decision"
            ),
        }
    )
    try:
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            f"V5 post-assessment registry does not satisfy the typed contract: {error}",
        ) from error
    temporary_path = registry_path.with_name("scenario_family_registry.json.assessment-tmp")
    try:
        with temporary_path.open("xb") as output:
            output.write(_canonical_registry_bytes(payload))
        temporary_path.replace(registry_path)
    except OSError as error:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise V5FinalHeldOutAssessmentExecutionError(
            V5FinalHeldOutAssessmentExecutionErrorCode.REGISTRY_TRANSITION_ERROR,
            f"unable to advance V5 registry after held-out assessment: {error}",
        ) from error


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_registry_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
