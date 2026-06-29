"""Typed contracts for raw-confidence diagnostics on calibration-only fixtures."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts import TraceSplit
from specsafe.contracts.models import StrictContract


class RawConfidenceFitnessStatus(StrEnum):
    """Diagnostic status for raw confidence before calibration is attempted."""

    PASSES_PRECALIBRATION_SCREEN = "passes_precalibration_screen"
    INSUFFICIENT_CALIBRATION_DATA = "insufficient_calibration_data"
    FAILS_PRECALIBRATION_SCREEN = "fails_precalibration_screen"


class AutomationControlEligibility(StrEnum):
    """Hard boundary preventing this diagnostic from authorizing a runtime policy."""

    NOT_ELIGIBLE_PENDING_HELD_OUT_CALIBRATION = (
        "not_eligible_pending_held_out_calibration"
    )


class ConfidenceFitnessErrorCode(StrEnum):
    """Machine-readable failures for calibration-split confidence diagnostics."""

    INVALID_FIXTURE_SET = "invalid_fixture_set"
    NO_CALIBRATION_CASES = "no_calibration_cases"


class ConfidenceFitnessProtocolConfig(StrictContract):
    """Predeclared raw-confidence fitness thresholds for a diagnostic study only."""

    protocol_id: str = Field(
        default="raw-confidence-fitness-v1",
        min_length=1,
        max_length=128,
    )
    calibration_split: Literal[TraceSplit.CALIBRATION] = TraceSplit.CALIBRATION
    minimum_observation_count: int = Field(default=8, ge=1)
    bin_count: int = Field(default=4, ge=2, le=20)
    maximum_brier_score: float = Field(default=0.25, ge=0.0, le=1.0)
    maximum_expected_calibration_error: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
    )


class ConfidenceCalibrationBin(StrictContract):
    """One deterministic confidence bin computed after calibration outcomes are read."""

    bin_index: int = Field(ge=0)
    lower_confidence_bound: float = Field(ge=0.0, le=1.0)
    upper_confidence_bound: float = Field(gt=0.0, le=1.0)
    observation_count: int = Field(ge=0)
    mean_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_empty_and_populated_bin_fields(self) -> ConfidenceCalibrationBin:
        """Require evidence statistics only when the bin has observations."""

        evidence_fields = (
            self.mean_confidence,
            self.observed_acceptance_rate,
            self.absolute_calibration_gap,
        )
        if self.lower_confidence_bound >= self.upper_confidence_bound:
            raise ValueError("confidence bin lower bound must be below the upper bound")
        if self.observation_count == 0 and any(value is not None for value in evidence_fields):
            raise ValueError("empty confidence bins must not invent evidence statistics")
        if self.observation_count > 0 and any(value is None for value in evidence_fields):
            raise ValueError("populated confidence bins require complete evidence statistics")
        return self


class ConfidenceFitnessResult(StrictContract):
    """Immutable, calibration-only diagnostic result that cannot authorize scheduling."""

    schema_version: Literal["raw-confidence-fitness-v1"] = "raw-confidence-fitness-v1"
    protocol: ConfidenceFitnessProtocolConfig
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source_split: Literal[TraceSplit.CALIBRATION] = TraceSplit.CALIBRATION
    calibration_case_ids: tuple[str, ...] = Field(min_length=1)
    calibration_trace_ids: tuple[str, ...] = Field(min_length=1)
    observation_count: int = Field(ge=1)
    mean_confidence: float = Field(ge=0.0, le=1.0)
    observed_acceptance_rate: float = Field(ge=0.0, le=1.0)
    brier_score: float = Field(ge=0.0, le=1.0)
    expected_calibration_error: float = Field(ge=0.0, le=1.0)
    bins: tuple[ConfidenceCalibrationBin, ...] = Field(min_length=2)
    status: RawConfidenceFitnessStatus
    automation_control_eligibility: Literal[
        AutomationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_CALIBRATION
    ] = AutomationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_CALIBRATION

    @model_validator(mode="after")
    def validate_calibration_diagnostic_evidence(self) -> ConfidenceFitnessResult:
        """Prevent incomplete bin evidence and accidental runtime-eligibility claims."""

        if len(set(self.calibration_case_ids)) != len(self.calibration_case_ids):
            raise ValueError("calibration_case_ids must not contain duplicates")
        if len(set(self.calibration_trace_ids)) != len(self.calibration_trace_ids):
            raise ValueError("calibration_trace_ids must not contain duplicates")
        if len(self.bins) != self.protocol.bin_count:
            raise ValueError("confidence fitness bins must match protocol bin_count")
        bin_observation_count = sum(
            bin_summary.observation_count for bin_summary in self.bins
        )
        if bin_observation_count != self.observation_count:
            raise ValueError("confidence bin observations must equal observation_count")
        if tuple(bin_summary.bin_index for bin_summary in self.bins) != tuple(
            range(self.protocol.bin_count)
        ):
            raise ValueError("confidence bins must cover each protocol bin index exactly once")
        return self
