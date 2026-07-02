"""Calibration-only fitting for the governed logit-temperature-scaling artifact."""

from __future__ import annotations

import json
from enum import StrEnum
from math import exp, isfinite, log
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from specsafe.contracts import TraceDataRole, TraceSourceType, TraceSplit
from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_redesign_manifest import (
    CalibrationRedesignManifestedFixtureSet,
)

_ARTIFACT_ID = "logit-temperature-scaling-v1"
_ARTIFACT_VERSION = "1.0.0"
_EPSILON = 1e-6
_LOG_TEMPERATURE_LOWER = -3.0
_LOG_TEMPERATURE_UPPER = 3.0
_SEARCH_ITERATIONS = 96


class LogitTemperatureScalingViolationCode(StrEnum):
    """Machine-readable reasons calibration-only fitting may be rejected."""

    UNTRUSTED_FIXTURE_SET = "untrusted_fixture_set"
    NON_CALIBRATION_EVIDENCE = "non_calibration_evidence"
    INSUFFICIENT_CALIBRATION_SAMPLES = "insufficient_calibration_samples"
    DEGENERATE_LABEL_DISTRIBUTION = "degenerate_label_distribution"
    NON_FINITE_CONFIDENCE = "non_finite_confidence"
    ARTIFACT_SCHEMA_ERROR = "artifact_schema_error"


