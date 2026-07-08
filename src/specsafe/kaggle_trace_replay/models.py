"""Contracts for replay diagnostics over retained Kaggle trace archives."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import StrictContract


class ReplayUtilityDiagnostic(StrictContract):
    """Utility proxy for one threshold under one mismatch-penalty setting."""

    mismatch_penalty: float = Field(ge=0.0)
    saved_target_verification_count: int = Field(ge=0)
    unverified_mismatch_count: int = Field(ge=0)
    diagnostic_utility_units: float

    @model_validator(mode="after")
    def validate_utility_formula(self) -> ReplayUtilityDiagnostic:
        expected = (
            self.saved_target_verification_count
            - self.mismatch_penalty * self.unverified_mismatch_count
        )
        if abs(self.diagnostic_utility_units - expected) > 1e-12:
            raise ValueError(
                "diagnostic utility must equal saved checks minus penalty-weighted mismatches"
            )
        return self


class ThresholdReplayDiagnostic(StrictContract):
    """Replay result for one raw-draft-probability threshold."""

    raw_draft_probability_threshold: float = Field(ge=0.0, le=1.0)
    selected_record_count: int = Field(ge=0)
    selected_fraction: float = Field(ge=0.0, le=1.0)
    selected_match_count: int = Field(ge=0)
    selected_nonmatch_count: int = Field(ge=0)
    selected_match_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    selected_mismatch_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    rejected_record_count: int = Field(ge=0)
    rejected_match_count: int = Field(ge=0)
    rejected_nonmatch_count: int = Field(ge=0)
    match_recall: float = Field(ge=0.0, le=1.0)
    mismatch_capture_rate: float = Field(ge=0.0, le=1.0)
    utility_diagnostics: tuple[ReplayUtilityDiagnostic, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_threshold_counts(self) -> ThresholdReplayDiagnostic:
        if self.selected_match_count + self.selected_nonmatch_count != self.selected_record_count:
            raise ValueError("selected match and nonmatch counts must add up")
        if self.rejected_match_count + self.rejected_nonmatch_count != self.rejected_record_count:
            raise ValueError("rejected match and nonmatch counts must add up")
        if self.selected_record_count > 0:
            expected_match_rate = self.selected_match_count / self.selected_record_count
            expected_mismatch_rate = self.selected_nonmatch_count / self.selected_record_count
            if self.selected_match_rate is None or self.selected_mismatch_rate is None:
                raise ValueError("non-empty selections require selected rates")
            if abs(self.selected_match_rate - expected_match_rate) > 1e-12:
                raise ValueError("selected_match_rate must match selected counts")
            if abs(self.selected_mismatch_rate - expected_mismatch_rate) > 1e-12:
                raise ValueError("selected_mismatch_rate must match selected counts")
        else:
            if self.selected_match_rate is not None or self.selected_mismatch_rate is not None:
                raise ValueError("empty selections must not retain selected rates")
        return self


class ReplayInterpretationBoundary(StrictContract):
    """Explicit non-claim boundary for the replay report."""

    replay_scope: Literal["retained_archive_threshold_diagnostic_replay"]
    target_label: Literal["target_argmax_matches_candidate"]
    runtime_signal: Literal["raw_draft_probability"]
    threshold_policy_selected: bool
    calibration_fit_performed: bool
    policy_utility_promotion_authorized: bool
    throughput_or_latency_measurement_performed: bool
    public_dataset_release_authorized: bool
    production_readiness_claimed: bool

    @model_validator(mode="after")
    def validate_non_claims(self) -> ReplayInterpretationBoundary:
        forbidden_claims = (
            self.threshold_policy_selected,
            self.calibration_fit_performed,
            self.policy_utility_promotion_authorized,
            self.throughput_or_latency_measurement_performed,
            self.public_dataset_release_authorized,
            self.production_readiness_claimed,
        )
        if any(forbidden_claims):
            raise ValueError("replay gate may not promote downstream claims")
        return self


class KaggleTraceReplayReport(StrictContract):
    """Deterministic threshold-replay report over a retained trace archive."""

    schema_version: Literal["specsafe-kaggle-trace-replay-report-v1"]
    replay_id: Literal["v5-kaggle-trace-threshold-replay-v1"]
    collection_id: str = Field(min_length=1, max_length=128)
    collection_attempt_id: str = Field(min_length=1, max_length=128)
    source_commit_sha: str = Field(min_length=7, max_length=128)
    preflight_attempt_id: str = Field(min_length=1, max_length=128)
    archive_sha256: str = Field(min_length=64, max_length=64)
    trace_analysis_report_sha256: str = Field(min_length=64, max_length=64)
    runtime_record_count: int = Field(ge=1)
    expected_outcome_record_count: int = Field(ge=1)
    target_argmax_match_count: int = Field(ge=0)
    target_argmax_nonmatch_count: int = Field(ge=0)
    target_argmax_match_rate: float = Field(ge=0.0, le=1.0)
    threshold_replay: tuple[ThresholdReplayDiagnostic, ...] = Field(min_length=1)
    high_confidence_zero_mismatch_thresholds: tuple[float, ...]
    replay_gate_status: Literal[
        "passes_diagnostic_trace_replay_gate",
        "fails_diagnostic_trace_replay_gate",
    ]
    next_authorized_step: Literal["calibration_replay_harness_authorized_no_threshold_selected"]
    interpretation_boundary: ReplayInterpretationBoundary

    @model_validator(mode="after")
    def validate_report_counts(self) -> KaggleTraceReplayReport:
        if self.runtime_record_count != self.expected_outcome_record_count:
            raise ValueError("runtime and outcome record counts must match")
        total = self.target_argmax_match_count + self.target_argmax_nonmatch_count
        if total != self.runtime_record_count:
            raise ValueError("match and nonmatch counts must add up to runtime count")
        expected_rate = self.target_argmax_match_count / self.runtime_record_count
        if abs(self.target_argmax_match_rate - expected_rate) > 1e-12:
            raise ValueError("target match rate must match retained counts")
        replay_record_counts = {
            item.selected_record_count + item.rejected_record_count
            for item in self.threshold_replay
        }
        if replay_record_counts != {self.runtime_record_count}:
            raise ValueError("every threshold replay must cover all retained records")
        return self
