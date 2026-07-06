"""One-time V3 held-out calibration assessment with immutable evidence output.

This module is deliberately narrower than policy evaluation. It verifies the frozen V3 final
manifest and frozen calibration provenance, loads the already-fitted quantile-isotonic artifact
without refitting it, computes raw-versus-calibrated probability diagnostics once, and persists
a write-once result. It never invokes a scheduler, tunes a threshold, or exposes held-out labels
to runtime policy code.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_redesign_v3_final_evidence import (
    CalibrationRedesignV3FinalEvidenceIndex,
    load_calibration_redesign_v3_final_evidence_index,
)
from specsafe.traces.calibration_redesign_v3_final_manifest import (
    CalibrationRedesignV3FinalManifestedFixtureSet,
    load_calibration_redesign_v3_final_evaluation_manifested_fixture_set,
)
from specsafe.traces.calibration_redesign_v3_manifest import (
    load_calibration_redesign_v3_calibration_manifested_fixture_set,
)
from specsafe.traces.quantile_isotonic_calibration import (
    QuantileIsotonicCalibrationArtifact,
    QuantileIsotonicCalibrationFitReport,
    QuantileIsotonicCalibrationFitResult,
)

_ASSESSMENT_SCHEMA_VERSION = "v3-final-heldout-calibration-assessment-v1"
_ASSESSMENT_PROTOCOL_ID = "v3_final_heldout_calibration_assessment_protocol_v1"
_EXPECTED_CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(201, 225))
_EXPECTED_POSITION_INDICES = (1, 2, 3, 4)
_EXPECTED_OBSERVATION_COUNT = 96
_EXPECTED_CASE_COUNT = 24
_DIAGNOSTIC_BIN_COUNT = 10


class V3FinalHeldOutCalibrationAssessmentErrorCode(StrEnum):
    """Machine-readable failures for the V3 final-assessment boundary."""

    INVALID_FIXTURE_ROOT = "v3_final_heldout_calibration_invalid_fixture_root"
    FROZEN_PROVENANCE_MISMATCH = (
        "v3_final_heldout_calibration_frozen_provenance_mismatch"
    )
    ARTIFACT_SCHEMA_ERROR = "v3_final_heldout_calibration_artifact_schema_error"
    ARTIFACT_REPORT_MISMATCH = "v3_final_heldout_calibration_artifact_report_mismatch"
    CALIBRATION_MANIFEST_MISMATCH = "v3_final_heldout_calibration_manifest_mismatch"
    OBSERVATION_ALIGNMENT_ERROR = (
        "v3_final_heldout_calibration_observation_alignment_error"
    )
    INVALID_DESTINATION = "v3_final_heldout_calibration_invalid_destination"
    DESTINATION_ALREADY_EXISTS = (
        "v3_final_heldout_calibration_destination_already_exists"
    )
    INVALID_RESULT = "v3_final_heldout_calibration_invalid_result"


class V3FinalHeldOutCalibrationAssessmentError(ValueError):
    """Raised when V3 final-assessment evidence cannot be trusted or persisted safely."""

    def __init__(
        self,
        code: V3FinalHeldOutCalibrationAssessmentErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class V3FinalHeldOutCalibrationAssessmentStatus(StrEnum):
    """Predeclared final-evaluation fitness outcomes for the frozen V3 calibrator."""

    PASSES_HELD_OUT_FITNESS = "passes_held_out_fitness"
    CALIBRATOR_REGRESSION = "calibrator_regression"
    NO_MATERIAL_HELD_OUT_IMPROVEMENT = "no_material_held_out_improvement"


class V3FinalAdaptivePolicyResearchEligibility(StrEnum):
    """Research-only next-step posture; this assessment never authorizes runtime control."""

    ELIGIBLE_PENDING_EXPLICIT_AUTHORIZATION = "eligible_pending_explicit_authorization"
    BLOCKED_HELD_OUT_CALIBRATION_REGRESSION = "blocked_held_out_calibration_regression"
    BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT = (
        "blocked_no_material_held_out_improvement"
    )


class V3FinalHeldOutCalibrationAssessmentProtocol(StrictContract):
    """Predeclared, fixed assessment criteria that cannot be tuned on final outcomes."""

    protocol_id: Literal["v3_final_heldout_calibration_assessment_protocol_v1"] = (
        _ASSESSMENT_PROTOCOL_ID
    )
    expected_case_count: Literal[24] = _EXPECTED_CASE_COUNT
    expected_observation_count: Literal[96] = _EXPECTED_OBSERVATION_COUNT
    diagnostic_bin_count: Literal[10] = _DIAGNOSTIC_BIN_COUNT
    minimum_brier_score_improvement: Literal[0.0] = 0.0
    minimum_expected_calibration_error_improvement: Literal[0.0] = 0.0
    require_strict_improvement: Literal[True] = True


DEFAULT_V3_FINAL_HELDOUT_CALIBRATION_ASSESSMENT_PROTOCOL = (
    V3FinalHeldOutCalibrationAssessmentProtocol()
)


class V3FinalHeldOutCalibrationBin(StrictContract):
    """One fixed-width diagnostic bin for raw or calibrated held-out probabilities."""

    bin_index: int = Field(ge=0, le=_DIAGNOSTIC_BIN_COUNT - 1)
    lower_probability_bound: float = Field(ge=0.0, le=1.0)
    upper_probability_bound: float = Field(gt=0.0, le=1.0)
    observation_count: int = Field(ge=0)
    mean_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bin_evidence(self) -> V3FinalHeldOutCalibrationBin:
        if self.lower_probability_bound >= self.upper_probability_bound:
            raise ValueError("held-out bin lower bound must be below upper bound")
        evidence_fields = (
            self.mean_probability,
            self.observed_acceptance_rate,
            self.absolute_calibration_gap,
        )
        if self.observation_count == 0 and any(
            value is not None for value in evidence_fields
        ):
            raise ValueError("empty held-out bins must not contain diagnostic values")
        if self.observation_count > 0 and any(
            value is None for value in evidence_fields
        ):
            raise ValueError(
                "populated held-out bins require complete diagnostic values"
            )
        return self


class V3FinalProbabilityMetrics(StrictContract):
    """Brier, ECE, and fixed-width diagnostic evidence for one probability representation."""

    brier_score: float = Field(ge=0.0, le=1.0)
    expected_calibration_error: float = Field(ge=0.0, le=1.0)
    bins: tuple[V3FinalHeldOutCalibrationBin, ...] = Field(
        min_length=_DIAGNOSTIC_BIN_COUNT,
        max_length=_DIAGNOSTIC_BIN_COUNT,
    )

    @model_validator(mode="after")
    def validate_bin_coverage(self) -> V3FinalProbabilityMetrics:
        expected_indices = tuple(range(_DIAGNOSTIC_BIN_COUNT))
        actual_indices = tuple(bin_summary.bin_index for bin_summary in self.bins)
        if actual_indices != expected_indices:
            raise ValueError(
                "probability metric bins must cover all fixed bin indices in order"
            )
        return self


class V3FinalPositionCalibrationMetrics(StrictContract):
    """Raw-versus-calibrated diagnostics for one fixed candidate position."""

    block_position_index: Literal[1, 2, 3, 4]
    observation_count: Literal[24] = 24
    raw_metrics: V3FinalProbabilityMetrics
    calibrated_metrics: V3FinalProbabilityMetrics
    brier_score_improvement: float
    expected_calibration_error_improvement: float

    @model_validator(mode="after")
    def validate_improvements(self) -> V3FinalPositionCalibrationMetrics:
        expected_brier_improvement = (
            self.raw_metrics.brier_score - self.calibrated_metrics.brier_score
        )
        expected_ece_improvement = (
            self.raw_metrics.expected_calibration_error
            - self.calibrated_metrics.expected_calibration_error
        )
        if self.brier_score_improvement != expected_brier_improvement:
            raise ValueError("position brier improvement must match retained metrics")
        if self.expected_calibration_error_improvement != expected_ece_improvement:
            raise ValueError("position ECE improvement must match retained metrics")
        return self


class V3FinalHeldOutCalibrationAssessmentResult(StrictContract):
    """Write-once V3 final-evaluation calibration evidence with no runtime promotion."""

    schema_version: Literal["v3-final-heldout-calibration-assessment-v1"] = (
        _ASSESSMENT_SCHEMA_VERSION
    )
    protocol: V3FinalHeldOutCalibrationAssessmentProtocol
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    final_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_fit_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_id: Literal["quantile-isotonic-calibration-v1"]
    calibration_artifact_version: Literal["1.0.0"]
    assessment_case_ids: tuple[str, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )
    assessment_trace_ids: tuple[str, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )
    observation_count: Literal[96] = _EXPECTED_OBSERVATION_COUNT
    raw_metrics: V3FinalProbabilityMetrics
    calibrated_metrics: V3FinalProbabilityMetrics
    position_metrics: tuple[V3FinalPositionCalibrationMetrics, ...] = Field(
        min_length=4,
        max_length=4,
    )
    brier_score_improvement: float
    expected_calibration_error_improvement: float
    status: V3FinalHeldOutCalibrationAssessmentStatus
    adaptive_policy_research_eligibility: V3FinalAdaptivePolicyResearchEligibility
    runtime_control_eligible: Literal[False] = False
    calibration_refit_performed: Literal[False] = False
    scheduler_or_policy_execution_performed: Literal[False] = False
    write_mode: Literal["write_once"] = "write_once"

    @model_validator(mode="after")
    def validate_result_integrity(self) -> V3FinalHeldOutCalibrationAssessmentResult:
        if tuple(sorted(self.assessment_case_ids)) != _EXPECTED_CASE_IDS:
            raise ValueError("assessment must retain exactly CRV3-201 through CRV3-224")
        if len(set(self.assessment_trace_ids)) != _EXPECTED_CASE_COUNT:
            raise ValueError("assessment trace IDs must be unique")
        if (
            tuple(item.block_position_index for item in self.position_metrics)
            != _EXPECTED_POSITION_INDICES
        ):
            raise ValueError(
                "position metrics must cover positions one through four in order"
            )
        if (
            sum(item.observation_count for item in self.position_metrics)
            != self.observation_count
        ):
            raise ValueError(
                "position metric observations must sum to the final observation count"
            )
        for metrics in (self.raw_metrics, self.calibrated_metrics):
            if sum(bin_summary.observation_count for bin_summary in metrics.bins) != (
                self.observation_count
            ):
                raise ValueError(
                    "aggregate metric bin counts must match observation_count"
                )
        expected_brier_improvement = (
            self.raw_metrics.brier_score - self.calibrated_metrics.brier_score
        )
        expected_ece_improvement = (
            self.raw_metrics.expected_calibration_error
            - self.calibrated_metrics.expected_calibration_error
        )
        if self.brier_score_improvement != expected_brier_improvement:
            raise ValueError("brier score improvement must match retained metrics")
        if self.expected_calibration_error_improvement != expected_ece_improvement:
            raise ValueError("ECE improvement must match retained metrics")
        expected_eligibility = {
            V3FinalHeldOutCalibrationAssessmentStatus.PASSES_HELD_OUT_FITNESS: (
                V3FinalAdaptivePolicyResearchEligibility.ELIGIBLE_PENDING_EXPLICIT_AUTHORIZATION
            ),
            V3FinalHeldOutCalibrationAssessmentStatus.CALIBRATOR_REGRESSION: (
                V3FinalAdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION
            ),
            V3FinalHeldOutCalibrationAssessmentStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT: (
                V3FinalAdaptivePolicyResearchEligibility.BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT
            ),
        }
        if (
            expected_eligibility[self.status]
            is not self.adaptive_policy_research_eligibility
        ):
            raise ValueError(
                "assessment status must match the research-eligibility posture"
            )
        return self


@dataclass(frozen=True, slots=True)
class _HeldOutObservation:
    """One post-hoc final observation; never available to a runtime policy."""

    case_id: str
    trace_id: str
    block_position_index: int
    raw_probability: float
    calibrated_probability: float
    observed_acceptance: bool


def evaluate_v3_final_heldout_calibration(
    fixture_root: Path,
    *,
    protocol: V3FinalHeldOutCalibrationAssessmentProtocol = (
        DEFAULT_V3_FINAL_HELDOUT_CALIBRATION_ASSESSMENT_PROTOCOL
    ),
) -> V3FinalHeldOutCalibrationAssessmentResult:
    """Evaluate the frozen V3 calibrator once against frozen final evidence.

    This function is intentionally not a scheduler interface. It performs no calibration fit,
    policy execution, threshold tuning, capacity tuning, or output overwrite.
    """

    if type(protocol) is not V3FinalHeldOutCalibrationAssessmentProtocol:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.INVALID_FIXTURE_ROOT,
            "V3 final assessment requires the exact frozen assessment protocol",
        )

    root = fixture_root.resolve()
    try:
        final_index = load_calibration_redesign_v3_final_evidence_index(root)
        final_fixture_set = (
            load_calibration_redesign_v3_final_evaluation_manifested_fixture_set(root)
        )
        calibration_fixture_set = (
            load_calibration_redesign_v3_calibration_manifested_fixture_set(root)
        )
    except ValueError as error:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.FROZEN_PROVENANCE_MISMATCH,
            f"unable to verify frozen V3 assessment inputs: {error}",
        ) from error

    artifact, fit_report = _load_frozen_calibration_artifact_and_report(
        root, final_index
    )
    _validate_cross_boundary_provenance(
        final_fixture_set=final_fixture_set,
        calibration_manifest_aggregate_sha256=calibration_fixture_set.manifest.aggregate_sha256,
        artifact=artifact,
        fit_report=fit_report,
        final_index=final_index,
    )

    observations = _collect_heldout_observations(final_fixture_set, artifact)
    if len(observations) != protocol.expected_observation_count:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V3 final assessment must retain exactly 96 scored observations",
        )

    raw_metrics = _build_probability_metrics(
        probabilities=tuple(item.raw_probability for item in observations),
        labels=tuple(item.observed_acceptance for item in observations),
        bin_count=protocol.diagnostic_bin_count,
    )
    calibrated_metrics = _build_probability_metrics(
        probabilities=tuple(item.calibrated_probability for item in observations),
        labels=tuple(item.observed_acceptance for item in observations),
        bin_count=protocol.diagnostic_bin_count,
    )
    position_metrics = _build_position_metrics(
        observations=observations,
        bin_count=protocol.diagnostic_bin_count,
    )
    brier_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_improvement = (
        raw_metrics.expected_calibration_error
        - calibrated_metrics.expected_calibration_error
    )
    status, research_eligibility = _derive_assessment_status(
        observation_count=len(observations),
        brier_improvement=brier_improvement,
        expected_calibration_error_improvement=ece_improvement,
        protocol=protocol,
    )

    return V3FinalHeldOutCalibrationAssessmentResult(
        protocol=protocol,
        fixture_set_id=final_fixture_set.manifest.fixture_set_id,
        fixture_set_version=final_fixture_set.manifest.fixture_set_version,
        final_manifest_aggregate_sha256=final_fixture_set.manifest.aggregate_sha256,
        final_evidence_index_sha256=final_fixture_set.manifest.final_evidence_index_sha256,
        calibration_registry_sha256=final_index.calibration_registry_sha256,
        calibration_manifest_sha256=final_index.calibration_manifest_sha256,
        calibration_manifest_aggregate_sha256=calibration_fixture_set.manifest.aggregate_sha256,
        calibration_artifact_sha256=final_index.calibration_artifact_sha256,
        calibration_fit_report_sha256=final_index.calibration_fit_report_sha256,
        calibration_artifact_id=artifact.artifact_id,
        calibration_artifact_version=artifact.artifact_version,
        assessment_case_ids=tuple(
            case.runtime_input.case_id for case in final_fixture_set.cases
        ),
        assessment_trace_ids=tuple(
            case.runtime_input.trace_id for case in final_fixture_set.cases
        ),
        observation_count=len(observations),
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        position_metrics=position_metrics,
        brier_score_improvement=brier_improvement,
        expected_calibration_error_improvement=ece_improvement,
        status=status,
        adaptive_policy_research_eligibility=research_eligibility,
    )


def run_v3_final_heldout_calibration_assessment_once(
    fixture_root: Path,
    destination: Path,
) -> tuple[V3FinalHeldOutCalibrationAssessmentResult, Path]:
    """Perform the V3 final score only when its immutable destination is still absent."""

    if destination.exists():
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V3 final assessment is write-once and already exists: {destination}",
        )
    result = evaluate_v3_final_heldout_calibration(fixture_root)
    return result, write_v3_final_heldout_calibration_assessment(result, destination)


def write_v3_final_heldout_calibration_assessment(
    result: V3FinalHeldOutCalibrationAssessmentResult,
    destination: Path,
) -> Path:
    """Persist a deterministic V3 assessment result exactly once without overwrite."""

    if type(result) is not V3FinalHeldOutCalibrationAssessmentResult:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.INVALID_RESULT,
            "V3 final assessment persistence requires the exact result contract",
        )
    if destination.suffix != ".json":
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.INVALID_DESTINATION,
            "V3 final assessment destination must use a .json suffix",
        )

    payload = (
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(payload)
    except FileExistsError as error:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.DESTINATION_ALREADY_EXISTS,
            f"V3 final assessment is write-once and already exists: {destination}",
        ) from error
    except OSError as error:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.INVALID_DESTINATION,
            f"unable to persist V3 final assessment: {destination}",
        ) from error
    return destination


def _load_frozen_calibration_artifact_and_report(
    fixture_root: Path,
    final_index: CalibrationRedesignV3FinalEvidenceIndex,
) -> tuple[QuantileIsotonicCalibrationArtifact, QuantileIsotonicCalibrationFitReport]:
    project_root = fixture_root.resolve().parents[2]
    artifact_path = project_root / final_index.calibration_artifact_path
    report_path = project_root / final_index.calibration_fit_report_path
    try:
        artifact_bytes = artifact_path.read_bytes()
        report_bytes = report_path.read_bytes()
        artifact = QuantileIsotonicCalibrationArtifact.model_validate_json(
            artifact_bytes
        )
        fit_report = QuantileIsotonicCalibrationFitReport.model_validate_json(
            report_bytes
        )
        QuantileIsotonicCalibrationFitResult(artifact=artifact, report=fit_report)
    except (OSError, ValidationError, ValueError) as error:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.ARTIFACT_SCHEMA_ERROR,
            f"unable to load the frozen V3 calibration artifact and fit report: {error}",
        ) from error

    if _sha256(artifact_bytes) != final_index.calibration_artifact_sha256:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "frozen calibration artifact bytes do not match the final-evidence index",
        )
    if _sha256(report_bytes) != final_index.calibration_fit_report_sha256:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "frozen calibration fit-report bytes do not match the final-evidence index",
        )
    return artifact, fit_report


def _validate_cross_boundary_provenance(
    *,
    final_fixture_set: CalibrationRedesignV3FinalManifestedFixtureSet,
    calibration_manifest_aggregate_sha256: str,
    artifact: QuantileIsotonicCalibrationArtifact,
    fit_report: QuantileIsotonicCalibrationFitReport,
    final_index: CalibrationRedesignV3FinalEvidenceIndex,
) -> None:
    if final_fixture_set.manifest.case_count != _EXPECTED_CASE_COUNT:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V3 final manifest must contain exactly 24 held-out cases",
        )
    if final_fixture_set.manifest.observation_count != _EXPECTED_OBSERVATION_COUNT:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V3 final manifest must contain exactly 96 held-out observations",
        )
    if (
        artifact.calibration_manifest_aggregate_sha256
        != calibration_manifest_aggregate_sha256
    ):
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.CALIBRATION_MANIFEST_MISMATCH,
            "frozen calibration artifact does not match the verified calibration manifest",
        )
    if (
        fit_report.calibration_manifest_aggregate_sha256
        != calibration_manifest_aggregate_sha256
    ):
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.CALIBRATION_MANIFEST_MISMATCH,
            "frozen calibration fit report does not match the verified calibration manifest",
        )
    if (
        final_fixture_set.manifest.fixture_set_id != final_index.fixture_set_id
        or final_fixture_set.manifest.fixture_set_version
        != final_index.fixture_set_version
        or artifact.fixture_set_id != final_index.fixture_set_id
        or artifact.fixture_set_version != final_index.fixture_set_version
    ):
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.FROZEN_PROVENANCE_MISMATCH,
            "V3 final assessment inputs disagree on fixture-set identity or version",
        )


def _collect_heldout_observations(
    fixture_set: CalibrationRedesignV3FinalManifestedFixtureSet,
    artifact: QuantileIsotonicCalibrationArtifact,
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
                raise V3FinalHeldOutCalibrationAssessmentError(
                    V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                    "V3 final assessment is missing an outcome for "
                    f"{replay_case.runtime_input.case_id}",
                )
            raw_probability = context.conditional_survival_confidence
            if not isfinite(raw_probability) or not 0.0 <= raw_probability <= 1.0:
                raise V3FinalHeldOutCalibrationAssessmentError(
                    V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                    "V3 final raw confidence must be finite and inside the unit interval",
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
    *,
    observations: tuple[_HeldOutObservation, ...],
    bin_count: int,
) -> tuple[V3FinalPositionCalibrationMetrics, ...]:
    position_metrics: list[V3FinalPositionCalibrationMetrics] = []
    for position_index in _EXPECTED_POSITION_INDICES:
        position_observations = tuple(
            item for item in observations if item.block_position_index == position_index
        )
        if len(position_observations) != _EXPECTED_CASE_COUNT:
            raise V3FinalHeldOutCalibrationAssessmentError(
                V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
                f"V3 final position {position_index} must retain exactly 24 observations",
            )
        raw_metrics = _build_probability_metrics(
            probabilities=tuple(item.raw_probability for item in position_observations),
            labels=tuple(item.observed_acceptance for item in position_observations),
            bin_count=bin_count,
        )
        calibrated_metrics = _build_probability_metrics(
            probabilities=tuple(
                item.calibrated_probability for item in position_observations
            ),
            labels=tuple(item.observed_acceptance for item in position_observations),
            bin_count=bin_count,
        )
        position_metrics.append(
            V3FinalPositionCalibrationMetrics(
                block_position_index=position_index,
                observation_count=len(position_observations),
                raw_metrics=raw_metrics,
                calibrated_metrics=calibrated_metrics,
                brier_score_improvement=(
                    raw_metrics.brier_score - calibrated_metrics.brier_score
                ),
                expected_calibration_error_improvement=(
                    raw_metrics.expected_calibration_error
                    - calibrated_metrics.expected_calibration_error
                ),
            )
        )
    return tuple(position_metrics)


def _build_probability_metrics(
    *,
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
    bin_count: int,
) -> V3FinalProbabilityMetrics:
    if len(probabilities) != len(labels) or not probabilities:
        raise ValueError("probabilities and labels must be non-empty and aligned")
    if bin_count != _DIAGNOSTIC_BIN_COUNT:
        raise ValueError(
            "V3 final assessment requires exactly ten fixed diagnostic bins"
        )

    brier_score = sum(
        (probability - float(label)) ** 2
        for probability, label in zip(probabilities, labels, strict=True)
    ) / len(probabilities)
    bins = _build_bins(probabilities=probabilities, labels=labels, bin_count=bin_count)
    expected_calibration_error = sum(
        (bin_summary.observation_count / len(probabilities))
        * (bin_summary.absolute_calibration_gap or 0.0)
        for bin_summary in bins
    )
    return V3FinalProbabilityMetrics(
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        bins=bins,
    )


def _build_bins(
    *,
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
    bin_count: int,
) -> tuple[V3FinalHeldOutCalibrationBin, ...]:
    grouped: list[list[tuple[float, bool]]] = [[] for _ in range(bin_count)]
    for probability, label in zip(probabilities, labels, strict=True):
        bin_index = min(int(probability * bin_count), bin_count - 1)
        grouped[bin_index].append((probability, label))

    summaries: list[V3FinalHeldOutCalibrationBin] = []
    for bin_index, members in enumerate(grouped):
        lower_bound = bin_index / bin_count
        upper_bound = (bin_index + 1) / bin_count
        if not members:
            summaries.append(
                V3FinalHeldOutCalibrationBin(
                    bin_index=bin_index,
                    lower_probability_bound=lower_bound,
                    upper_probability_bound=upper_bound,
                    observation_count=0,
                )
            )
            continue
        count = len(members)
        mean_probability = sum(probability for probability, _ in members) / count
        observed_acceptance_rate = sum(label for _, label in members) / count
        summaries.append(
            V3FinalHeldOutCalibrationBin(
                bin_index=bin_index,
                lower_probability_bound=lower_bound,
                upper_probability_bound=upper_bound,
                observation_count=count,
                mean_probability=mean_probability,
                observed_acceptance_rate=observed_acceptance_rate,
                absolute_calibration_gap=abs(
                    mean_probability - observed_acceptance_rate
                ),
            )
        )
    return tuple(summaries)


def _derive_assessment_status(
    *,
    observation_count: int,
    brier_improvement: float,
    expected_calibration_error_improvement: float,
    protocol: V3FinalHeldOutCalibrationAssessmentProtocol,
) -> tuple[
    V3FinalHeldOutCalibrationAssessmentStatus,
    V3FinalAdaptivePolicyResearchEligibility,
]:
    if observation_count != protocol.expected_observation_count:
        raise V3FinalHeldOutCalibrationAssessmentError(
            V3FinalHeldOutCalibrationAssessmentErrorCode.OBSERVATION_ALIGNMENT_ERROR,
            "V3 final assessment cannot evaluate a partial or expanded final corpus",
        )
    if brier_improvement < 0.0 or expected_calibration_error_improvement < 0.0:
        return (
            V3FinalHeldOutCalibrationAssessmentStatus.CALIBRATOR_REGRESSION,
            V3FinalAdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION,
        )
    if (
        brier_improvement <= protocol.minimum_brier_score_improvement
        or expected_calibration_error_improvement
        <= protocol.minimum_expected_calibration_error_improvement
    ):
        return (
            V3FinalHeldOutCalibrationAssessmentStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT,
            V3FinalAdaptivePolicyResearchEligibility.BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
        )
    return (
        V3FinalHeldOutCalibrationAssessmentStatus.PASSES_HELD_OUT_FITNESS,
        V3FinalAdaptivePolicyResearchEligibility.ELIGIBLE_PENDING_EXPLICIT_AUTHORIZATION,
    )


def _sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()
