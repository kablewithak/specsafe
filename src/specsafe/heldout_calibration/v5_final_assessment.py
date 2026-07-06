"""V5 calibration-eligibility contracts with no V5 evidence access.

This module deliberately contains only strict contracts, a pure bounded-monotone-beta
transform, deterministic monotonicity evidence, complete gate semantics, canonical
serialization, and write-once persistence boundaries. It does not define V5 fixtures,
a calibration fitter, final-evidence loading, scheduler logic, capacity profiles, utility
scoring, replay comparison, or runtime control.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Sequence
from enum import StrEnum
from math import exp, isclose, log
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import StrictContract, WorkloadType
from specsafe.metrics.ranking import (
    TieAwareAurocInputError,
)
from specsafe.metrics.ranking import (
    calculate_tie_aware_auroc as _calculate_tie_aware_auroc,
)

_ARTIFACT_SCHEMA_VERSION = "bounded-monotone-beta-calibration-artifact-v5"
_ARTIFACT_ID = "bounded-monotone-beta-calibration-v5"
_ARTIFACT_VERSION = "1.0.0"
_METHOD_FAMILY = "global_monotone_beta_calibration"
_OPTIMIZER_ID = "deterministic_projected_gradient_descent_v1"
_MONOTONICITY_VERIFICATION_ID = "bounded_monotone_beta_order_check_v1"
_ASSESSMENT_SCHEMA_VERSION = "v5-final-heldout-calibration-assessment-v1"
_ASSESSMENT_PROTOCOL_ID = "v5_final_heldout_calibration_assessment_protocol_v1"
_AUROC_CALCULATION_VERSION = "tie_aware_mann_whitney_v1"
_FIXTURE_SET_ID = "synthetic-calibration-successor-v5"
_FIXTURE_SET_VERSION = "1.0.0"
_EXPECTED_FINAL_CASE_COUNT = 36
_EXPECTED_FINAL_OBSERVATION_COUNT = 144
_EXPECTED_POSITION_COUNT = 4
_EXPECTED_OBSERVATIONS_PER_POSITION = 36
_EXPECTED_OBSERVATIONS_PER_WORKLOAD = 48
_REQUIRED_WORKLOAD_TYPES = (
    WorkloadType.STRUCTURED_TEXT,
    WorkloadType.CODE,
    WorkloadType.OPEN_ENDED_CHAT,
)
_ECE_BIN_COUNT = 10
_MINIMUM_BRIER_IMPROVEMENT = 0.005
_MINIMUM_ECE_IMPROVEMENT = 0.010
_MAXIMUM_AUROC_DEGRADATION = 0.001
_CLIPPING_EPSILON = 0.000001
_PARAMETER_MINIMUM = 0.25
_PARAMETER_MAXIMUM = 4.00
_INTERCEPT_MINIMUM = -4.00
_INTERCEPT_MAXIMUM = 4.00
_OBJECTIVE_REGULARIZATION_WEIGHT = 0.02
_LEARNING_RATE = 0.02
_MAXIMUM_ITERATIONS = 8000
_OBJECTIVE_TOLERANCE = 0.000000000001
_GRADIENT_NORM_TOLERANCE = 0.00000001
_FALLBACK_POLICY_ID = "fixed-short-1-v5"


class V5FinalAssessmentErrorCode(StrEnum):
    """Machine-readable failures for the V5 contract and persistence boundary."""

    INVALID_METRICS = "v5_final_assessment_invalid_metrics"
    INVALID_RESULT = "v5_final_assessment_invalid_result"
    INVALID_DESTINATION = "v5_final_assessment_invalid_destination"
    DESTINATION_ALREADY_EXISTS = "v5_final_assessment_destination_already_exists"
    INVALID_ASSESSMENT_BUILDER = "v5_final_assessment_invalid_builder"
    INVALID_MONOTONICITY_INPUT = "v5_final_assessment_invalid_monotonicity_input"


class V5FinalAssessmentError(ValueError):
    """Raised when the V5 boundary cannot produce trustworthy evidence."""

    def __init__(self, code: V5FinalAssessmentErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class V5EvidenceRole(StrEnum):
    """The two evidence roles V5 contracts may reference before fixture authoring."""

    CALIBRATION = "calibration"
    FINAL_EVALUATION = "final_evaluation"


class V5FinalHeldOutAssessmentStatus(StrEnum):
    """Predeclared V5 complete-gate outcome precedence."""

    PASSES_V5_CALIBRATION_ELIGIBILITY_GATE = "PASSES_V5_CALIBRATION_ELIGIBILITY_GATE"
    CALIBRATOR_REGRESSION = "CALIBRATOR_REGRESSION"
    RANKING_SAFETY_REGRESSION = "RANKING_SAFETY_REGRESSION"
    INSUFFICIENT_HELD_OUT_COVERAGE = "INSUFFICIENT_HELD_OUT_COVERAGE"
    INVALID_PROVENANCE = "INVALID_PROVENANCE"
    INCOMPLETE_GATE_EVIDENCE = "INCOMPLETE_GATE_EVIDENCE"
    WRITE_ONCE_DESTINATION_EXISTS = "WRITE_ONCE_DESTINATION_EXISTS"


class V5AdaptivePolicyResearchEligibility(StrEnum):
    """A V5 pass permits controlled policy research only, never runtime control."""

    ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH = "eligible_for_controlled_policy_research"
    BLOCKED = "blocked"


class V5ConservativeFallback(StrEnum):
    """Fallback action retained by every V5 non-passing result."""

    CONSERVATIVE_FALLBACK = "CONSERVATIVE_FALLBACK"


class V5BoundedMonotoneBetaCalibrationProtocol(StrictContract):
    """Fixed V5 method settings, selected before V5 evidence exists."""

    artifact_id: Literal["bounded-monotone-beta-calibration-v5"] = _ARTIFACT_ID
    artifact_version: Literal["1.0.0"] = _ARTIFACT_VERSION
    method_family: Literal["global_monotone_beta_calibration"] = _METHOD_FAMILY
    fit_split: Literal["calibration"] = "calibration"
    fit_data_role: Literal["calibration"] = "calibration"
    runtime_control_eligible: Literal[False] = False
    a_minimum: Literal[0.25] = _PARAMETER_MINIMUM
    a_maximum: Literal[4.0] = _PARAMETER_MAXIMUM
    b_minimum: Literal[0.25] = _PARAMETER_MINIMUM
    b_maximum: Literal[4.0] = _PARAMETER_MAXIMUM
    c_minimum: Literal[-4.0] = _INTERCEPT_MINIMUM
    c_maximum: Literal[4.0] = _INTERCEPT_MAXIMUM
    initial_a: Literal[1.0] = 1.0
    initial_b: Literal[1.0] = 1.0
    initial_c: Literal[0.0] = 0.0
    objective_regularization_weight: Literal[0.02] = _OBJECTIVE_REGULARIZATION_WEIGHT
    optimizer_id: Literal["deterministic_projected_gradient_descent_v1"] = _OPTIMIZER_ID
    learning_rate: Literal[0.02] = _LEARNING_RATE
    maximum_iterations: Literal[8000] = _MAXIMUM_ITERATIONS
    objective_tolerance: Literal[0.000000000001] = _OBJECTIVE_TOLERANCE
    gradient_norm_tolerance: Literal[0.00000001] = _GRADIENT_NORM_TOLERANCE
    confidence_clipping_epsilon: Literal[0.000001] = _CLIPPING_EPSILON
    equal_objective_tie_rule: Literal["retain_earlier_iteration"] = "retain_earlier_iteration"


DEFAULT_V5_BOUNDED_MONOTONE_BETA_CALIBRATION_PROTOCOL = V5BoundedMonotoneBetaCalibrationProtocol()


class V5FrozenEvidenceManifestReference(StrictContract):
    """Hash-addressed manifest identity without authoring a V5 fixture asset."""

    fixture_set_id: Literal["synthetic-calibration-successor-v5"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    evidence_role: V5EvidenceRole
    manifest_schema_version: str = Field(min_length=1, max_length=128)
    manifest_relative_path: str = Field(min_length=1, max_length=256)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_id_start: str = Field(min_length=1, max_length=32)
    case_id_end: str = Field(min_length=1, max_length=32)
    case_count: int = Field(ge=1)
    observation_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_v5_role_shape(self) -> V5FrozenEvidenceManifestReference:
        if (
            self.manifest_relative_path.startswith("/")
            or "\\" in self.manifest_relative_path
            or ".." in self.manifest_relative_path.split("/")
        ):
            raise ValueError("manifest_relative_path must be a safe relative POSIX path")
        expected = {
            V5EvidenceRole.CALIBRATION: ("CSV5-101", "CSV5-148", 48, 192),
            V5EvidenceRole.FINAL_EVALUATION: ("CSV5-201", "CSV5-236", 36, 144),
        }[self.evidence_role]
        actual = (
            self.case_id_start,
            self.case_id_end,
            self.case_count,
            self.observation_count,
        )
        if actual != expected:
            raise ValueError(
                "V5 manifest reference must retain the predeclared namespace and coverage "
                f"for {self.evidence_role.value} evidence"
            )
        return self


class V5BoundedMonotoneBetaParameters(StrictContract):
    """Globally shared bounded coefficients for the V5 monotone-beta transform."""

    a: float = Field(ge=_PARAMETER_MINIMUM, le=_PARAMETER_MAXIMUM)
    b: float = Field(ge=_PARAMETER_MINIMUM, le=_PARAMETER_MAXIMUM)
    c: float = Field(ge=_INTERCEPT_MINIMUM, le=_INTERCEPT_MAXIMUM)


class V5MonotonicityVerification(StrictContract):
    """Retained deterministic evidence that the frozen V5 artifact was checked for order safety."""

    verification_id: Literal["bounded_monotone_beta_order_check_v1"] = _MONOTONICITY_VERIFICATION_ID
    boundary_input_count: int = Field(ge=2)
    boundary_inputs_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_calibration_input_count: int = Field(ge=1)
    observed_calibration_inputs_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_strictly_increasing: bool
    observed_inputs_non_decreasing: bool
    verification_passed: bool

    @model_validator(mode="after")
    def validate_verification_semantics(self) -> V5MonotonicityVerification:
        expected = self.boundary_strictly_increasing and self.observed_inputs_non_decreasing
        if self.verification_passed is not expected:
            raise ValueError(
                "verification_passed must match retained boundary and observed-input checks"
            )
        return self


class V5BoundedMonotoneBetaCalibrationArtifact(StrictContract):
    """A post-fit V5 artifact contract; no instance is authored by this pre-fixture slice."""

    schema_version: Literal["bounded-monotone-beta-calibration-artifact-v5"] = (
        _ARTIFACT_SCHEMA_VERSION
    )
    protocol: V5BoundedMonotoneBetaCalibrationProtocol
    calibration_manifest: V5FrozenEvidenceManifestReference
    parameters: V5BoundedMonotoneBetaParameters
    monotonicity_verification: V5MonotonicityVerification
    fitting_completed: Literal[True] = True
    calibration_observation_count: Literal[192] = 192

    @model_validator(mode="after")
    def validate_artifact_provenance(self) -> V5BoundedMonotoneBetaCalibrationArtifact:
        if type(self.protocol) is not V5BoundedMonotoneBetaCalibrationProtocol:
            raise ValueError("V5 artifact requires the exact bounded-monotone-beta protocol")
        if self.calibration_manifest.evidence_role is not V5EvidenceRole.CALIBRATION:
            raise ValueError("V5 artifact may reference calibration evidence only")
        if not self.monotonicity_verification.verification_passed:
            raise ValueError("a frozen V5 artifact requires passing monotonicity verification")
        return self


class V5FinalAssessmentProtocol(StrictContract):
    """Frozen V5 complete-gate semantics that exist before V5 evidence authoring."""

    protocol_id: Literal["v5_final_heldout_calibration_assessment_protocol_v1"] = (
        _ASSESSMENT_PROTOCOL_ID
    )
    expected_final_case_count: Literal[36] = _EXPECTED_FINAL_CASE_COUNT
    expected_final_observation_count: Literal[144] = _EXPECTED_FINAL_OBSERVATION_COUNT
    expected_observations_per_position: Literal[36] = _EXPECTED_OBSERVATIONS_PER_POSITION
    expected_observations_per_workload: Literal[48] = _EXPECTED_OBSERVATIONS_PER_WORKLOAD
    fixed_ece_bin_count: Literal[10] = _ECE_BIN_COUNT
    minimum_brier_score_improvement: Literal[0.005] = _MINIMUM_BRIER_IMPROVEMENT
    minimum_ece_10_bin_improvement: Literal[0.01] = _MINIMUM_ECE_IMPROVEMENT
    maximum_auroc_degradation: Literal[0.001] = _MAXIMUM_AUROC_DEGRADATION
    auroc_calculation_version: Literal["tie_aware_mann_whitney_v1"] = _AUROC_CALCULATION_VERSION


DEFAULT_V5_FINAL_ASSESSMENT_PROTOCOL = V5FinalAssessmentProtocol()


class V5FinalAssessmentGateChecks(StrictContract):
    """Every V5 promotion condition retained as an inspectable boolean."""

    manifest_integrity_passed: bool
    provenance_alignment_passed: bool
    observation_coverage_passed: bool
    per_position_coverage_passed: bool
    workload_coverage_passed: bool
    monotonicity_verification_passed: bool
    brier_improvement_passed: bool
    ece_improvement_passed: bool
    ranking_safety_passed: bool
    no_refit_passed: bool
    no_policy_execution_passed: bool
    write_once_precheck_passed: bool
    canonical_serialization_passed: bool

    @property
    def all_passed(self) -> bool:
        """Whether every V5 complete-gate condition passed."""

        return all(
            (
                self.manifest_integrity_passed,
                self.provenance_alignment_passed,
                self.observation_coverage_passed,
                self.per_position_coverage_passed,
                self.workload_coverage_passed,
                self.monotonicity_verification_passed,
                self.brier_improvement_passed,
                self.ece_improvement_passed,
                self.ranking_safety_passed,
                self.no_refit_passed,
                self.no_policy_execution_passed,
                self.write_once_precheck_passed,
                self.canonical_serialization_passed,
            )
        )


class V5FinalProbabilityMetrics(StrictContract):
    """Aggregate or stratified probability evidence for the V5 final gate."""

    brier_score: float = Field(ge=0.0, le=1.0)
    ece_10_bin: float = Field(ge=0.0, le=1.0)
    auroc: float = Field(ge=0.0, le=1.0)


class V5FinalPositionMetrics(StrictContract):
    """Raw-versus-calibrated diagnostics for one candidate position."""

    block_position_index: Literal[1, 2, 3, 4]
    observation_count: int = Field(ge=0)
    raw_metrics: V5FinalProbabilityMetrics
    calibrated_metrics: V5FinalProbabilityMetrics
    brier_score_improvement: float
    ece_10_bin_improvement: float
    auroc_delta: float

    @model_validator(mode="after")
    def validate_metric_deltas(self) -> V5FinalPositionMetrics:
        _require_matching_float(
            actual=self.brier_score_improvement,
            expected=self.raw_metrics.brier_score - self.calibrated_metrics.brier_score,
            message="position brier_score_improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.ece_10_bin_improvement,
            expected=self.raw_metrics.ece_10_bin - self.calibrated_metrics.ece_10_bin,
            message="position ece_10_bin_improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.auroc_delta,
            expected=self.calibrated_metrics.auroc - self.raw_metrics.auroc,
            message="position auroc_delta must match retained metrics",
        )
        return self


class V5FinalWorkloadCoverage(StrictContract):
    """Coverage retained for one required workload class without adding a policy metric."""

    workload_type: WorkloadType
    observation_count: int = Field(ge=0)


class V5ConservativeFallbackRecord(StrictContract):
    """The exact bounded fallback required whenever the V5 gate does not pass."""

    action: Literal["CONSERVATIVE_FALLBACK"] = V5ConservativeFallback.CONSERVATIVE_FALLBACK
    fallback_policy_id: Literal["fixed-short-1-v5"] = _FALLBACK_POLICY_ID
    maximum_verification_length: Literal[1] = 1
    reason: Literal["complete_v5_calibration_eligibility_gate_not_passed"] = (
        "complete_v5_calibration_eligibility_gate_not_passed"
    )


class V5FinalHeldOutAssessmentResult(StrictContract):
    """Complete write-once V5 calibration-gate evidence with no runtime promotion."""

    schema_version: Literal["v5-final-heldout-calibration-assessment-v1"] = (
        _ASSESSMENT_SCHEMA_VERSION
    )
    protocol: V5FinalAssessmentProtocol
    fixture_set_id: Literal["synthetic-calibration-successor-v5"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    final_manifest: V5FrozenEvidenceManifestReference
    calibration_manifest: V5FrozenEvidenceManifestReference
    final_evidence_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_fit_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact: V5BoundedMonotoneBetaCalibrationArtifact
    assessment_case_ids: tuple[str, ...] = Field(min_length=1)
    assessment_trace_ids: tuple[str, ...] = Field(min_length=1)
    case_count: int = Field(ge=0)
    observation_count: int = Field(ge=0)
    raw_metrics: V5FinalProbabilityMetrics
    calibrated_metrics: V5FinalProbabilityMetrics
    position_metrics: tuple[V5FinalPositionMetrics, ...]
    workload_coverage: tuple[V5FinalWorkloadCoverage, ...]
    brier_score_improvement: float
    ece_10_bin_improvement: float
    auroc_delta: float
    gate_checks: V5FinalAssessmentGateChecks
    status: V5FinalHeldOutAssessmentStatus
    adaptive_policy_research_eligibility: V5AdaptivePolicyResearchEligibility
    fallback: V5ConservativeFallbackRecord | None = None
    runtime_control_eligible: Literal[False] = False
    calibration_refit_performed: bool
    policy_or_replay_execution_performed: bool
    write_mode: Literal["write_once"] = "write_once"

    @model_validator(mode="after")
    def validate_complete_gate_semantics(self) -> V5FinalHeldOutAssessmentResult:
        if type(self.protocol) is not V5FinalAssessmentProtocol:
            raise ValueError("V5 result requires the exact V5 final assessment protocol")
        if type(self.final_manifest) is not V5FrozenEvidenceManifestReference:
            raise ValueError("V5 result requires the exact V5 final manifest contract")
        if type(self.calibration_manifest) is not V5FrozenEvidenceManifestReference:
            raise ValueError("V5 result requires the exact V5 calibration manifest contract")
        if type(self.calibration_artifact) is not V5BoundedMonotoneBetaCalibrationArtifact:
            raise ValueError("V5 result requires the exact V5 bounded-monotone-beta artifact")
        if self.final_manifest.evidence_role is not V5EvidenceRole.FINAL_EVALUATION:
            raise ValueError("V5 result must identify V5 final-evaluation evidence")
        if self.calibration_manifest.evidence_role is not V5EvidenceRole.CALIBRATION:
            raise ValueError("V5 result must identify V5 calibration evidence")
        if self.calibration_artifact.calibration_manifest != self.calibration_manifest:
            raise ValueError("V5 artifact must identify the same retained calibration manifest")
        if self.case_count != len(self.assessment_case_ids):
            raise ValueError("case_count must match retained assessment_case_ids")
        if self.case_count != len(self.assessment_trace_ids):
            raise ValueError("case_count must match retained assessment_trace_ids")
        if len(set(self.assessment_case_ids)) != self.case_count:
            raise ValueError("assessment_case_ids must be unique")
        if len(set(self.assessment_trace_ids)) != self.case_count:
            raise ValueError("assessment_trace_ids must be unique")

        _require_matching_float(
            actual=self.brier_score_improvement,
            expected=self.raw_metrics.brier_score - self.calibrated_metrics.brier_score,
            message="aggregate brier_score_improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.ece_10_bin_improvement,
            expected=self.raw_metrics.ece_10_bin - self.calibrated_metrics.ece_10_bin,
            message="aggregate ece_10_bin_improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.auroc_delta,
            expected=self.calibrated_metrics.auroc - self.raw_metrics.auroc,
            message="aggregate auroc_delta must match retained metrics",
        )

        expected_positions = (1, 2, 3, 4)
        actual_positions = tuple(item.block_position_index for item in self.position_metrics)
        if actual_positions != expected_positions:
            raise ValueError("position_metrics must retain positions 1 through 4 in order")
        expected_workloads = _REQUIRED_WORKLOAD_TYPES
        actual_workloads = tuple(item.workload_type for item in self.workload_coverage)
        if actual_workloads != expected_workloads:
            raise ValueError("workload_coverage must retain all required workload classes in order")

        observed_coverage = (
            self.case_count == self.protocol.expected_final_case_count
            and self.observation_count == self.protocol.expected_final_observation_count
        )
        if sum(item.observation_count for item in self.position_metrics) != self.observation_count:
            raise ValueError("position metrics must sum to observation_count")
        if sum(item.observation_count for item in self.workload_coverage) != self.observation_count:
            raise ValueError("workload coverage must sum to observation_count")
        position_coverage = all(
            item.observation_count == self.protocol.expected_observations_per_position
            for item in self.position_metrics
        )
        workload_coverage = all(
            item.observation_count == self.protocol.expected_observations_per_workload
            for item in self.workload_coverage
        )
        brier_improvement = (
            self.brier_score_improvement >= self.protocol.minimum_brier_score_improvement
        )
        ece_improvement = (
            self.ece_10_bin_improvement >= self.protocol.minimum_ece_10_bin_improvement
        )
        ranking_safety = self.auroc_delta >= -self.protocol.maximum_auroc_degradation
        derived_checks = {
            "observation_coverage_passed": observed_coverage,
            "per_position_coverage_passed": position_coverage,
            "workload_coverage_passed": workload_coverage,
            "monotonicity_verification_passed": (
                self.calibration_artifact.monotonicity_verification.verification_passed
            ),
            "brier_improvement_passed": brier_improvement,
            "ece_improvement_passed": ece_improvement,
            "ranking_safety_passed": ranking_safety,
            "no_refit_passed": not self.calibration_refit_performed,
            "no_policy_execution_passed": not self.policy_or_replay_execution_performed,
        }
        for name, expected in derived_checks.items():
            if getattr(self.gate_checks, name) is not expected:
                raise ValueError(f"{name} must match retained V5 result evidence")

        expected_status = derive_v5_final_assessment_status(self.gate_checks)
        if self.status is not expected_status:
            raise ValueError("status must match V5 complete-gate precedence")
        is_pass = (
            self.status is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
        )
        expected_eligibility = (
            V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
            if is_pass
            else V5AdaptivePolicyResearchEligibility.BLOCKED
        )
        if self.adaptive_policy_research_eligibility is not expected_eligibility:
            raise ValueError("adaptive policy eligibility must match V5 final status")
        if is_pass and self.fallback is not None:
            raise ValueError("a passing V5 gate cannot retain a conservative fallback")
        if not is_pass and self.fallback is None:
            raise ValueError("a non-passing V5 gate requires the conservative fallback")
        return self


def calculate_v5_bounded_monotone_beta_probability(
    raw_confidence: float,
    parameters: V5BoundedMonotoneBetaParameters,
) -> float:
    """Apply the predeclared V5 transform without fitting, artifact I/O, or evidence access."""

    if type(parameters) is not V5BoundedMonotoneBetaParameters:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_METRICS,
            "V5 bounded-monotone-beta calibration requires the exact parameter contract",
        )
    if not 0.0 <= raw_confidence <= 1.0:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_METRICS,
            "raw_confidence must be within [0.0, 1.0]",
        )
    clipped = min(max(raw_confidence, _CLIPPING_EPSILON), 1.0 - _CLIPPING_EPSILON)
    logit = parameters.a * log(clipped) - parameters.b * log(1.0 - clipped) + parameters.c
    if logit >= 0.0:
        return 1.0 / (1.0 + exp(-logit))
    positive_exp = exp(logit)
    return positive_exp / (1.0 + positive_exp)


def verify_v5_bounded_monotone_beta_monotonicity(
    parameters: V5BoundedMonotoneBetaParameters,
    boundary_inputs: Iterable[float],
    observed_calibration_inputs: Iterable[float],
) -> V5MonotonicityVerification:
    """Create deterministic, minimized monotonicity evidence for a frozen V5 artifact."""

    boundary = _sorted_unique_probability_inputs(boundary_inputs)
    observed = _sorted_unique_probability_inputs(observed_calibration_inputs)
    if len(boundary) < 2:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_MONOTONICITY_INPUT,
            "V5 monotonicity verification requires at least two unique boundary inputs",
        )
    if not observed:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_MONOTONICITY_INPUT,
            "V5 monotonicity verification requires at least one observed calibration input",
        )
    boundary_outputs = tuple(
        calculate_v5_bounded_monotone_beta_probability(value, parameters) for value in boundary
    )
    observed_outputs = tuple(
        calculate_v5_bounded_monotone_beta_probability(value, parameters) for value in observed
    )
    boundary_increasing = _strictly_increasing(boundary_outputs)
    observed_non_decreasing = _non_decreasing(observed_outputs)
    return V5MonotonicityVerification(
        boundary_input_count=len(boundary),
        boundary_inputs_sha256=_canonical_probability_input_hash(boundary),
        observed_calibration_input_count=len(observed),
        observed_calibration_inputs_sha256=_canonical_probability_input_hash(observed),
        boundary_strictly_increasing=boundary_increasing,
        observed_inputs_non_decreasing=observed_non_decreasing,
        verification_passed=boundary_increasing and observed_non_decreasing,
    )


def derive_v5_final_assessment_status(
    gate_checks: V5FinalAssessmentGateChecks,
) -> V5FinalHeldOutAssessmentStatus:
    """Apply ADR-0018 status precedence without reading V5 evidence assets."""

    if not (gate_checks.manifest_integrity_passed and gate_checks.provenance_alignment_passed):
        return V5FinalHeldOutAssessmentStatus.INVALID_PROVENANCE
    if not gate_checks.write_once_precheck_passed:
        return V5FinalHeldOutAssessmentStatus.WRITE_ONCE_DESTINATION_EXISTS
    if not (
        gate_checks.no_refit_passed
        and gate_checks.no_policy_execution_passed
        and gate_checks.canonical_serialization_passed
    ):
        return V5FinalHeldOutAssessmentStatus.INCOMPLETE_GATE_EVIDENCE
    if not (
        gate_checks.observation_coverage_passed
        and gate_checks.per_position_coverage_passed
        and gate_checks.workload_coverage_passed
    ):
        return V5FinalHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_COVERAGE
    if not gate_checks.ranking_safety_passed:
        return V5FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    if not (
        gate_checks.monotonicity_verification_passed
        and gate_checks.brier_improvement_passed
        and gate_checks.ece_improvement_passed
    ):
        return V5FinalHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    return V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE


def calculate_tie_aware_auroc(
    probabilities: Sequence[float],
    labels: Sequence[bool],
) -> float:
    """Calculate AUROC while retaining the V5 assessment error contract."""

    try:
        return _calculate_tie_aware_auroc(probabilities, labels)
    except TieAwareAurocInputError as error:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_METRICS,
            str(error),
        ) from error


def canonical_v5_final_assessment_json(result: V5FinalHeldOutAssessmentResult) -> bytes:
    """Return stable JSON bytes for an already-validated V5 assessment result."""

    if type(result) is not V5FinalHeldOutAssessmentResult:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_RESULT,
            "canonical V5 output requires the exact V5 final result contract",
        )
    return (
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def write_v5_final_assessment_result(
    result: V5FinalHeldOutAssessmentResult,
    destination: Path,
) -> Path:
    """Persist a validated V5 result once, without an overwrite path."""

    if destination.suffix != ".json":
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_DESTINATION,
            "V5 final assessment destination must use a .json suffix",
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as output:
            output.write(canonical_v5_final_assessment_json(result))
    except FileExistsError as error:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V5 final assessment is write-once and already exists: {destination}",
        ) from error
    except OSError as error:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_DESTINATION,
            f"unable to persist V5 final assessment: {destination}",
        ) from error
    return destination


def run_v5_final_assessment_once(
    destination: Path,
    assessment_builder: Callable[[], V5FinalHeldOutAssessmentResult],
) -> tuple[V5FinalHeldOutAssessmentResult, Path]:
    """Enforce write-once precheck before any future V5 loader or scorer is invoked."""

    if destination.exists():
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V5 final assessment is write-once and already exists: {destination}",
        )
    if not callable(assessment_builder):
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_ASSESSMENT_BUILDER,
            "V5 final assessment requires a callable result builder",
        )
    result = assessment_builder()
    if type(result) is not V5FinalHeldOutAssessmentResult:
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_RESULT,
            "V5 final assessment builder must return the exact V5 result contract",
        )
    return result, write_v5_final_assessment_result(result, destination)


def _canonical_probability_input_hash(inputs: Sequence[float]) -> str:
    payload = json.dumps(tuple(inputs), ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sorted_unique_probability_inputs(values: Iterable[float]) -> tuple[float, ...]:
    values_tuple = tuple(values)
    if any(not 0.0 <= value <= 1.0 for value in values_tuple):
        raise V5FinalAssessmentError(
            V5FinalAssessmentErrorCode.INVALID_MONOTONICITY_INPUT,
            "V5 monotonicity inputs must all be within [0.0, 1.0]",
        )
    return tuple(sorted(set(values_tuple)))


def _strictly_increasing(values: Sequence[float]) -> bool:
    return all(right > left for left, right in zip(values, values[1:]))


def _non_decreasing(values: Sequence[float]) -> bool:
    return all(right >= left for left, right in zip(values, values[1:]))


def _require_matching_float(*, actual: float, expected: float, message: str) -> None:
    if not isclose(actual, expected, abs_tol=1e-12, rel_tol=0.0):
        raise ValueError(message)
