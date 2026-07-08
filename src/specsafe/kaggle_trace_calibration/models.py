"""Contracts for diagnostic calibration review over retained Kaggle traces."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import StrictContract


class ProbabilityBinDiagnostic(StrictContract):
    """Observed agreement diagnostic for one fixed raw-probability bin."""

    bin_id: str = Field(min_length=1, max_length=64)
    lower_inclusive: float = Field(ge=0.0, le=1.0)
    upper_exclusive: float = Field(gt=0.0, le=1.000000000001)
    record_count: int = Field(ge=0)
    match_count: int = Field(ge=0)
    observed_match_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mean_raw_draft_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_calibration_gap: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_bin_diagnostic(self) -> ProbabilityBinDiagnostic:
        if self.lower_inclusive >= self.upper_exclusive:
            raise ValueError("bin lower bound must be below upper bound")
        if self.match_count > self.record_count:
            raise ValueError("bin match count cannot exceed record count")
        populated = (
            self.observed_match_rate,
            self.mean_raw_draft_probability,
            self.absolute_calibration_gap,
        )
        if self.record_count == 0:
            if self.match_count != 0:
                raise ValueError("empty bins cannot contain matches")
            if any(value is not None for value in populated):
                raise ValueError("empty bins cannot contain numeric rates")
            return self
        if any(value is None for value in populated):
            raise ValueError("non-empty bins require observed rate, mean probability, and gap")
        expected_observed = self.match_count / self.record_count
        if abs(self.observed_match_rate - expected_observed) > 1e-12:
            raise ValueError("observed match rate must equal match_count / record_count")
        expected_gap = abs(self.observed_match_rate - self.mean_raw_draft_probability)
        if abs(self.absolute_calibration_gap - expected_gap) > 1e-12:
            raise ValueError("absolute calibration gap must match observed-minus-mean gap")
        return self


class CalibrationReadinessGate(StrictContract):
    """Gate deciding whether retained traces are enough for calibration fitting."""

    minimum_record_count_for_calibration_fit: int = Field(ge=1)
    minimum_positive_count_for_calibration_fit: int = Field(ge=1)
    minimum_negative_count_for_calibration_fit: int = Field(ge=1)
    observed_record_count: int = Field(ge=1)
    observed_positive_count: int = Field(ge=0)
    observed_negative_count: int = Field(ge=0)
    signal_diagnostic_passed: bool
    calibration_fit_readiness_status: Literal[
        "insufficient_sample_for_calibration_fit_signal_supportive",
        "insufficient_signal_for_calibration_fit",
        "passes_calibration_fit_readiness",
    ]
    next_authorized_step: Literal[
        "expand_trace_corpus_before_calibration_fit",
        "calibration_fit_harness_authorized",
    ]

    @model_validator(mode="after")
    def validate_readiness_status(self) -> CalibrationReadinessGate:
        if (
            self.observed_positive_count + self.observed_negative_count
            != self.observed_record_count
        ):
            raise ValueError("positive and negative counts must equal observed record count")
        enough_records = self.observed_record_count >= self.minimum_record_count_for_calibration_fit
        enough_positive = (
            self.observed_positive_count >= self.minimum_positive_count_for_calibration_fit
        )
        enough_negative = (
            self.observed_negative_count >= self.minimum_negative_count_for_calibration_fit
        )
        sample_ready = enough_records and enough_positive and enough_negative
        if self.calibration_fit_readiness_status == "passes_calibration_fit_readiness":
            if not sample_ready or not self.signal_diagnostic_passed:
                raise ValueError("calibration fit readiness cannot pass without sample and signal")
            if self.next_authorized_step != "calibration_fit_harness_authorized":
                raise ValueError("passing readiness must authorize calibration fit harness")
        else:
            if self.next_authorized_step != "expand_trace_corpus_before_calibration_fit":
                raise ValueError("failed readiness must authorize corpus expansion only")
        return self


class CalibrationInterpretationBoundary(StrictContract):
    """Explicit non-claim boundary for calibration diagnostics."""

    calibration_scope: Literal["retained_archive_calibration_diagnostic"]
    runtime_signal: Literal["raw_draft_probability"]
    target_label: Literal["target_argmax_matches_candidate"]
    calibration_fit_performed: bool
    calibration_model_retained: bool
    threshold_policy_selected: bool
    policy_utility_promotion_authorized: bool
    throughput_or_latency_measurement_performed: bool
    public_dataset_release_authorized: bool
    production_readiness_claimed: bool

    @model_validator(mode="after")
    def validate_no_promoted_claims(self) -> CalibrationInterpretationBoundary:
        forbidden_claims = (
            self.calibration_fit_performed,
            self.calibration_model_retained,
            self.threshold_policy_selected,
            self.policy_utility_promotion_authorized,
            self.throughput_or_latency_measurement_performed,
            self.public_dataset_release_authorized,
            self.production_readiness_claimed,
        )
        if any(forbidden_claims):
            raise ValueError("calibration diagnostic may not promote downstream claims")
        return self


class KaggleTraceCalibrationDiagnosticReport(StrictContract):
    """Diagnostic calibration review for the first retained Kaggle trace archive."""

    schema_version: Literal["specsafe-kaggle-trace-calibration-diagnostic-report-v1"]
    diagnostic_id: Literal["v5-kaggle-trace-calibration-diagnostic-v1"]
    collection_id: str = Field(min_length=1, max_length=128)
    collection_attempt_id: str = Field(min_length=1, max_length=128)
    source_commit_sha: str = Field(min_length=7, max_length=128)
    preflight_attempt_id: str = Field(min_length=1, max_length=128)
    archive_sha256: str = Field(min_length=64, max_length=64)
    trace_analysis_report_sha256: str = Field(min_length=64, max_length=64)
    trace_replay_report_sha256: str = Field(min_length=64, max_length=64)
    runtime_record_count: int = Field(ge=1)
    expected_outcome_record_count: int = Field(ge=1)
    target_argmax_match_count: int = Field(ge=0)
    target_argmax_nonmatch_count: int = Field(ge=0)
    raw_draft_probability_brier_diagnostic: float = Field(ge=0.0)
    fixed_bin_expected_calibration_error: float = Field(ge=0.0)
    fixed_bin_maximum_calibration_error: float = Field(ge=0.0)
    fixed_probability_bins: tuple[ProbabilityBinDiagnostic, ...] = Field(min_length=1)
    readiness_gate: CalibrationReadinessGate
    interpretation_boundary: CalibrationInterpretationBoundary

    @model_validator(mode="after")
    def validate_report_counts_and_errors(self) -> KaggleTraceCalibrationDiagnosticReport:
        if self.runtime_record_count != self.expected_outcome_record_count:
            raise ValueError("runtime and outcome record counts must match")
        total_outcomes = self.target_argmax_match_count + self.target_argmax_nonmatch_count
        if total_outcomes != self.runtime_record_count:
            raise ValueError("match and nonmatch counts must add up to runtime count")
        bin_record_count = sum(item.record_count for item in self.fixed_probability_bins)
        if bin_record_count != self.runtime_record_count:
            raise ValueError("fixed bins must cover all runtime records")
        bin_match_count = sum(item.match_count for item in self.fixed_probability_bins)
        if bin_match_count != self.target_argmax_match_count:
            raise ValueError("fixed bins must preserve match count")
        nonempty_gaps = [
            item.absolute_calibration_gap
            for item in self.fixed_probability_bins
            if item.record_count > 0
        ]
        expected_ece = sum(
            (item.record_count / self.runtime_record_count) * item.absolute_calibration_gap
            for item in self.fixed_probability_bins
            if item.record_count > 0
        )
        expected_mce = max(nonempty_gaps)
        if abs(self.fixed_bin_expected_calibration_error - expected_ece) > 1e-12:
            raise ValueError("ECE must equal weighted fixed-bin calibration gaps")
        if abs(self.fixed_bin_maximum_calibration_error - expected_mce) > 1e-12:
            raise ValueError("MCE must equal maximum fixed-bin calibration gap")
        return self
