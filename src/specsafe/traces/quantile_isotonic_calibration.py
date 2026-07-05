"""Deterministic V3 quantile-isotonic calibration fit.

This module consumes only the hash-verified V3 calibration manifest. It cannot load
V3 final-evaluation or adversarial assets, make a promotion decision, or emit policy
actions. The fitted map is retained as calibration-only evidence until a later locked
held-out assessment decides whether it is fit for automated scheduling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from specsafe.contracts.models import StrictContract, TraceDataRole, TraceSourceType, TraceSplit
from specsafe.traces.calibration_redesign_v3_manifest import (
    CalibrationRedesignV3CalibrationManifestedFixtureSet,
    load_calibration_redesign_v3_calibration_manifested_fixture_set,
)

_ARTIFACT_ID = "quantile-isotonic-calibration-v1"
_ARTIFACT_VERSION = "1.0.0"
_PROTOCOL_ID = "quantile_isotonic_calibration_fit_protocol_v1"
_ARTIFACT_FILENAME = "artifact.json"
_FIT_REPORT_FILENAME = "fit_report.json"
_GROUP_COUNT = 8
_MINIMUM_GROUP_OBSERVATIONS = 12
_LAPLACE_SUCCESS_PRIOR = 1
_LAPLACE_TOTAL_PRIOR = 2
_OUTPUT_LOWER_BOUND = 0.02
_OUTPUT_UPPER_BOUND = 0.98
_ECE_BIN_COUNT = 10


class QuantileIsotonicCalibrationViolationCode(StrEnum):
    """Machine-readable reasons the V3 calibration-only fit may be rejected."""

    UNTRUSTED_FIXTURE_SET = "untrusted_fixture_set"
    NON_CALIBRATION_EVIDENCE = "non_calibration_evidence"
    INSUFFICIENT_CALIBRATION_SAMPLES = "insufficient_calibration_samples"
    DEGENERATE_LABEL_DISTRIBUTION = "degenerate_label_distribution"
    NON_FINITE_CONFIDENCE = "non_finite_confidence"
    INVALID_RAW_CONFIDENCE = "invalid_raw_confidence"
    ARTIFACT_SCHEMA_ERROR = "artifact_schema_error"
    INVALID_DESTINATION = "invalid_destination"


class QuantileIsotonicCalibrationFitError(ValueError):
    """Typed error raised when the frozen V3 fit boundary is violated."""

    def __init__(self, code: QuantileIsotonicCalibrationViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class QuantileIsotonicCalibrationFitProtocol(StrictContract):
    """Predeclared V3 quantile, smoothing, and monotonic-pooling configuration."""

    protocol_id: Literal["quantile_isotonic_calibration_fit_protocol_v1"] = _PROTOCOL_ID
    quantile_group_count: Literal[8] = _GROUP_COUNT
    minimum_observations_per_group: Literal[12] = _MINIMUM_GROUP_OBSERVATIONS
    laplace_success_prior: Literal[1] = _LAPLACE_SUCCESS_PRIOR
    laplace_total_prior: Literal[2] = _LAPLACE_TOTAL_PRIOR
    output_lower_bound: float = Field(default=_OUTPUT_LOWER_BOUND, gt=0.0, lt=0.5)
    output_upper_bound: float = Field(default=_OUTPUT_UPPER_BOUND, gt=0.5, lt=1.0)
    ece_bin_count: Literal[10] = _ECE_BIN_COUNT

    @model_validator(mode="after")
    def validate_output_bounds(self) -> QuantileIsotonicCalibrationFitProtocol:
        """Keep the frozen output bounds internally coherent."""

        if self.output_lower_bound >= self.output_upper_bound:
            raise ValueError("output lower bound must be less than output upper bound")
        return self


DEFAULT_QUANTILE_ISOTONIC_CALIBRATION_FIT_PROTOCOL = QuantileIsotonicCalibrationFitProtocol()


class QuantileIsotonicCalibrationBin(StrictContract):
    """One equal-count raw-confidence group after deterministic monotonic pooling."""

    quantile_index: int = Field(ge=1, le=_GROUP_COUNT)
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
        """Reject non-finite retained calibration values."""

        if not isfinite(value):
            raise ValueError("quantile-isotonic bin values must be finite")
        return value

    @model_validator(mode="after")
    def validate_bin_counts_and_bounds(self) -> QuantileIsotonicCalibrationBin:
        """Require an internally consistent quantile bin."""

        if self.raw_confidence_lower_bound > self.raw_confidence_upper_bound:
            raise ValueError("raw-confidence bin lower bound must not exceed upper bound")
        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("quantile bin label counts must sum to sample_count")
        return self


class QuantileIsotonicCalibrationArtifact(StrictContract):
    """Immutable V3 calibration-only map fitted from the frozen corpus."""

    schema_version: Literal["quantile-isotonic-calibration-artifact-v1"]
    artifact_id: Literal["quantile-isotonic-calibration-v1"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_type: Literal[TraceSourceType.SYNTHETIC]
    fit_split: Literal[TraceSplit.CALIBRATION]
    fit_data_role: Literal[TraceDataRole.CALIBRATION]
    fit_case_ids: tuple[str, ...] = Field(min_length=36, max_length=36)
    fit_scenario_family_ids: tuple[str, ...] = Field(min_length=3, max_length=3)
    sample_count: Literal[144]
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    quantile_group_count: Literal[8]
    equal_count_group_size: Literal[18]
    minimum_observations_per_group: Literal[12]
    laplace_success_prior: Literal[1]
    laplace_total_prior: Literal[2]
    output_lower_bound: float = Field(ge=0.0, le=1.0)
    output_upper_bound: float = Field(ge=0.0, le=1.0)
    bins: tuple[QuantileIsotonicCalibrationBin, ...] = Field(min_length=8, max_length=8)
    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    raw_ece_10_bin: float = Field(ge=0.0, le=1.0)
    calibrated_ece_10_bin: float = Field(ge=0.0, le=1.0)
    final_evaluation_accessed: Literal[False]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "output_lower_bound",
        "output_upper_bound",
        "raw_brier_score",
        "calibrated_brier_score",
        "raw_ece_10_bin",
        "calibrated_ece_10_bin",
    )
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        """Reject non-finite artifact metrics and bounds."""

        if not isfinite(value):
            raise ValueError("quantile-isotonic artifact values must be finite")
        return value

    @model_validator(mode="after")
    def validate_artifact_shape(self) -> QuantileIsotonicCalibrationArtifact:
        """Require the retained map to remain monotonic and calibration-only."""

        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("artifact label counts must sum to sample_count")
        if self.output_lower_bound >= self.output_upper_bound:
            raise ValueError("artifact output bounds are invalid")
        if tuple(bin_.quantile_index for bin_ in self.bins) != tuple(range(1, 9)):
            raise ValueError("artifact bins must retain all eight quantile indices in order")
        previous_upper_bound = -1.0
        previous_calibrated_confidence = -1.0
        for bin_ in self.bins:
            if bin_.raw_confidence_lower_bound < previous_upper_bound:
                raise ValueError("artifact raw-confidence bins must be ordered")
            if bin_.calibrated_confidence < previous_calibrated_confidence:
                raise ValueError("artifact calibrated confidence must be non-decreasing")
            previous_upper_bound = bin_.raw_confidence_upper_bound
            previous_calibrated_confidence = bin_.calibrated_confidence
        return self

    def calibrate(self, raw_confidence: float) -> float:
        """Apply the frozen piecewise-constant monotonic V3 confidence map."""

        if not isfinite(raw_confidence):
            raise QuantileIsotonicCalibrationFitError(
                QuantileIsotonicCalibrationViolationCode.NON_FINITE_CONFIDENCE,
                "raw confidence must be finite before quantile-isotonic calibration",
            )
        if raw_confidence < 0.0 or raw_confidence > 1.0:
            raise QuantileIsotonicCalibrationFitError(
                QuantileIsotonicCalibrationViolationCode.INVALID_RAW_CONFIDENCE,
                "raw confidence must be inside the closed unit interval",
            )
        for bin_ in self.bins:
            if raw_confidence <= bin_.raw_confidence_upper_bound:
                return bin_.calibrated_confidence
        return self.bins[-1].calibrated_confidence


class QuantileIsotonicCalibrationFitReport(StrictContract):
    """Retained calibration-only report with no held-out claim or promotion decision."""

    schema_version: Literal["quantile-isotonic-calibration-fit-report-v1"]
    artifact_id: Literal["quantile-isotonic-calibration-v1"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    calibration_manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fit_scope: Literal["calibration_split_only"]
    method: Literal["equal_count_quantiles_laplace_smoothed_weighted_pav"]
    sample_count: Literal[144]
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    quantile_group_count: Literal[8]
    equal_count_group_size: Literal[18]
    pooled_block_count: int = Field(ge=1, le=8)
    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    raw_ece_10_bin: float = Field(ge=0.0, le=1.0)
    calibrated_ece_10_bin: float = Field(ge=0.0, le=1.0)
    failure_status: Literal["none"]
    final_evaluation_accessed: Literal[False]
    heldout_calibration_gate_status: Literal["not_assessed"]
    promotion_status: Literal["not_assessed"]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "raw_brier_score",
        "calibrated_brier_score",
        "raw_ece_10_bin",
        "calibrated_ece_10_bin",
    )
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        """Reject non-finite fit-report metrics."""

        if not isfinite(value):
            raise ValueError("quantile-isotonic fit-report metrics must be finite")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> QuantileIsotonicCalibrationFitReport:
        """Keep retained fit counts internally consistent."""

        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("fit-report label counts must sum to sample_count")
        return self


class QuantileIsotonicCalibrationFitResult(StrictContract):
    """Typed pairing of a frozen V3 artifact and calibration-only report."""

    artifact: QuantileIsotonicCalibrationArtifact
    report: QuantileIsotonicCalibrationFitReport

    @model_validator(mode="after")
    def validate_artifact_report_alignment(self) -> QuantileIsotonicCalibrationFitResult:
        """Prevent the retained report from drifting away from its fitted artifact."""

        aligned_fields = (
            "artifact_id",
            "artifact_version",
            "fixture_set_id",
            "fixture_set_version",
            "calibration_manifest_aggregate_sha256",
            "sample_count",
            "positive_label_count",
            "negative_label_count",
            "quantile_group_count",
            "equal_count_group_size",
            "raw_brier_score",
            "calibrated_brier_score",
            "raw_ece_10_bin",
            "calibrated_ece_10_bin",
            "final_evaluation_accessed",
            "runtime_control_eligible",
        )
        for field_name in aligned_fields:
            if getattr(self.artifact, field_name) != getattr(self.report, field_name):
                raise ValueError(f"artifact and fit report disagree on {field_name}")
        return self


@dataclass(frozen=True)
class _FitSample:
    raw_confidence: float
    observed_acceptance: int
    case_id: str
    block_position_index: int


@dataclass(frozen=True)
class _PooledBlock:
    first_quantile_index: int
    last_quantile_index: int
    weight: int
    weighted_rate_sum: float

    @property
    def calibrated_confidence(self) -> float:
        return self.weighted_rate_sum / self.weight


def fit_quantile_isotonic_calibration(
    fixture_set: CalibrationRedesignV3CalibrationManifestedFixtureSet,
    *,
    protocol: QuantileIsotonicCalibrationFitProtocol = (
        DEFAULT_QUANTILE_ISOTONIC_CALIBRATION_FIT_PROTOCOL
    ),
) -> QuantileIsotonicCalibrationFitResult:
    """Fit the predeclared V3 map using only verified frozen calibration evidence."""

    _validate_calibration_only_fixture_set(fixture_set)
    if not isinstance(protocol, QuantileIsotonicCalibrationFitProtocol):
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.ARTIFACT_SCHEMA_ERROR,
            "V3 quantile-isotonic fitting requires the frozen typed fit protocol",
        )

    samples = _extract_fit_samples(fixture_set)
    sample_count = len(samples)
    if sample_count % protocol.quantile_group_count != 0:
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.INSUFFICIENT_CALIBRATION_SAMPLES,
            "V3 calibration sample count must divide evenly across the fixed quantile count",
        )
    group_size = sample_count // protocol.quantile_group_count
    if group_size < protocol.minimum_observations_per_group:
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.INSUFFICIENT_CALIBRATION_SAMPLES,
            "V3 calibration corpus does not meet the fixed minimum quantile group size",
        )

    positive_label_count = sum(sample.observed_acceptance for sample in samples)
    negative_label_count = sample_count - positive_label_count
    if positive_label_count == 0 or negative_label_count == 0:
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.DEGENERATE_LABEL_DISTRIBUTION,
            "V3 quantile-isotonic fitting requires both accepted and rejected observations",
        )

    quantile_samples = tuple(
        tuple(samples[index : index + group_size])
        for index in range(0, sample_count, group_size)
    )
    initial_bins = _build_initial_bins(quantile_samples, protocol)
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
    report = QuantileIsotonicCalibrationFitReport(
        schema_version="quantile-isotonic-calibration-fit-report-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=artifact.fixture_set_id,
        fixture_set_version=artifact.fixture_set_version,
        calibration_manifest_aggregate_sha256=artifact.calibration_manifest_aggregate_sha256,
        fit_scope="calibration_split_only",
        method="equal_count_quantiles_laplace_smoothed_weighted_pav",
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        quantile_group_count=protocol.quantile_group_count,
        equal_count_group_size=group_size,
        pooled_block_count=len(pooled_blocks),
        raw_brier_score=artifact.raw_brier_score,
        calibrated_brier_score=artifact.calibrated_brier_score,
        raw_ece_10_bin=artifact.raw_ece_10_bin,
        calibrated_ece_10_bin=artifact.calibrated_ece_10_bin,
        failure_status="none",
        final_evaluation_accessed=False,
        heldout_calibration_gate_status="not_assessed",
        promotion_status="not_assessed",
        runtime_control_eligible=False,
    )
    return QuantileIsotonicCalibrationFitResult(artifact=artifact, report=report)


def write_quantile_isotonic_calibration_fit(
    fixture_root: Path,
    output_directory: Path,
) -> QuantileIsotonicCalibrationFitResult:
    """Write deterministic V3 calibration-only artifact and report JSON files."""

    fixture_set = load_calibration_redesign_v3_calibration_manifested_fixture_set(fixture_root)
    result = fit_quantile_isotonic_calibration(fixture_set)
    output_directory.mkdir(parents=True, exist_ok=True)
    artifact_path = output_directory / _ARTIFACT_FILENAME
    report_path = output_directory / _FIT_REPORT_FILENAME
    if artifact_path.suffix != ".json" or report_path.suffix != ".json":
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.INVALID_DESTINATION,
            "quantile-isotonic fit evidence destinations must be JSON files",
        )
    _write_json(artifact_path, result.artifact.model_dump(mode="json"))
    _write_json(report_path, result.report.model_dump(mode="json"))
    return result


def _validate_calibration_only_fixture_set(
    fixture_set: CalibrationRedesignV3CalibrationManifestedFixtureSet,
) -> None:
    if not isinstance(fixture_set, CalibrationRedesignV3CalibrationManifestedFixtureSet):
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.UNTRUSTED_FIXTURE_SET,
            "V3 quantile-isotonic fitting requires a verified V3 calibration fixture set",
        )
    manifest = fixture_set.manifest
    if (
        manifest.fixture_set_id != "synthetic-calibration-redesign-v3"
        or manifest.calibration_method_id != _ARTIFACT_ID
        or manifest.case_count != 36
        or manifest.observation_count != 144
        or manifest.calibration_quantile_group_count != _GROUP_COUNT
    ):
        raise QuantileIsotonicCalibrationFitError(
            QuantileIsotonicCalibrationViolationCode.NON_CALIBRATION_EVIDENCE,
            "V3 quantile-isotonic fitting requires the frozen V3 calibration manifest",
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
            raise QuantileIsotonicCalibrationFitError(
                QuantileIsotonicCalibrationViolationCode.NON_CALIBRATION_EVIDENCE,
                "V3 quantile-isotonic fitting cannot consume non-calibration evidence",
            )


def _extract_fit_samples(
    fixture_set: CalibrationRedesignV3CalibrationManifestedFixtureSet,
) -> tuple[_FitSample, ...]:
    samples: list[_FitSample] = []
    for replay_case in fixture_set.cases:
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in replay_case.expected_outcomes.outcomes
        }
        for context in replay_case.runtime_input.contexts:
            raw_confidence = context.conditional_survival_confidence
            if not isfinite(raw_confidence):
                raise QuantileIsotonicCalibrationFitError(
                    QuantileIsotonicCalibrationViolationCode.NON_FINITE_CONFIDENCE,
                    "V3 calibration confidence must be finite",
                )
            if raw_confidence < 0.0 or raw_confidence > 1.0:
                raise QuantileIsotonicCalibrationFitError(
                    QuantileIsotonicCalibrationViolationCode.INVALID_RAW_CONFIDENCE,
                    "V3 calibration confidence must be inside the closed unit interval",
                )
            outcome = outcomes_by_key[(context.decode_round, context.block_position_index)]
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
    quantile_samples: tuple[tuple[_FitSample, ...], ...],
    protocol: QuantileIsotonicCalibrationFitProtocol,
) -> tuple[QuantileIsotonicCalibrationBin, ...]:
    bins: list[QuantileIsotonicCalibrationBin] = []
    for index, samples in enumerate(quantile_samples, start=1):
        positive_label_count = sum(sample.observed_acceptance for sample in samples)
        sample_count = len(samples)
        smoothed_rate = (
            positive_label_count + protocol.laplace_success_prior
        ) / (sample_count + protocol.laplace_total_prior)
        bins.append(
            QuantileIsotonicCalibrationBin(
                quantile_index=index,
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
    bins: tuple[QuantileIsotonicCalibrationBin, ...],
) -> tuple[_PooledBlock, ...]:
    blocks: list[_PooledBlock] = []
    for bin_ in bins:
        blocks.append(
            _PooledBlock(
                first_quantile_index=bin_.quantile_index,
                last_quantile_index=bin_.quantile_index,
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
                    first_quantile_index=left.first_quantile_index,
                    last_quantile_index=right.last_quantile_index,
                    weight=left.weight + right.weight,
                    weighted_rate_sum=left.weighted_rate_sum + right.weighted_rate_sum,
                )
            )
    return tuple(blocks)


def _materialize_bins(
    initial_bins: tuple[QuantileIsotonicCalibrationBin, ...],
    pooled_blocks: tuple[_PooledBlock, ...],
    protocol: QuantileIsotonicCalibrationFitProtocol,
) -> tuple[QuantileIsotonicCalibrationBin, ...]:
    materialized: list[QuantileIsotonicCalibrationBin] = []
    for bin_ in initial_bins:
        matching_block_index, matching_block = next(
            (index, block)
            for index, block in enumerate(pooled_blocks, start=1)
            if block.first_quantile_index <= bin_.quantile_index <= block.last_quantile_index
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
    fixture_set: CalibrationRedesignV3CalibrationManifestedFixtureSet,
    protocol: QuantileIsotonicCalibrationFitProtocol,
    bins: tuple[QuantileIsotonicCalibrationBin, ...],
    sample_count: int,
    positive_label_count: int,
    negative_label_count: int,
    group_size: int,
) -> QuantileIsotonicCalibrationArtifact:
    manifest = fixture_set.manifest
    samples = _extract_fit_samples(fixture_set)
    calibrated_confidences = tuple(
        _calibrate_with_bins(sample.raw_confidence, bins) for sample in samples
    )
    labels = tuple(sample.observed_acceptance for sample in samples)
    return QuantileIsotonicCalibrationArtifact(
        schema_version="quantile-isotonic-calibration-artifact-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=manifest.fixture_set_id,
        fixture_set_version=manifest.fixture_set_version,
        calibration_manifest_aggregate_sha256=manifest.aggregate_sha256,
        source_type=TraceSourceType.SYNTHETIC,
        fit_split=TraceSplit.CALIBRATION,
        fit_data_role=TraceDataRole.CALIBRATION,
        fit_case_ids=tuple(sorted(case.runtime_input.case_id for case in fixture_set.cases)),
        fit_scenario_family_ids=tuple(
            sorted({case.runtime_input.scenario_family_id for case in fixture_set.cases})
        ),
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        quantile_group_count=protocol.quantile_group_count,
        equal_count_group_size=group_size,
        minimum_observations_per_group=protocol.minimum_observations_per_group,
        laplace_success_prior=protocol.laplace_success_prior,
        laplace_total_prior=protocol.laplace_total_prior,
        output_lower_bound=protocol.output_lower_bound,
        output_upper_bound=protocol.output_upper_bound,
        bins=bins,
        raw_brier_score=_brier_score(
            tuple(sample.raw_confidence for sample in samples),
            labels,
        ),
        calibrated_brier_score=_brier_score(calibrated_confidences, labels),
        raw_ece_10_bin=_expected_calibration_error(
            tuple(sample.raw_confidence for sample in samples),
            labels,
            protocol.ece_bin_count,
        ),
        calibrated_ece_10_bin=_expected_calibration_error(
            calibrated_confidences,
            labels,
            protocol.ece_bin_count,
        ),
        final_evaluation_accessed=False,
        runtime_control_eligible=False,
    )


def _calibrate_with_bins(
    raw_confidence: float,
    bins: tuple[QuantileIsotonicCalibrationBin, ...],
) -> float:
    for bin_ in bins:
        if raw_confidence <= bin_.raw_confidence_upper_bound:
            return bin_.calibrated_confidence
    return bins[-1].calibrated_confidence


def _brier_score(confidences: tuple[float, ...], labels: tuple[int, ...]) -> float:
    return sum(
        (confidence - label) ** 2 for confidence, label in zip(confidences, labels, strict=True)
    ) / len(confidences)


def _expected_calibration_error(
    confidences: tuple[float, ...],
    labels: tuple[int, ...],
    bin_count: int,
) -> float:
    weighted_error = 0.0
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        members = tuple(
            (confidence, label)
            for confidence, label in zip(confidences, labels, strict=True)
            if lower <= confidence and (
                confidence < upper or index == bin_count - 1 and confidence <= upper
            )
        )
        if not members:
            continue
        average_confidence = sum(item[0] for item in members) / len(members)
        observed_frequency = sum(item[1] for item in members) / len(members)
        weighted_error += len(members) / len(confidences) * abs(
            average_confidence - observed_frequency
        )
    return weighted_error


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_bytes(
        (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
            )
            + "\n"
        ).encode("utf-8")
    )
