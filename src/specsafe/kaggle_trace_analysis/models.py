"""Contracts for local analysis of retained Kaggle trace archives."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import StrictContract


class CandidateNumericStats(StrictContract):
    """Aggregate numeric diagnostics for one candidate subset."""

    record_count: int = Field(ge=0)
    mean_raw_draft_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    median_raw_draft_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    min_raw_draft_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    max_raw_draft_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    mean_raw_draft_entropy: float | None = Field(default=None, ge=0.0)
    mean_target_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    mean_target_entropy: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_empty_stats(self) -> CandidateNumericStats:
        populated = [
            self.mean_raw_draft_probability,
            self.median_raw_draft_probability,
            self.min_raw_draft_probability,
            self.max_raw_draft_probability,
            self.mean_raw_draft_entropy,
            self.mean_target_probability,
            self.mean_target_entropy,
        ]
        if self.record_count == 0 and any(value is not None for value in populated):
            raise ValueError("empty candidate stats cannot contain numeric aggregates")
        if self.record_count > 0 and any(value is None for value in populated):
            raise ValueError("non-empty candidate stats require all numeric aggregates")
        return self


class TraceStratumSummary(StrictContract):
    """Match-rate diagnostics for one workload, case, or block-position stratum."""

    record_count: int = Field(ge=1)
    target_argmax_match_count: int = Field(ge=0)
    target_argmax_match_rate: float = Field(ge=0.0, le=1.0)
    mean_raw_draft_probability: float = Field(ge=0.0, le=1.0)
    mean_raw_draft_entropy: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_match_count(self) -> TraceStratumSummary:
        if self.target_argmax_match_count > self.record_count:
            raise ValueError("stratum match count cannot exceed record count")
        expected_rate = self.target_argmax_match_count / self.record_count
        if abs(self.target_argmax_match_rate - expected_rate) > 1e-12:
            raise ValueError("stratum match rate must equal match_count / record_count")
        return self


class ThresholdDiagnostic(StrictContract):
    """Diagnostic threshold sweep over raw draft probability."""

    raw_draft_probability_threshold: float = Field(ge=0.0, le=1.0)
    selected_record_count: int = Field(ge=0)
    selected_match_count: int = Field(ge=0)
    selected_nonmatch_count: int = Field(ge=0)
    selected_match_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    retained_candidate_fraction: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_selected_counts(self) -> ThresholdDiagnostic:
        total_selected = self.selected_match_count + self.selected_nonmatch_count
        if total_selected != self.selected_record_count:
            raise ValueError("selected threshold counts do not add up")
        if self.selected_record_count == 0 and self.selected_match_rate is not None:
            raise ValueError("empty threshold selections cannot have a match rate")
        if self.selected_record_count > 0:
            expected_rate = self.selected_match_count / self.selected_record_count
            if self.selected_match_rate is None:
                raise ValueError("non-empty threshold selections require a match rate")
            if abs(self.selected_match_rate - expected_rate) > 1e-12:
                raise ValueError(
                    "selected match rate must equal selected_match_count / selected_record_count"
                )
        return self


class TraceSignalDiagnostics(StrictContract):
    """Local diagnostic signal checks without fitting calibration."""

    raw_draft_probability_pairwise_separation_rate: float = Field(ge=0.0, le=1.0)
    raw_draft_entropy_pairwise_lower_for_match_rate: float = Field(ge=0.0, le=1.0)
    raw_draft_probability_brier_diagnostic: float = Field(ge=0.0)
    support_interpretation: Literal["directionally_supportive_small_sample_not_calibration_claim"]


class TraceAnalysisBoundary(StrictContract):
    """Explicit boundary for what this local analysis did and did not do."""

    analysis_scope: Literal["local_retained_archive_diagnostics"]
    calibration_fit_performed: Literal[False]
    policy_threshold_selected: Literal[False]
    policy_utility_evaluation_performed: Literal[False]
    throughput_or_latency_measurement_performed: Literal[False]
    public_dataset_release_authorized: Literal[False]
    production_readiness_claimed: Literal[False]


class KaggleTraceAnalysisReport(StrictContract):
    """Reproducible local analysis report for one retained Kaggle trace archive."""

    schema_version: Literal["specsafe-kaggle-trace-analysis-report-v1"]
    collection_id: str = Field(min_length=1, max_length=128)
    collection_attempt_id: str = Field(min_length=1, max_length=128)
    source_commit_sha: str = Field(min_length=7, max_length=128)
    preflight_attempt_id: str = Field(min_length=1, max_length=128)
    archive_sha256: str = Field(min_length=64, max_length=64)
    manifest_sha256: str = Field(min_length=64, max_length=64)
    runtime_records_sha256: str = Field(min_length=64, max_length=64)
    expected_outcomes_sha256: str = Field(min_length=64, max_length=64)
    case_count: int = Field(ge=1)
    runtime_record_count: int = Field(ge=1)
    expected_outcome_record_count: int = Field(ge=1)
    target_argmax_match_count: int = Field(ge=0)
    target_argmax_nonmatch_count: int = Field(ge=0)
    target_argmax_match_rate: float = Field(ge=0.0, le=1.0)
    matched_candidate_stats: CandidateNumericStats
    nonmatched_candidate_stats: CandidateNumericStats
    signal_diagnostics: TraceSignalDiagnostics
    by_workload_type: dict[str, TraceStratumSummary] = Field(min_length=1)
    by_case_id: dict[str, TraceStratumSummary] = Field(min_length=1)
    by_block_position_index: dict[str, TraceStratumSummary] = Field(min_length=1)
    raw_draft_probability_threshold_sensitivity: tuple[ThresholdDiagnostic, ...] = Field(
        min_length=1
    )
    interpretation_boundary: TraceAnalysisBoundary

    @model_validator(mode="after")
    def validate_report_counts(self) -> KaggleTraceAnalysisReport:
        if self.runtime_record_count != self.expected_outcome_record_count:
            raise ValueError("runtime and outcome record counts must match")
        total_outcomes = self.target_argmax_match_count + self.target_argmax_nonmatch_count
        if total_outcomes != self.runtime_record_count:
            raise ValueError("match and nonmatch counts do not add up")
        expected_rate = self.target_argmax_match_count / self.runtime_record_count
        if abs(self.target_argmax_match_rate - expected_rate) > 1e-12:
            raise ValueError("overall match rate must equal match_count / runtime_record_count")
        if self.matched_candidate_stats.record_count != self.target_argmax_match_count:
            raise ValueError("matched stats record count must equal match count")
        nonmatched_stats_count = self.nonmatched_candidate_stats.record_count
        if nonmatched_stats_count != self.target_argmax_nonmatch_count:
            raise ValueError("nonmatched stats record count must equal nonmatch count")
        return self
