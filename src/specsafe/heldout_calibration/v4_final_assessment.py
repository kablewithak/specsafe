"""V4 complete held-out calibration-gate contracts with no V4 evidence access.

This module deliberately contains only typed contracts, deterministic metric primitives, canonical
serialization, and write-once persistence boundaries. It does not define a V4 fixture loader,
calibrator fitter, scheduler, baseline, capacity model, or replay scorer.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from enum import StrEnum
from math import isclose
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import StrictContract
from specsafe.metrics.ranking import (
    TieAwareAurocInputError,
)
from specsafe.metrics.ranking import (
    calculate_tie_aware_auroc as _calculate_tie_aware_auroc,
)

_ASSESSMENT_SCHEMA_VERSION = "v4-final-heldout-calibration-assessment-v1"
_ASSESSMENT_PROTOCOL_ID = "v4_final_heldout_calibration_assessment_protocol_v1"
_AUROC_CALCULATION_VERSION = "tie_aware_mann_whitney_v1"
_EXPECTED_FINAL_CASE_COUNT = 36
_EXPECTED_FINAL_OBSERVATION_COUNT = 144
_EXPECTED_POSITION_COUNT = 4
_EXPECTED_OBSERVATIONS_PER_POSITION = 36
_ECE_BIN_COUNT = 10
_MINIMUM_BRIER_IMPROVEMENT = 0.010
_MINIMUM_ECE_IMPROVEMENT = 0.020
_MAXIMUM_AUROC_DEGRADATION = 0.002
_UNSAFE_RETROSPECTIVE_CONTROL_ID = "unsafe_retrospective_oracle_v4"


class V4FinalAssessmentErrorCode(StrEnum):
    """Machine-readable contract and persistence failures for the V4 assessment boundary."""

    INVALID_METRICS = "v4_final_assessment_invalid_metrics"
    INVALID_RESULT = "v4_final_assessment_invalid_result"
    INVALID_DESTINATION = "v4_final_assessment_invalid_destination"
    DESTINATION_ALREADY_EXISTS = "v4_final_assessment_destination_already_exists"
    INVALID_ASSESSMENT_BUILDER = "v4_final_assessment_invalid_builder"
    UNSAFE_RETROSPECTIVE_CONTROL_REJECTED = (
        "v4_final_assessment_unsafe_retrospective_control_rejected"
    )


class V4FinalAssessmentError(ValueError):
    """Raised when the V4 assessment boundary cannot produce trustworthy evidence."""

    def __init__(self, code: V4FinalAssessmentErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class V4FinalHeldOutAssessmentStatus(StrEnum):
    """Predeclared status precedence for the complete V4 calibration gate."""

    PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE = "PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE"
    CALIBRATOR_REGRESSION = "CALIBRATOR_REGRESSION"
    INSUFFICIENT_HELD_OUT_COVERAGE = "INSUFFICIENT_HELD_OUT_COVERAGE"
    RANKING_SAFETY_REGRESSION = "RANKING_SAFETY_REGRESSION"
    INCOMPLETE_GATE_EVIDENCE = "INCOMPLETE_GATE_EVIDENCE"
    INVALID_PROVENANCE = "INVALID_PROVENANCE"


class V4AdaptivePolicyResearchEligibility(StrEnum):
    """A complete calibration pass permits research only, never runtime control."""

    ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH = "eligible_for_controlled_policy_research"
    BLOCKED = "blocked"


class V4ConservativeFallback(StrEnum):
    """Fallback action required by every non-passing V4 calibration result."""

    CONSERVATIVE_FALLBACK = "CONSERVATIVE_FALLBACK"


class V4FinalAssessmentProtocol(StrictContract):
    """Frozen V4 final-gate semantics that must exist before V4 evidence authoring."""

    protocol_id: Literal["v4_final_heldout_calibration_assessment_protocol_v1"] = (
        _ASSESSMENT_PROTOCOL_ID
    )
    expected_final_case_count: Literal[36] = _EXPECTED_FINAL_CASE_COUNT
    expected_final_observation_count: Literal[144] = _EXPECTED_FINAL_OBSERVATION_COUNT
    expected_observations_per_position: Literal[36] = _EXPECTED_OBSERVATIONS_PER_POSITION
    fixed_ece_bin_count: Literal[10] = _ECE_BIN_COUNT
    minimum_brier_score_improvement: Literal[0.01] = _MINIMUM_BRIER_IMPROVEMENT
    minimum_ece_10_bin_improvement: Literal[0.02] = _MINIMUM_ECE_IMPROVEMENT
    maximum_auroc_degradation: Literal[0.002] = _MAXIMUM_AUROC_DEGRADATION
    auroc_calculation_version: Literal["tie_aware_mann_whitney_v1"] = _AUROC_CALCULATION_VERSION


DEFAULT_V4_FINAL_ASSESSMENT_PROTOCOL = V4FinalAssessmentProtocol()


class V4FinalAssessmentGateChecks(StrictContract):
    """Every promotion condition retained as an explicit, inspectable gate boolean."""

    manifest_integrity_passed: bool
    provenance_alignment_passed: bool
    observation_coverage_passed: bool
    per_position_coverage_passed: bool
    brier_improvement_passed: bool
    ece_improvement_passed: bool
    ranking_safety_passed: bool
    no_refit_passed: bool
    no_policy_execution_passed: bool
    write_once_precheck_passed: bool
    canonical_serialization_passed: bool

    @property
    def all_passed(self) -> bool:
        """Whether every predeclared V4 calibration-gate requirement passed."""

        return all(
            (
                self.manifest_integrity_passed,
                self.provenance_alignment_passed,
                self.observation_coverage_passed,
                self.per_position_coverage_passed,
                self.brier_improvement_passed,
                self.ece_improvement_passed,
                self.ranking_safety_passed,
                self.no_refit_passed,
                self.no_policy_execution_passed,
                self.write_once_precheck_passed,
                self.canonical_serialization_passed,
            )
        )


class V4FinalProbabilityMetrics(StrictContract):
    """Complete aggregate or per-position probability evidence for the V4 gate."""

    brier_score: float = Field(ge=0.0, le=1.0)
    ece_10_bin: float = Field(ge=0.0, le=1.0)
    auroc: float = Field(ge=0.0, le=1.0)


class V4FinalPositionMetrics(StrictContract):
    """Complete raw-versus-calibrated diagnostics for one candidate position."""

    block_position_index: Literal[1, 2, 3, 4]
    observation_count: int = Field(ge=0)
    raw_metrics: V4FinalProbabilityMetrics
    calibrated_metrics: V4FinalProbabilityMetrics
    brier_score_improvement: float
    ece_10_bin_improvement: float
    auroc_delta: float

    @model_validator(mode="after")
    def validate_metric_deltas(self) -> V4FinalPositionMetrics:
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


class V4ConservativeFallbackRecord(StrictContract):
    """The exact bounded fallback required whenever the complete V4 gate does not pass."""

    action: Literal["CONSERVATIVE_FALLBACK"] = V4ConservativeFallback.CONSERVATIVE_FALLBACK
    fallback_policy_id: Literal["fixed_short_1"] = "fixed_short_1"
    reason: Literal["complete_v4_calibration_gate_not_passed"] = (
        "complete_v4_calibration_gate_not_passed"
    )


class V4UnsafeRetrospectiveControlRejection(StrictContract):
    """An explicit invalid label for the evaluation-only unsafe retrospective control."""

    policy_id: Literal["unsafe_retrospective_oracle_v4"] = _UNSAFE_RETROSPECTIVE_CONTROL_ID
    classification: Literal["test_only_invalid_control"] = "test_only_invalid_control"
    result_label: Literal["INVALID_CAUSAL_COMPARISON"] = "INVALID_CAUSAL_COMPARISON"
    admitted_to_valid_baseline_comparison: Literal[False] = False


class V4FinalHeldOutAssessmentResult(StrictContract):
    """Complete, write-once V4 calibration-gate evidence with no runtime promotion."""

    schema_version: Literal["v4-final-heldout-calibration-assessment-v1"] = (
        _ASSESSMENT_SCHEMA_VERSION
    )
    protocol: V4FinalAssessmentProtocol
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    final_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_fit_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_id: Literal["regularized-isotonic-calibration-v4"]
    calibration_artifact_version: Literal["1.0.0"]
    assessment_case_ids: tuple[str, ...]
    assessment_trace_ids: tuple[str, ...]
    case_count: int = Field(ge=0)
    observation_count: int = Field(ge=0)
    raw_metrics: V4FinalProbabilityMetrics
    calibrated_metrics: V4FinalProbabilityMetrics
    position_metrics: tuple[V4FinalPositionMetrics, ...]
    brier_score_improvement: float
    ece_10_bin_improvement: float
    auroc_delta: float
    gate_checks: V4FinalAssessmentGateChecks
    status: V4FinalHeldOutAssessmentStatus
    adaptive_policy_research_eligibility: V4AdaptivePolicyResearchEligibility
    fallback: V4ConservativeFallbackRecord | None = None
    runtime_control_eligible: Literal[False] = False
    calibration_refit_performed: bool
    scheduler_or_policy_execution_performed: bool
    write_mode: Literal["write_once"] = "write_once"

    @model_validator(mode="after")
    def validate_complete_gate_semantics(self) -> V4FinalHeldOutAssessmentResult:
        if type(self.protocol) is not V4FinalAssessmentProtocol:
            raise ValueError("V4 result requires the exact frozen V4 assessment protocol")
        if self.case_count != len(self.assessment_case_ids):
            raise ValueError("case_count must match assessment_case_ids")
        if self.case_count != len(self.assessment_trace_ids):
            raise ValueError("case_count must match assessment_trace_ids")
        if len(set(self.assessment_case_ids)) != self.case_count:
            raise ValueError("assessment_case_ids must be unique")
        if len(set(self.assessment_trace_ids)) != self.case_count:
            raise ValueError("assessment_trace_ids must be unique")
        if any(not case_id.startswith("CRV4-") for case_id in self.assessment_case_ids):
            raise ValueError("assessment_case_ids must use the CRV4 namespace")

        expected_positions = tuple(range(1, _EXPECTED_POSITION_COUNT + 1))
        actual_positions = tuple(item.block_position_index for item in self.position_metrics)
        if actual_positions != expected_positions:
            raise ValueError("position_metrics must cover positions one through four in order")
        if sum(item.observation_count for item in self.position_metrics) != self.observation_count:
            raise ValueError("position metric observations must sum to observation_count")

        _require_matching_float(
            actual=self.brier_score_improvement,
            expected=self.raw_metrics.brier_score - self.calibrated_metrics.brier_score,
            message="brier_score_improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.ece_10_bin_improvement,
            expected=self.raw_metrics.ece_10_bin - self.calibrated_metrics.ece_10_bin,
            message="ece_10_bin_improvement must match retained metrics",
        )
        _require_matching_float(
            actual=self.auroc_delta,
            expected=self.calibrated_metrics.auroc - self.raw_metrics.auroc,
            message="auroc_delta must match retained metrics",
        )

        expected_gate_values = {
            "observation_coverage_passed": (
                self.case_count == self.protocol.expected_final_case_count
                and self.observation_count == self.protocol.expected_final_observation_count
            ),
            "per_position_coverage_passed": all(
                item.observation_count == self.protocol.expected_observations_per_position
                for item in self.position_metrics
            ),
            "brier_improvement_passed": (
                self.brier_score_improvement >= self.protocol.minimum_brier_score_improvement
            ),
            "ece_improvement_passed": (
                self.ece_10_bin_improvement >= self.protocol.minimum_ece_10_bin_improvement
            ),
            "ranking_safety_passed": (
                self.calibrated_metrics.auroc
                >= self.raw_metrics.auroc - self.protocol.maximum_auroc_degradation
            ),
            "no_refit_passed": not self.calibration_refit_performed,
            "no_policy_execution_passed": not self.scheduler_or_policy_execution_performed,
        }
        for gate_name, expected_value in expected_gate_values.items():
            if getattr(self.gate_checks, gate_name) is not expected_value:
                raise ValueError(f"{gate_name} must match retained V4 result evidence")

        expected_status = derive_v4_final_assessment_status(self.gate_checks)
        if self.status is not expected_status:
            raise ValueError("status must match the predeclared V4 gate precedence")

        expected_eligibility = (
            V4AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
            if self.status
            is V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
            else V4AdaptivePolicyResearchEligibility.BLOCKED
        )
        if self.adaptive_policy_research_eligibility is not expected_eligibility:
            raise ValueError("research eligibility must match the final V4 gate status")

        if self.status is V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE:
            if self.fallback is not None:
                raise ValueError("a passing V4 gate must not retain a conservative fallback")
        elif self.fallback is None:
            raise ValueError("a non-passing V4 gate requires the conservative fallback")
        return self


def derive_v4_final_assessment_status(
    gate_checks: V4FinalAssessmentGateChecks,
) -> V4FinalHeldOutAssessmentStatus:
    """Apply ADR-0015 status precedence without inspecting evidence assets."""

    if not (gate_checks.manifest_integrity_passed and gate_checks.provenance_alignment_passed):
        return V4FinalHeldOutAssessmentStatus.INVALID_PROVENANCE
    if not (
        gate_checks.no_refit_passed
        and gate_checks.no_policy_execution_passed
        and gate_checks.write_once_precheck_passed
        and gate_checks.canonical_serialization_passed
    ):
        return V4FinalHeldOutAssessmentStatus.INCOMPLETE_GATE_EVIDENCE
    if not (gate_checks.observation_coverage_passed and gate_checks.per_position_coverage_passed):
        return V4FinalHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_COVERAGE
    if not gate_checks.ranking_safety_passed:
        return V4FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    if not (gate_checks.brier_improvement_passed and gate_checks.ece_improvement_passed):
        return V4FinalHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    return V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE


def calculate_tie_aware_auroc(
    probabilities: Sequence[float],
    labels: Sequence[bool],
) -> float:
    """Calculate AUROC while retaining the V4 assessment error contract."""

    try:
        return _calculate_tie_aware_auroc(probabilities, labels)
    except TieAwareAurocInputError as error:
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.INVALID_METRICS,
            str(error),
        ) from error


def canonical_v4_final_assessment_json(
    result: V4FinalHeldOutAssessmentResult,
) -> bytes:
    """Return stable JSON bytes for an already-validated V4 assessment result."""

    if type(result) is not V4FinalHeldOutAssessmentResult:
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.INVALID_RESULT,
            "canonical V4 output requires the exact V4 final result contract",
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


def write_v4_final_assessment_result(
    result: V4FinalHeldOutAssessmentResult,
    destination: Path,
) -> Path:
    """Persist a validated V4 result once, without an overwrite path."""

    if destination.suffix != ".json":
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.INVALID_DESTINATION,
            "V4 final assessment destination must use a .json suffix",
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as output:
            output.write(canonical_v4_final_assessment_json(result))
    except FileExistsError as error:
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V4 final assessment is write-once and already exists: {destination}",
        ) from error
    except OSError as error:
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.INVALID_DESTINATION,
            f"unable to persist V4 final assessment: {destination}",
        ) from error
    return destination


def run_v4_final_assessment_once(
    destination: Path,
    assessment_builder: Callable[[], V4FinalHeldOutAssessmentResult],
) -> tuple[V4FinalHeldOutAssessmentResult, Path]:
    """Enforce write-once precheck before a future V4 loader or scorer can be invoked.

    The builder is injected because this pre-evidence slice intentionally has no V4 fixture loader
    or scoring path. A future implementation may supply one only after V4 evidence authoring is
    authorized.
    """

    if destination.exists():
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V4 final assessment is write-once and already exists: {destination}",
        )
    if not callable(assessment_builder):
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.INVALID_ASSESSMENT_BUILDER,
            "V4 final assessment requires a callable result builder",
        )
    result = assessment_builder()
    if type(result) is not V4FinalHeldOutAssessmentResult:
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.INVALID_RESULT,
            "V4 final assessment builder must return the exact V4 result contract",
        )
    return result, write_v4_final_assessment_result(result, destination)


def reject_unsafe_retrospective_control(
    policy_id: str,
) -> V4UnsafeRetrospectiveControlRejection:
    """Return the mandatory invalid label for the V4 retrospective oracle control."""

    if policy_id != _UNSAFE_RETROSPECTIVE_CONTROL_ID:
        raise V4FinalAssessmentError(
            V4FinalAssessmentErrorCode.UNSAFE_RETROSPECTIVE_CONTROL_REJECTED,
            "only unsafe_retrospective_oracle_v4 may be labelled by this rejection boundary",
        )
    return V4UnsafeRetrospectiveControlRejection()


def _require_matching_float(*, actual: float, expected: float, message: str) -> None:
    if not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(message)
