"""Typed contracts for a frozen calibration artifact fitted on calibration data only."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts import TraceSplit
from specsafe.contracts.models import StrictContract


class CalibrationArtifactStatus(StrEnum):
    """Lifecycle state for a fitted artifact that still lacks held-out fitness evidence."""

    FROZEN_PENDING_HELD_OUT_FITNESS = "frozen_pending_held_out_fitness"


class CalibrationControlEligibility(StrEnum):
    """Hard boundary preventing a fitted artifact from authorizing runtime control."""

    NOT_ELIGIBLE_PENDING_HELD_OUT_FITNESS = "not_eligible_pending_held_out_fitness"


class CalibrationFitErrorCode(StrEnum):
    """Machine-readable failures for calibration-only artifact fitting and persistence."""

    INVALID_FIXTURE_SET = "invalid_fixture_set"
    NO_CALIBRATION_CASES = "no_calibration_cases"
    INSUFFICIENT_CALIBRATION_OBSERVATIONS = "insufficient_calibration_observations"
    INVALID_ARTIFACT = "invalid_artifact"
    INVALID_DESTINATION = "invalid_destination"


class FrozenCalibratorFitProtocol(StrictContract):
    """Predeclared fitting method for a calibration-split-only histogram artifact."""

    protocol_id: str = Field(
        default="frozen-histogram-calibrator-v1",
        min_length=1,
        max_length=128,
    )
    calibration_split: Literal[TraceSplit.CALIBRATION] = TraceSplit.CALIBRATION
    bin_count: int = Field(default=4, ge=2, le=20)
    minimum_observation_count: int = Field(default=8, ge=1)


class FrozenCalibratorBin(StrictContract):
    """One frozen histogram bin with source evidence and a deterministic applied value."""

    bin_index: int = Field(ge=0)
    lower_confidence_bound: float = Field(ge=0.0, le=1.0)
    upper_confidence_bound: float = Field(gt=0.0, le=1.0)
    source_observation_count: int = Field(ge=0)
    observed_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    applied_calibrated_probability: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_evidence_shape(self) -> FrozenCalibratorBin:
        """Keep empty-bin fallback values distinct from measured acceptance evidence."""

        if self.lower_confidence_bound >= self.upper_confidence_bound:
            raise ValueError("frozen calibrator bin lower bound must be below upper bound")
        if self.source_observation_count == 0 and self.observed_acceptance_rate is not None:
            raise ValueError("empty frozen bins must not report observed acceptance evidence")
        if self.source_observation_count > 0 and self.observed_acceptance_rate is None:
            raise ValueError("populated frozen bins require observed acceptance evidence")
        return self


class FrozenCalibratorArtifact(StrictContract):
    """Immutable calibration artifact awaiting a separately governed held-out assessment."""

    schema_version: Literal["frozen-histogram-calibrator-v1"] = "frozen-histogram-calibrator-v1"
    protocol: FrozenCalibratorFitProtocol
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source_split: Literal[TraceSplit.CALIBRATION] = TraceSplit.CALIBRATION
    calibration_case_ids: tuple[str, ...] = Field(min_length=1)
    calibration_trace_ids: tuple[str, ...] = Field(min_length=1)
    source_observation_count: int = Field(ge=1)
    global_observed_acceptance_rate: float = Field(ge=0.0, le=1.0)
    bins: tuple[FrozenCalibratorBin, ...] = Field(min_length=2)
    status: Literal[CalibrationArtifactStatus.FROZEN_PENDING_HELD_OUT_FITNESS] = (
        CalibrationArtifactStatus.FROZEN_PENDING_HELD_OUT_FITNESS
    )
    automation_control_eligibility: Literal[
        CalibrationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_FITNESS
    ] = CalibrationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_FITNESS

    @model_validator(mode="after")
    def validate_frozen_artifact_evidence(self) -> FrozenCalibratorArtifact:
        """Bind the immutable artifact to calibration-only source evidence."""

        if len(set(self.calibration_case_ids)) != len(self.calibration_case_ids):
            raise ValueError("calibration_case_ids must not contain duplicates")
        if len(set(self.calibration_trace_ids)) != len(self.calibration_trace_ids):
            raise ValueError("calibration_trace_ids must not contain duplicates")
        if len(self.bins) != self.protocol.bin_count:
            raise ValueError("frozen calibrator bins must match protocol bin_count")
        if sum(bin_summary.source_observation_count for bin_summary in self.bins) != (
            self.source_observation_count
        ):
            raise ValueError("frozen calibrator bin counts must equal source_observation_count")
        expected_indices = tuple(range(self.protocol.bin_count))
        actual_indices = tuple(bin_summary.bin_index for bin_summary in self.bins)
        if actual_indices != expected_indices:
            raise ValueError("frozen calibrator bins must cover each protocol bin exactly once")
        return self