class LogitTemperatureScalingFitError(ValueError):
    """Typed error raised when a temperature-scaling fit boundary is violated."""

    def __init__(self, code: LogitTemperatureScalingViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class LogitTemperatureScalingArtifact(StrictContract):
    """Frozen temperature-scaling artifact fitted only from a verified calibration manifest."""

    schema_version: Literal["logit-temperature-scaling-artifact-v1"]
    artifact_id: Literal["logit-temperature-scaling-v1"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    fixture_set_version: str = Field(min_length=1, max_length=64)
    manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_type: Literal[TraceSourceType.SYNTHETIC]
    fit_split: Literal[TraceSplit.CALIBRATION]
    fit_data_role: Literal[TraceDataRole.CALIBRATION]
    scenario_family_ids: tuple[str, ...] = Field(min_length=2)
    fitted_case_ids: tuple[str, ...] = Field(min_length=1)
    sample_count: int = Field(gt=0)
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    temperature: float = Field(gt=0.0)
    log_temperature: float
    raw_negative_log_likelihood: float = Field(ge=0.0)
    calibrated_negative_log_likelihood: float = Field(ge=0.0)
    final_evaluation_accessed: Literal[False]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "log_temperature",
        "raw_negative_log_likelihood",
        "calibrated_negative_log_likelihood",
    )
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        """Reject non-finite artifact values before a result can be retained."""

        if not isfinite(value):
            raise ValueError("temperature-scaling artifact values must be finite")
        return value

    @model_validator(mode="after")
    def validate_counts_and_temperature(self) -> LogitTemperatureScalingArtifact:
        """Keep artifact counts and numeric representation internally consistent."""

        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("label counts must sum to sample_count")
        if abs(log(self.temperature) - self.log_temperature) > 1e-9:
            raise ValueError("temperature and log_temperature must represent the same value")
        return self

    def calibrate(self, raw_confidence: float) -> float:
        """Apply the frozen monotonic temperature transform to one raw confidence value."""

        return _temperature_scaled_probability(raw_confidence, self.temperature)


class LogitTemperatureScalingFitReport(StrictContract):
    """Retained in-sample fit record that is explicitly not a promotion decision."""

    schema_version: Literal["logit-temperature-scaling-fit-report-v1"]
    artifact_id: Literal["logit-temperature-scaling-v1"]
    artifact_version: Literal["1.0.0"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    fixture_set_version: str = Field(min_length=1, max_length=64)
    manifest_aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fit_scope: Literal["calibration_split_only"]
    objective: Literal["mean_negative_log_likelihood"]
    search_log_temperature_lower: float
    search_log_temperature_upper: float
    search_iterations: int = Field(gt=0)
    sample_count: int = Field(gt=0)
    positive_label_count: int = Field(gt=0)
    negative_label_count: int = Field(gt=0)
    raw_negative_log_likelihood: float = Field(ge=0.0)
    calibrated_negative_log_likelihood: float = Field(ge=0.0)
    final_evaluation_accessed: Literal[False]
    promotion_status: Literal["not_assessed"]
    runtime_control_eligible: Literal[False]

    @field_validator(
        "search_log_temperature_lower",
        "search_log_temperature_upper",
        "raw_negative_log_likelihood",
        "calibrated_negative_log_likelihood",
    )
    @classmethod
    def validate_finite_metrics(cls, value: float) -> float:
        """Reject non-finite fit-report values before they can become evidence."""

        if not isfinite(value):
            raise ValueError("temperature-scaling fit-report values must be finite")
        return value

    @model_validator(mode="after")
    def validate_counts_and_search_bounds(self) -> LogitTemperatureScalingFitReport:
        """Keep report counts and the predeclared search interval coherent."""

        if self.positive_label_count + self.negative_label_count != self.sample_count:
            raise ValueError("label counts must sum to sample_count")
        if self.search_log_temperature_lower >= self.search_log_temperature_upper:
            raise ValueError("log-temperature search lower bound must be less than upper bound")
        return self


class LogitTemperatureScalingFitResult(StrictContract):
    """Typed pairing of a frozen artifact and its retained calibration-only fit report."""

    artifact: LogitTemperatureScalingArtifact
    report: LogitTemperatureScalingFitReport

    @model_validator(mode="after")
    def validate_artifact_report_alignment(self) -> LogitTemperatureScalingFitResult:
        """Prevent a report from being detached from the artifact it describes."""

        artifact = self.artifact
        report = self.report
        aligned_fields = (
            "artifact_id",
            "artifact_version",
            "fixture_set_id",
            "fixture_set_version",
            "manifest_aggregate_sha256",
            "sample_count",
            "positive_label_count",
            "negative_label_count",
            "raw_negative_log_likelihood",
            "calibrated_negative_log_likelihood",
            "final_evaluation_accessed",
            "runtime_control_eligible",
        )
        for field_name in aligned_fields:
            if getattr(artifact, field_name) != getattr(report, field_name):
                raise ValueError(f"artifact and fit report disagree on {field_name}")
        return self


def fit_logit_temperature_scaling(
    fixture_set: CalibrationRedesignManifestedFixtureSet,
) -> LogitTemperatureScalingFitResult:
    """Fit the predeclared calibrator using only a verified calibration-only fixture set."""

    _validate_calibration_only_fixture_set(fixture_set)
    probabilities, labels = _extract_fit_samples(fixture_set)
    sample_count = len(probabilities)
    positive_label_count = sum(labels)
    negative_label_count = sample_count - positive_label_count
    if sample_count < 2:
        raise LogitTemperatureScalingFitError(
            LogitTemperatureScalingViolationCode.INSUFFICIENT_CALIBRATION_SAMPLES,
            "temperature scaling requires at least two calibration samples",
        )
    if positive_label_count == 0 or negative_label_count == 0:
        raise LogitTemperatureScalingFitError(
            LogitTemperatureScalingViolationCode.DEGENERATE_LABEL_DISTRIBUTION,
            "temperature scaling requires both accepted and rejected calibration labels",
        )

    log_temperature = _minimize_mean_negative_log_likelihood(probabilities, labels)
    temperature = exp(log_temperature)
    raw_loss = _mean_negative_log_likelihood(probabilities, labels, temperature=1.0)
    calibrated_loss = _mean_negative_log_likelihood(
        probabilities,
        labels,
        temperature=temperature,
    )
    manifest = fixture_set.manifest
    scenario_family_ids = tuple(
        sorted({case.runtime_input.scenario_family_id for case in fixture_set.cases})
    )
    fitted_case_ids = tuple(sorted(case.runtime_input.case_id for case in fixture_set.cases))

    artifact = LogitTemperatureScalingArtifact(
        schema_version="logit-temperature-scaling-artifact-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=manifest.fixture_set_id,
        fixture_set_version=manifest.fixture_set_version,
        manifest_aggregate_sha256=manifest.aggregate_sha256,
        source_type=TraceSourceType.SYNTHETIC,
        fit_split=TraceSplit.CALIBRATION,
        fit_data_role=TraceDataRole.CALIBRATION,
        scenario_family_ids=scenario_family_ids,
        fitted_case_ids=fitted_case_ids,
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        temperature=temperature,
        log_temperature=log_temperature,
        raw_negative_log_likelihood=raw_loss,
        calibrated_negative_log_likelihood=calibrated_loss,
        final_evaluation_accessed=False,
        runtime_control_eligible=False,
    )
    report = LogitTemperatureScalingFitReport(
        schema_version="logit-temperature-scaling-fit-report-v1",
        artifact_id=_ARTIFACT_ID,
        artifact_version=_ARTIFACT_VERSION,
        fixture_set_id=manifest.fixture_set_id,
        fixture_set_version=manifest.fixture_set_version,
        manifest_aggregate_sha256=manifest.aggregate_sha256,
        fit_scope="calibration_split_only",
        objective="mean_negative_log_likelihood",
        search_log_temperature_lower=_LOG_TEMPERATURE_LOWER,
        search_log_temperature_upper=_LOG_TEMPERATURE_UPPER,
        search_iterations=_SEARCH_ITERATIONS,
        sample_count=sample_count,
        positive_label_count=positive_label_count,
        negative_label_count=negative_label_count,
        raw_negative_log_likelihood=raw_loss,
        calibrated_negative_log_likelihood=calibrated_loss,
        final_evaluation_accessed=False,
        promotion_status="not_assessed",
        runtime_control_eligible=False,
    )
    return LogitTemperatureScalingFitResult(artifact=artifact, report=report)


def write_logit_temperature_scaling_fit(
    fixture_root: Path,
    output_directory: Path,
) -> LogitTemperatureScalingFitResult:
    """Load verified calibration evidence, fit it, and retain only artifact/report metadata."""

    from specsafe.traces.calibration_redesign_manifest import (
        load_calibration_redesign_manifested_fixture_set,
    )

    fixture_set = load_calibration_redesign_manifested_fixture_set(fixture_root)
    result = fit_logit_temperature_scaling(fixture_set)
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_json(output_directory / "artifact.json", result.artifact.model_dump(mode="json"))
    _write_json(output_directory / "fit_report.json", result.report.model_dump(mode="json"))
    return result


def _validate_calibration_only_fixture_set(
    fixture_set: CalibrationRedesignManifestedFixtureSet,
) -> None:
    """Recheck fitting preconditions even when the manifest loader already enforced them."""

    if not isinstance(fixture_set, CalibrationRedesignManifestedFixtureSet):
        raise LogitTemperatureScalingFitError(
            LogitTemperatureScalingViolationCode.UNTRUSTED_FIXTURE_SET,
            "temperature scaling requires a verified manifested calibration fixture set",
        )
    manifest = fixture_set.manifest
    if (
        manifest.source_type is not TraceSourceType.SYNTHETIC
        or manifest.case_count != len(fixture_set.cases)
    ):
        raise LogitTemperatureScalingFitError(
            LogitTemperatureScalingViolationCode.UNTRUSTED_FIXTURE_SET,
            "manifested fixture set does not satisfy trusted synthetic calibration invariants",
        )
    for replay_case in fixture_set.cases:
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes
        if (
            runtime.split is not TraceSplit.CALIBRATION
            or outcomes.split is not TraceSplit.CALIBRATION
            or runtime.data_role is not TraceDataRole.CALIBRATION
            or outcomes.data_role is not TraceDataRole.CALIBRATION
            or runtime.source_type is not TraceSourceType.SYNTHETIC
            or outcomes.source_type is not TraceSourceType.SYNTHETIC
        ):
            raise LogitTemperatureScalingFitError(
                LogitTemperatureScalingViolationCode.NON_CALIBRATION_EVIDENCE,
                "temperature scaling may consume only synthetic calibration-split evidence",
            )


def _extract_fit_samples(
    fixture_set: CalibrationRedesignManifestedFixtureSet,
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Extract aligned raw confidence and post-hoc labels after trusted loading completes."""

    probabilities: list[float] = []
    labels: list[int] = []
    for replay_case in fixture_set.cases:
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in replay_case.runtime_input.contexts
        }
        for outcome in replay_case.expected_outcomes.outcomes:
            key = (outcome.decode_round, outcome.block_position_index)
            context = contexts_by_key[key]
            confidence = context.conditional_survival_confidence
            if not isfinite(confidence):
                raise LogitTemperatureScalingFitError(
                    LogitTemperatureScalingViolationCode.NON_FINITE_CONFIDENCE,
                    "calibration confidence values must be finite",
                )
            probabilities.append(confidence)
            labels.append(int(outcome.observed_acceptance))
    return tuple(probabilities), tuple(labels)


def _minimize_mean_negative_log_likelihood(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
) -> float:
    """Minimize the convex one-dimensional fit objective over predeclared log-temperature bounds."""

    lower = _LOG_TEMPERATURE_LOWER
    upper = _LOG_TEMPERATURE_UPPER
    golden_ratio_complement = (5.0**0.5 - 1.0) / 2.0
    left = upper - golden_ratio_complement * (upper - lower)
    right = lower + golden_ratio_complement * (upper - lower)
    left_loss = _mean_negative_log_likelihood(probabilities, labels, exp(left))
    right_loss = _mean_negative_log_likelihood(probabilities, labels, exp(right))

    for _ in range(_SEARCH_ITERATIONS):
        if left_loss <= right_loss:
            upper = right
            right = left
            right_loss = left_loss
            left = upper - golden_ratio_complement * (upper - lower)
            left_loss = _mean_negative_log_likelihood(probabilities, labels, exp(left))
        else:
            lower = left
            left = right
            left_loss = right_loss
            right = lower + golden_ratio_complement * (upper - lower)
            right_loss = _mean_negative_log_likelihood(probabilities, labels, exp(right))
    return (lower + upper) / 2.0


def _mean_negative_log_likelihood(
    probabilities: tuple[float, ...],
    labels: tuple[int, ...],
    temperature: float,
) -> float:
    """Return mean binary negative log likelihood after a temperature transform."""

    losses = []
    for probability, label in zip(probabilities, labels, strict=True):
        calibrated = _temperature_scaled_probability(probability, temperature)
        if label == 1:
            losses.append(-log(calibrated))
        else:
            losses.append(-log(1.0 - calibrated))
    return sum(losses) / len(losses)


def _temperature_scaled_probability(raw_confidence: float, temperature: float) -> float:
    """Apply a numerically bounded logistic temperature transform."""

    if not isfinite(raw_confidence):
        raise LogitTemperatureScalingFitError(
            LogitTemperatureScalingViolationCode.NON_FINITE_CONFIDENCE,
            "raw confidence must be finite",
        )
    if not isfinite(temperature) or temperature <= 0.0:
        raise LogitTemperatureScalingFitError(
            LogitTemperatureScalingViolationCode.ARTIFACT_SCHEMA_ERROR,
            "temperature must be finite and greater than zero",
        )
    bounded = min(max(raw_confidence, _EPSILON), 1.0 - _EPSILON)
    logit = log(bounded / (1.0 - bounded))
    scaled_logit = logit / temperature
    if scaled_logit >= 0.0:
        return 1.0 / (1.0 + exp(-scaled_logit))
    exp_scaled_logit = exp(scaled_logit)
    return exp_scaled_logit / (1.0 + exp_scaled_logit)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a reviewable JSON evidence record with no raw fixture contents."""

    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
