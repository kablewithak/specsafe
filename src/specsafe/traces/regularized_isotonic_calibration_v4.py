"""Deterministic V4 regularized-isotonic calibration fit and diagnostics.

This module consumes only the hash-verified V4 calibration manifest and the 48 calibration-only
case pairs it names. It produces calibration-only evidence. It cannot load V4 final-evaluation or
adversarial evidence, execute a scheduler, compare policies, or authorize runtime control.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)
from specsafe.metrics.ranking import calculate_tie_aware_auroc
from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    load_calibration_redesign_v4_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v4_cases import (
    CalibrationRedesignV4ReplayCase,
    load_calibration_redesign_v4_replay_case,
)
from specsafe.traces.calibration_redesign_v4_manifest import (
    CalibrationRedesignV4CalibrationManifest,
    load_calibration_redesign_v4_calibration_manifest,
)

_ARTIFACT_ID = "regularized-isotonic-calibration-v4"
_ARTIFACT_VERSION = "1.0.0"
_PROTOCOL_ID = "regularized_isotonic_calibration_v4_fit_protocol_v1"
_ARTIFACT_FILENAME = "artifact.json"
_FIT_REPORT_FILENAME = "fit_report.json"
_EXPECTED_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(101, 149))
_EXPECTED_FAMILY_IDS = (
    "CRV4-CAL-CAPACITY-CONTRAST",
    "CRV4-CAL-CURVE-COVERAGE",
    "CRV4-CAL-POSITION-SPREAD",
    "CRV4-CAL-WORKLOAD-MIX",
)
_GROUP_COUNT = 12
_MINIMUM_GROUP_OBSERVATIONS = 16
_LAPLACE_SUCCESS_PRIOR = 1
_LAPLACE_TOTAL_PRIOR = 2
_OUTPUT_LOWER_BOUND = 0.01
_OUTPUT_UPPER_BOUND = 0.99
_ECE_BIN_COUNT = 10


class RegularizedIsotonicCalibrationV4ViolationCode(StrEnum):
    """Machine-readable reasons the V4 calibration-only fit can be rejected."""

    UNTRUSTED_FIXTURE_SET = "regularized_isotonic_calibration_v4_untrusted_fixture_set"
    NON_CALIBRATION_EVIDENCE = (
        "regularized_isotonic_calibration_v4_non_calibration_evidence"
    )
    MANIFEST_PROVENANCE_FAILURE = (
        "regularized_isotonic_calibration_v4_manifest_provenance_failure"
    )
    INSUFFICIENT_CALIBRATION_SAMPLES = (
        "regularized_isotonic_calibration_v4_insufficient_calibration_samples"
    )
    DEGENERATE_LABEL_DISTRIBUTION = (
        "regularized_isotonic_calibration_v4_degenerate_label_distribution"
    )
    NON_FINITE_CONFIDENCE = "regularized_isotonic_calibration_v4_non_finite_confidence"
    INVALID_RAW_CONFIDENCE = (
        "regularized_isotonic_calibration_v4_invalid_raw_confidence"
    )
    ARTIFACT_SCHEMA_ERROR = "regularized_isotonic_calibration_v4_artifact_schema_error"
    DESTINATION_ALREADY_EXISTS = (
        "regularized_isotonic_calibration_v4_destination_exists"
    )
    INVALID_DESTINATION = "regularized_isotonic_calibration_v4_invalid_destination"
    FIT_EVIDENCE_READ_ERROR = (
        "regularized_isotonic_calibration_v4_fit_evidence_read_error"
    )
    FIT_EVIDENCE_HASH_MISMATCH = (
        "regularized_isotonic_calibration_v4_fit_evidence_hash_mismatch"
    )


class RegularizedIsotonicCalibrationV4FitError(ValueError):
    """Raised when V4 fitting crosses a typed calibration-only boundary."""

    def __init__(
        self,
        code: RegularizedIsotonicCalibrationV4ViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class RegularizedIsotonicCalibrationV4FitProtocol(StrictContract):
    """Predeclared V4 equal-count, smoothing, and monotonic-pooling configuration."""

    protocol_id: Literal["regularized_isotonic_calibration_v4_fit_protocol_v1"] = (
        _PROTOCOL_ID
    )
    equal_count_group_count: Literal[12] = _GROUP_COUNT
    minimum_observations_per_group: Literal[16] = _MINIMUM_GROUP_OBSERVATIONS
    laplace_success_prior: Literal[1] = _LAPLACE_SUCCESS_PRIOR
    laplace_total_prior: Literal[2] = _LAPLACE_TOTAL_PRIOR
    output_lower_bound: float = Field(default=_OUTPUT_LOWER_BOUND, gt=0.0, lt=0.5)
    output_upper_bound: float = Field(default=_OUTPUT_UPPER_BOUND, gt=0.5, lt=1.0)
    ece_bin_count: Literal[10] = _ECE_BIN_COUNT

    @model_validator(mode="after")
    def validate_output_bounds(self) -> RegularizedIsotonicCalibrationV4FitProtocol:
        if self.output_lower_bound >= self.output_upper_bound:
            raise ValueError("output lower bound must be less than output upper bound")
        return self


DEFAULT_REGULARIZED_ISOTONIC_CALIBRATION_V4_FIT_PROTOCOL = (
    RegularizedIsotonicCalibrationV4FitProtocol()
)


class RegularizedIsotonicCalibrationV4Bin(StrictContract):
    """One equal-count raw-confidence group after deterministic weighted PAV pooling."""

    group_index: int = Field(ge=1, le=_GROUP_COUNT)
    raw_confidence_lower_bound: float = Field(ge=0.0, le=1.0)
    raw_confidence_upper_bound: float = Field(ge=0.0, le=1.0)
    sample_count: int = Field(ge=_MINIMUM_GROUP_OBSERVATIONS)
    positive_label_count: int = Field(ge=0)
    negative_label_count: int = Field(ge=0)
    laplace_smoothed_acceptance_rate: float = Field(ge=0.0, le=1.0)
    pooled_block_index: int = Field(ge=1, le=_GROUP_COUNT)
    calibrated_confidence: float = Field(ge=_OUTPUT_LOWER_BOUND, le=_OUTPUT_UPPER_BOUND)

    @field_validator(
        "raw_confidence_lower_bound",
        "raw_confidence_upper_bound",
        "laplace_smoothed_acceptance_rate",
        "calibrated_confidence",
    )
    @classmethod
    def validate_finite_values(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("regularized-isotonic V4 bin values must be finite")
        return value

    @model_validator(mode="after")
    def validate_bin_shape(self) -> RegularizedIsotonicCalibrationV4Bin:
        if self.raw_confidence_lower_bound > self.raw_confidence_upper_bound:
            raise ValueError(
                "raw-confidence bin lower bound must not exceed upper bound"
            )
        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("V4 bin label counts must sum to sample_count")
        return self


class RegularizedIsotonicCalibrationV4Artifact(StrictContract):
    """Immutable V4 calibration-only map fitted from the frozen corpus."""

    schema_version: Literal["regularized-isotonic-calibration-v4-artifact-v1"]
    artifact_id: Literal["regularized-isotonic-calibration-v4"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    calibration_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_type: Literal[TraceSourceType.SYNTHETIC]
    fit_split: Literal[TraceSplit.CALIBRATION]
    fit_data_role: Literal[TraceDataRole.CALIBRATION]
    fit_case_ids: tuple[str, ...] = Field(min_length=48, max_length=48)
    fit_scenario_family_ids: tuple[str, ...] = Field(min_length=4, max_length=4)
    sample_count: Literal[192]
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    equal_count_group_count: Literal[12]
    equal_count_group_size: Literal[16]
    minimum_observations_per_group: Literal[16]
    laplace_success_prior: Literal[1]
    laplace_total_prior: Literal[2]
    output_lower_bound: float = Field(ge=0.0, le=1.0)
    output_upper_bound: float = Field(ge=0.0, le=1.0)
    bins: tuple[RegularizedIsotonicCalibrationV4Bin, ...] = Field(
        min_length=12,
        max_length=12,
    )
    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    raw_ece_10_bin: float = Field(ge=0.0, le=1.0)
    calibrated_ece_10_bin: float = Field(ge=0.0, le=1.0)
    raw_auroc: float = Field(ge=0.0, le=1.0)
    calibrated_auroc: float = Field(ge=0.0, le=1.0)
    final_evaluation_accessed: Literal[False]
    calibration_refit_performed: Literal[False]
    scheduler_or_policy_execution_performed: Literal[False]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "output_lower_bound",
        "output_upper_bound",
        "raw_brier_score",
        "calibrated_brier_score",
        "raw_ece_10_bin",
        "calibrated_ece_10_bin",
        "raw_auroc",
        "calibrated_auroc",
    )
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("regularized-isotonic V4 artifact metrics must be finite")
        return value

    @model_validator(mode="after")
    def validate_artifact_shape(self) -> RegularizedIsotonicCalibrationV4Artifact:
        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("artifact label counts must sum to sample_count")
        if self.fit_case_ids != _EXPECTED_CASE_IDS:
            raise ValueError(
                "V4 artifact fit case IDs must be CRV4-101 through CRV4-148"
            )
        if self.fit_scenario_family_ids != _EXPECTED_FAMILY_IDS:
            raise ValueError(
                "V4 artifact must retain the four fixed calibration families"
            )
        if self.output_lower_bound >= self.output_upper_bound:
            raise ValueError("artifact output bounds are invalid")
        if tuple(bin_.group_index for bin_ in self.bins) != tuple(range(1, 13)):
            raise ValueError(
                "artifact bins must retain all twelve group indices in order"
            )
        previous_upper_bound = -1.0
        previous_calibrated_confidence = -1.0
        for bin_ in self.bins:
            if bin_.raw_confidence_lower_bound < previous_upper_bound:
                raise ValueError("artifact raw-confidence bins must be ordered")
            if bin_.calibrated_confidence < previous_calibrated_confidence:
                raise ValueError(
                    "artifact calibrated confidence must be non-decreasing"
                )
            previous_upper_bound = bin_.raw_confidence_upper_bound
            previous_calibrated_confidence = bin_.calibrated_confidence
        return self

    def calibrate(self, raw_confidence: float) -> float:
        """Apply the frozen piecewise-constant monotonic V4 confidence map."""

        _validate_raw_confidence(raw_confidence)
        for bin_ in self.bins:
            if raw_confidence <= bin_.raw_confidence_upper_bound:
                return bin_.calibrated_confidence
        return self.bins[-1].calibrated_confidence


class RegularizedIsotonicCalibrationV4FitReport(StrictContract):
    """Retained calibration-only diagnostics with no held-out or policy claim."""

    schema_version: Literal["regularized-isotonic-calibration-v4-fit-report-v1"]
    artifact_id: Literal["regularized-isotonic-calibration-v4"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    calibration_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fit_scope: Literal["calibration_split_only"]
    method: Literal["equal_count_groups_laplace_smoothed_weighted_pav"]
    sample_count: Literal[192]
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    equal_count_group_count: Literal[12]
    equal_count_group_size: Literal[16]
    pooled_block_count: int = Field(ge=1, le=12)
    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    raw_ece_10_bin: float = Field(ge=0.0, le=1.0)
    calibrated_ece_10_bin: float = Field(ge=0.0, le=1.0)
    raw_auroc: float = Field(ge=0.0, le=1.0)
    calibrated_auroc: float = Field(ge=0.0, le=1.0)
    brier_score_improvement_on_fit_data: float
    ece_10_bin_improvement_on_fit_data: float
    auroc_delta_on_fit_data: float
    failure_status: Literal["none"]
    final_evaluation_accessed: Literal[False]
    heldout_calibration_gate_status: Literal["not_assessed"]
    policy_comparison_status: Literal["not_started"]
    runtime_control_eligible: Literal[False]

    @model_validator(mode="after")
    def validate_report_consistency(self) -> RegularizedIsotonicCalibrationV4FitReport:
        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("fit-report label counts must sum to sample_count")
        if self.brier_score_improvement_on_fit_data != (
            self.raw_brier_score - self.calibrated_brier_score
        ):
            raise ValueError("fit report Brier improvement must match retained metrics")
        if self.ece_10_bin_improvement_on_fit_data != (
            self.raw_ece_10_bin - self.calibrated_ece_10_bin
        ):
            raise ValueError("fit report ECE improvement must match retained metrics")
        if self.auroc_delta_on_fit_data != self.calibrated_auroc - self.raw_auroc:
            raise ValueError("fit report AUROC delta must match retained metrics")
        return self


class RegularizedIsotonicCalibrationV4FitResult(StrictContract):
    """Typed pairing of one V4 artifact and its calibration-only diagnostic report."""

    artifact: RegularizedIsotonicCalibrationV4Artifact
    report: RegularizedIsotonicCalibrationV4FitReport

    @model_validator(mode="after")
    def validate_alignment(self) -> RegularizedIsotonicCalibrationV4FitResult:
        aligned_fields = (
            "artifact_id",
            "artifact_version",
            "fixture_set_id",
            "fixture_set_version",
            "calibration_manifest_sha256",
            "calibration_manifest_aggregate_sha256",
            "calibration_registry_sha256",
            "sample_count",
            "positive_label_count",
            "negative_label_count",
            "equal_count_group_count",
            "equal_count_group_size",
            "raw_brier_score",
            "calibrated_brier_score",
            "raw_ece_10_bin",
            "calibrated_ece_10_bin",
            "raw_auroc",
            "calibrated_auroc",
            "final_evaluation_accessed",
            "runtime_control_eligible",
        )
        for field_name in aligned_fields:
            if getattr(self.artifact, field_name) != getattr(self.report, field_name):
                raise ValueError(f"artifact and fit report disagree on {field_name}")
        return self


@dataclass(frozen=True)
class RegularizedIsotonicCalibrationV4FixtureSet:
    """One manifest-verified V4 calibration corpus, materialized for a single fit."""

    root: Path
    manifest: CalibrationRedesignV4CalibrationManifest
    cases: tuple[CalibrationRedesignV4ReplayCase, ...]


@dataclass(frozen=True)
class _FitSample:
    raw_confidence: float
    observed_acceptance: int
    case_id: str
    block_position_index: int


@dataclass(frozen=True)
class _PooledBlock:
    first_group_index: int
    last_group_index: int
    weight: int
    weighted_rate_sum: float

    @property
    def calibrated_confidence(self) -> float:
        return self.weighted_rate_sum / self.weight


def load_regularized_isotonic_calibration_v4_fixture_set(
    root: Path,
) -> RegularizedIsotonicCalibrationV4FixtureSet:
    """Load exactly the manifest-verified V4 calibration evidence needed for fitting."""

    resolved_root = root.resolve()
    try:
        manifest = load_calibration_redesign_v4_calibration_manifest(resolved_root)
    except ValueError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
            f"V4 regularized-isotonic fitting requires a verified calibration manifest: {error}",
        ) from error

    if manifest.case_ids != _EXPECTED_CASE_IDS:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.NON_CALIBRATION_EVIDENCE,
            "V4 regularized-isotonic fitting requires the complete frozen calibration case set",
        )
    try:
        cases = tuple(
            load_calibration_redesign_v4_replay_case(resolved_root, case_id)
            for case_id in manifest.case_ids
        )
    except ValueError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
            f"V4 calibration fixture set cannot load one manifest-named case pair: {error}",
        ) from error
    return RegularizedIsotonicCalibrationV4FixtureSet(
        root=resolved_root,
        manifest=manifest,
        cases=cases,
    )


def fit_regularized_isotonic_calibration_v4(
    fixture_set: RegularizedIsotonicCalibrationV4FixtureSet,
    *,
    protocol: RegularizedIsotonicCalibrationV4FitProtocol = (
        DEFAULT_REGULARIZED_ISOTONIC_CALIBRATION_V4_FIT_PROTOCOL
    ),
) -> RegularizedIsotonicCalibrationV4FitResult:
    """Fit the predeclared V4 map using only verified frozen calibration evidence."""

    _validate_calibration_only_fixture_set(fixture_set)
    if type(protocol) is not RegularizedIsotonicCalibrationV4FitProtocol:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.ARTIFACT_SCHEMA_ERROR,
            "V4 fitting requires the exact frozen regularized-isotonic fit protocol",
        )

    samples = _extract_fit_samples(fixture_set)
    sample_count = len(samples)
    if sample_count % protocol.equal_count_group_count != 0:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.INSUFFICIENT_CALIBRATION_SAMPLES,
            "V4 calibration sample count must divide evenly across the fixed group count",
        )
    group_size = sample_count // protocol.equal_count_group_count
    if group_size < protocol.minimum_observations_per_group:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.INSUFFICIENT_CALIBRATION_SAMPLES,
            "V4 calibration corpus does not meet the fixed minimum group size",
        )

    positive_label_count = sum(sample.observed_acceptance for sample in samples)
    negative_label_count = sample_count - positive_label_count
    if positive_label_count == 0 or negative_label_count == 0:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.DEGENERATE_LABEL_DISTRIBUTION,
            "V4 fitting requires both accepted and rejected calibration observations",
        )

    grouped_samples = tuple(
        tuple(samples[index : index + group_size])
        for index in range(0, sample_count, group_size)
    )
    initial_bins = _build_initial_bins(grouped_samples, protocol)
    pooled_blocks = _weighted_pooled_adjacent_violators(initial_bins)
    bins = _materialize_bins(initial_bins, pooled_blocks, protocol)
    artifact = _build_artifact(
        fixture_set=fixture_set,
        protocol=protocol,
        bins=bins,
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        group_size=group_size,
    )
    report = RegularizedIsotonicCalibrationV4FitReport(
        schema_version="regularized-isotonic-calibration-v4-fit-report-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=artifact.fixture_set_id,
        fixture_set_version=artifact.fixture_set_version,
        calibration_manifest_sha256=artifact.calibration_manifest_sha256,
        calibration_manifest_aggregate_sha256=artifact.calibration_manifest_aggregate_sha256,
        calibration_registry_sha256=artifact.calibration_registry_sha256,
        fit_scope="calibration_split_only",
        method="equal_count_groups_laplace_smoothed_weighted_pav",
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        equal_count_group_count=protocol.equal_count_group_count,
        equal_count_group_size=group_size,
        pooled_block_count=len(pooled_blocks),
        raw_brier_score=artifact.raw_brier_score,
        calibrated_brier_score=artifact.calibrated_brier_score,
        raw_ece_10_bin=artifact.raw_ece_10_bin,
        calibrated_ece_10_bin=artifact.calibrated_ece_10_bin,
        raw_auroc=artifact.raw_auroc,
        calibrated_auroc=artifact.calibrated_auroc,
        brier_score_improvement_on_fit_data=(
            artifact.raw_brier_score - artifact.calibrated_brier_score
        ),
        ece_10_bin_improvement_on_fit_data=(
            artifact.raw_ece_10_bin - artifact.calibrated_ece_10_bin
        ),
        auroc_delta_on_fit_data=artifact.calibrated_auroc - artifact.raw_auroc,
        failure_status="none",
        final_evaluation_accessed=False,
        heldout_calibration_gate_status="not_assessed",
        policy_comparison_status="not_started",
        runtime_control_eligible=False,
    )
    return RegularizedIsotonicCalibrationV4FitResult(artifact=artifact, report=report)


def load_regularized_isotonic_calibration_v4_fit_result(
    fixture_root: Path,
    output_directory: Path,
) -> RegularizedIsotonicCalibrationV4FitResult:
    """Load retained V4 fit evidence only when its immutable provenance still matches."""

    resolved_fixture_root = fixture_root.resolve()
    resolved_output_directory = output_directory.resolve()
    try:
        manifest = load_calibration_redesign_v4_calibration_manifest(
            resolved_fixture_root
        )
        registry = load_calibration_redesign_v4_scenario_family_registry(
            resolved_fixture_root / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=True,
        )
    except (CalibrationRedesignV4RegistryLoadError, ValueError) as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
            f"V4 retained fit evidence requires a verified frozen calibration root: {error}",
        ) from error

    artifact_path = resolved_output_directory / _ARTIFACT_FILENAME
    report_path = resolved_output_directory / _FIT_REPORT_FILENAME
    artifact_payload = _read_json_object(artifact_path)
    report_payload = _read_json_object(report_path)
    try:
        result = RegularizedIsotonicCalibrationV4FitResult(
            artifact=RegularizedIsotonicCalibrationV4Artifact.model_validate(
                artifact_payload
            ),
            report=RegularizedIsotonicCalibrationV4FitReport.model_validate(
                report_payload
            ),
        )
    except ValueError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.ARTIFACT_SCHEMA_ERROR,
            f"V4 retained fit evidence schema validation failed: {error}",
        ) from error

    if registry.calibration_artifact_sha256 != _sha256(artifact_path):
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.FIT_EVIDENCE_HASH_MISMATCH,
            "V4 registry calibration artifact hash does not match retained evidence",
        )
    if registry.calibration_fit_report_sha256 != _sha256(report_path):
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.FIT_EVIDENCE_HASH_MISMATCH,
            "V4 registry calibration fit report hash does not match retained evidence",
        )
    _verify_result_provenance(
        result=result,
        manifest=manifest,
        fixture_root=resolved_fixture_root,
    )
    return result


def write_regularized_isotonic_calibration_v4_fit(
    fixture_root: Path,
    output_directory: Path,
) -> RegularizedIsotonicCalibrationV4FitResult:
    """Write one deterministic V4 calibration-only artifact and fit report without overwrite."""

    fixture_set = load_regularized_isotonic_calibration_v4_fixture_set(fixture_root)
    result = fit_regularized_isotonic_calibration_v4(fixture_set)
    artifact_path = output_directory / _ARTIFACT_FILENAME
    report_path = output_directory / _FIT_REPORT_FILENAME
    if artifact_path.suffix != ".json" or report_path.suffix != ".json":
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.INVALID_DESTINATION,
            "V4 regularized-isotonic fit evidence destinations must be JSON files",
        )
    if artifact_path.exists() or report_path.exists():
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.DESTINATION_ALREADY_EXISTS,
            "V4 regularized-isotonic fit evidence is write-once and already exists",
        )

    artifact_bytes = _canonical_json_bytes(result.artifact.model_dump(mode="json"))
    report_bytes = _canonical_json_bytes(result.report.model_dump(mode="json"))
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("xb") as artifact_file:
            artifact_file.write(artifact_bytes)
        try:
            with report_path.open("xb") as report_file:
                report_file.write(report_bytes)
        except OSError:
            artifact_path.unlink(missing_ok=True)
            raise
    except FileExistsError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.DESTINATION_ALREADY_EXISTS,
            "V4 regularized-isotonic fit evidence is write-once and already exists",
        ) from error
    except OSError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.INVALID_DESTINATION,
            f"unable to write V4 regularized-isotonic fit evidence: {error}",
        ) from error
    return result


def _validate_calibration_only_fixture_set(
    fixture_set: RegularizedIsotonicCalibrationV4FixtureSet,
) -> None:
    if type(fixture_set) is not RegularizedIsotonicCalibrationV4FixtureSet:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.UNTRUSTED_FIXTURE_SET,
            "V4 fitting requires an exact verified V4 calibration fixture set",
        )
    manifest = fixture_set.manifest
    if (
        manifest.fixture_set_id != "synthetic-calibration-redesign-v4"
        or manifest.calibration_method_id != _ARTIFACT_ID
        or manifest.case_pair_count != 48
        or manifest.observation_count != 192
    ):
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.NON_CALIBRATION_EVIDENCE,
            "V4 fitting requires the frozen V4 calibration manifest",
        )
    if len(fixture_set.cases) != 48:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.NON_CALIBRATION_EVIDENCE,
            "V4 fitting requires exactly forty-eight calibration case pairs",
        )
    for replay_case in fixture_set.cases:
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes
        if (
            runtime.split is not TraceSplit.CALIBRATION
            or runtime.data_role is not TraceDataRole.CALIBRATION
            or outcomes.split is not TraceSplit.CALIBRATION
            or outcomes.data_role is not TraceDataRole.CALIBRATION
        ):
            raise RegularizedIsotonicCalibrationV4FitError(
                RegularizedIsotonicCalibrationV4ViolationCode.NON_CALIBRATION_EVIDENCE,
                "V4 fitting cannot consume non-calibration evidence",
            )


def _extract_fit_samples(
    fixture_set: RegularizedIsotonicCalibrationV4FixtureSet,
) -> tuple[_FitSample, ...]:
    samples: list[_FitSample] = []
    for replay_case in fixture_set.cases:
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in replay_case.expected_outcomes.outcomes
        }
        for context in replay_case.runtime_input.contexts:
            raw_confidence = context.conditional_survival_confidence
            _validate_raw_confidence(raw_confidence)
            outcome = outcomes_by_key[
                (context.decode_round, context.block_position_index)
            ]
            samples.append(
                _FitSample(
                    raw_confidence=raw_confidence,
                    observed_acceptance=int(outcome.observed_acceptance),
                    case_id=replay_case.runtime_input.case_id,
                    block_position_index=context.block_position_index,
                )
            )
    return tuple(
        sorted(
            samples,
            key=lambda sample: (
                sample.raw_confidence,
                sample.case_id,
                sample.block_position_index,
            ),
        )
    )


def _build_initial_bins(
    grouped_samples: tuple[tuple[_FitSample, ...], ...],
    protocol: RegularizedIsotonicCalibrationV4FitProtocol,
) -> tuple[RegularizedIsotonicCalibrationV4Bin, ...]:
    bins: list[RegularizedIsotonicCalibrationV4Bin] = []
    for index, samples in enumerate(grouped_samples, start=1):
        positive_label_count = sum(sample.observed_acceptance for sample in samples)
        sample_count = len(samples)
        smoothed_rate = (positive_label_count + protocol.laplace_success_prior) / (
            sample_count + protocol.laplace_total_prior
        )
        bins.append(
            RegularizedIsotonicCalibrationV4Bin(
                group_index=index,
                raw_confidence_lower_bound=samples[0].raw_confidence,
                raw_confidence_upper_bound=samples[-1].raw_confidence,
                sample_count=sample_count,
                positive_label_count=positive_label_count,
                negative_label_count=sample_count - positive_label_count,
                laplace_smoothed_acceptance_rate=smoothed_rate,
                pooled_block_index=index,
                calibrated_confidence=max(
                    protocol.output_lower_bound,
                    min(protocol.output_upper_bound, smoothed_rate),
                ),
            )
        )
    return tuple(bins)


def _weighted_pooled_adjacent_violators(
    bins: tuple[RegularizedIsotonicCalibrationV4Bin, ...],
) -> tuple[_PooledBlock, ...]:
    blocks: list[_PooledBlock] = []
    for bin_ in bins:
        blocks.append(
            _PooledBlock(
                first_group_index=bin_.group_index,
                last_group_index=bin_.group_index,
                weight=bin_.sample_count,
                weighted_rate_sum=(
                    bin_.laplace_smoothed_acceptance_rate * bin_.sample_count
                ),
            )
        )
        while len(blocks) >= 2 and (
            blocks[-2].calibrated_confidence > blocks[-1].calibrated_confidence
        ):
            right = blocks.pop()
            left = blocks.pop()
            blocks.append(
                _PooledBlock(
                    first_group_index=left.first_group_index,
                    last_group_index=right.last_group_index,
                    weight=left.weight + right.weight,
                    weighted_rate_sum=left.weighted_rate_sum + right.weighted_rate_sum,
                )
            )
    return tuple(blocks)


def _materialize_bins(
    initial_bins: tuple[RegularizedIsotonicCalibrationV4Bin, ...],
    pooled_blocks: tuple[_PooledBlock, ...],
    protocol: RegularizedIsotonicCalibrationV4FitProtocol,
) -> tuple[RegularizedIsotonicCalibrationV4Bin, ...]:
    materialized: list[RegularizedIsotonicCalibrationV4Bin] = []
    for bin_ in initial_bins:
        matching_block_index, matching_block = next(
            (index, block)
            for index, block in enumerate(pooled_blocks, start=1)
            if block.first_group_index <= bin_.group_index <= block.last_group_index
        )
        calibrated_confidence = max(
            protocol.output_lower_bound,
            min(protocol.output_upper_bound, matching_block.calibrated_confidence),
        )
        materialized.append(
            bin_.model_copy(
                update={
                    "pooled_block_index": matching_block_index,
                    "calibrated_confidence": calibrated_confidence,
                }
            )
        )
    return tuple(materialized)


def _build_artifact(
    *,
    fixture_set: RegularizedIsotonicCalibrationV4FixtureSet,
    protocol: RegularizedIsotonicCalibrationV4FitProtocol,
    bins: tuple[RegularizedIsotonicCalibrationV4Bin, ...],
    sample_count: int,
    positive_label_count: int,
    negative_label_count: int,
    group_size: int,
) -> RegularizedIsotonicCalibrationV4Artifact:
    manifest = fixture_set.manifest
    samples = _extract_fit_samples(fixture_set)
    raw_confidences = tuple(sample.raw_confidence for sample in samples)
    calibrated_confidences = tuple(
        _calibrate_with_bins(sample.raw_confidence, bins) for sample in samples
    )
    labels = tuple(bool(sample.observed_acceptance) for sample in samples)
    return RegularizedIsotonicCalibrationV4Artifact(
        schema_version="regularized-isotonic-calibration-v4-artifact-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=manifest.fixture_set_id,
        fixture_set_version=manifest.fixture_set_version,
        calibration_manifest_sha256=_sha256(
            fixture_set.root / "calibration_manifest.json"
        ),
        calibration_manifest_aggregate_sha256=manifest.aggregate_sha256,
        calibration_registry_sha256=manifest.registry_sha256,
        source_type=TraceSourceType.SYNTHETIC,
        fit_split=TraceSplit.CALIBRATION,
        fit_data_role=TraceDataRole.CALIBRATION,
        fit_case_ids=tuple(case.runtime_input.case_id for case in fixture_set.cases),
        fit_scenario_family_ids=tuple(
            sorted(
                {case.runtime_input.scenario_family_id for case in fixture_set.cases}
            )
        ),
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        equal_count_group_count=protocol.equal_count_group_count,
        equal_count_group_size=group_size,
        minimum_observations_per_group=protocol.minimum_observations_per_group,
        laplace_success_prior=protocol.laplace_success_prior,
        laplace_total_prior=protocol.laplace_total_prior,
        output_lower_bound=protocol.output_lower_bound,
        output_upper_bound=protocol.output_upper_bound,
        bins=bins,
        raw_brier_score=_brier_score(raw_confidences, labels),
        calibrated_brier_score=_brier_score(calibrated_confidences, labels),
        raw_ece_10_bin=_ece_10_bin(raw_confidences, labels),
        calibrated_ece_10_bin=_ece_10_bin(calibrated_confidences, labels),
        raw_auroc=calculate_tie_aware_auroc(raw_confidences, labels),
        calibrated_auroc=calculate_tie_aware_auroc(calibrated_confidences, labels),
        final_evaluation_accessed=False,
        calibration_refit_performed=False,
        scheduler_or_policy_execution_performed=False,
        runtime_control_eligible=False,
    )


def _calibrate_with_bins(
    raw_confidence: float,
    bins: tuple[RegularizedIsotonicCalibrationV4Bin, ...],
) -> float:
    _validate_raw_confidence(raw_confidence)
    for bin_ in bins:
        if raw_confidence <= bin_.raw_confidence_upper_bound:
            return bin_.calibrated_confidence
    return bins[-1].calibrated_confidence


def _brier_score(probabilities: tuple[float, ...], labels: tuple[bool, ...]) -> float:
    _validate_probability_label_inputs(probabilities, labels)
    return sum(
        (probability - float(label)) ** 2
        for probability, label in zip(
            probabilities,
            labels,
            strict=True,
        )
    ) / len(probabilities)


def _ece_10_bin(probabilities: tuple[float, ...], labels: tuple[bool, ...]) -> float:
    _validate_probability_label_inputs(probabilities, labels)
    bins: list[list[tuple[float, bool]]] = [[] for _ in range(_ECE_BIN_COUNT)]
    for probability, label in zip(probabilities, labels, strict=True):
        bins[min(int(probability * _ECE_BIN_COUNT), _ECE_BIN_COUNT - 1)].append(
            (probability, label)
        )
    total = len(probabilities)
    ece = 0.0
    for bin_items in bins:
        if not bin_items:
            continue
        mean_confidence = sum(item[0] for item in bin_items) / len(bin_items)
        mean_accuracy = sum(float(item[1]) for item in bin_items) / len(bin_items)
        ece += (len(bin_items) / total) * abs(mean_confidence - mean_accuracy)
    return ece


def _validate_raw_confidence(raw_confidence: float) -> None:
    if not isfinite(raw_confidence):
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.NON_FINITE_CONFIDENCE,
            "raw confidence must be finite before V4 regularized-isotonic calibration",
        )
    if raw_confidence < 0.0 or raw_confidence > 1.0:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.INVALID_RAW_CONFIDENCE,
            "raw confidence must be inside the closed unit interval",
        )


def _validate_probability_label_inputs(
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
) -> None:
    if len(probabilities) != len(labels) or len(probabilities) < 2:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.ARTIFACT_SCHEMA_ERROR,
            "probabilities and labels must have equal length of at least two",
        )
    for probability in probabilities:
        _validate_raw_confidence(probability)


def _verify_result_provenance(
    *,
    result: RegularizedIsotonicCalibrationV4FitResult,
    manifest: CalibrationRedesignV4CalibrationManifest,
    fixture_root: Path,
) -> None:
    expected_manifest_sha256 = _sha256(fixture_root / "calibration_manifest.json")
    for value in (
        result.artifact.calibration_manifest_sha256,
        result.report.calibration_manifest_sha256,
    ):
        if value != expected_manifest_sha256:
            raise RegularizedIsotonicCalibrationV4FitError(
                RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
                "V4 retained fit evidence does not reference the current frozen manifest bytes",
            )
    for value in (
        result.artifact.calibration_manifest_aggregate_sha256,
        result.report.calibration_manifest_aggregate_sha256,
    ):
        if value != manifest.aggregate_sha256:
            raise RegularizedIsotonicCalibrationV4FitError(
                RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
                "V4 retained fit evidence does not reference the frozen asset aggregate",
            )
    for value in (
        result.artifact.calibration_registry_sha256,
        result.report.calibration_registry_sha256,
    ):
        if value != manifest.registry_sha256:
            raise RegularizedIsotonicCalibrationV4FitError(
                RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
                "V4 retained fit evidence does not reference the frozen registry snapshot",
            )


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_bytes().decode("utf-8"))
    except OSError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.FIT_EVIDENCE_READ_ERROR,
            f"unable to read V4 retained fit evidence {path.name}: {error}",
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.ARTIFACT_SCHEMA_ERROR,
            f"V4 retained fit evidence is not valid UTF-8 JSON: {path.name}: {error}",
        ) from error
    if not isinstance(payload, dict):
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.ARTIFACT_SCHEMA_ERROR,
            f"V4 retained fit evidence must be a JSON object: {path.name}",
        )
    return payload


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise RegularizedIsotonicCalibrationV4FitError(
            RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE,
            f"unable to read V4 calibration provenance input {path.name}: {error}",
        ) from error


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
