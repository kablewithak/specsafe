"""Diagnostic calibration checks over retained Kaggle trace archives."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

from specsafe.kaggle_trace_analysis.analysis import TracePair, load_trace_archive
from specsafe.kaggle_trace_analysis.models import KaggleTraceAnalysisReport
from specsafe.kaggle_trace_calibration.models import (
    CalibrationInterpretationBoundary,
    CalibrationReadinessGate,
    KaggleTraceCalibrationDiagnosticReport,
    ProbabilityBinDiagnostic,
)
from specsafe.kaggle_trace_replay.models import KaggleTraceReplayReport

DEFAULT_CALIBRATION_BIN_EDGES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.000000000001)
MINIMUM_RECORD_COUNT_FOR_CALIBRATION_FIT = 100
MINIMUM_POSITIVE_COUNT_FOR_CALIBRATION_FIT = 30
MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT = 30
MINIMUM_SIGNAL_SEPARATION_RATE = 0.8


def sha256_file(path: Path) -> str:
    """Return SHA-256 for a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot compute a mean for an empty sequence")
    return sum(values) / len(values)


def _trace_pairs(archive_path: Path) -> tuple[str, object, list[TracePair]]:
    archive_sha256, _, manifest, _, runtime_records, expected_outcomes = load_trace_archive(
        archive_path
    )
    outcome_by_key = {
        (outcome.trace_id, outcome.decode_round, outcome.block_position_index): outcome
        for outcome in expected_outcomes
    }
    pairs = [
        (
            runtime,
            outcome_by_key[(runtime.trace_id, runtime.decode_round, runtime.block_position_index)],
        )
        for runtime in runtime_records
    ]
    return archive_sha256, manifest, pairs


def _brier_diagnostic(pairs: Sequence[TracePair]) -> float:
    squared_errors = []
    for runtime, outcome in pairs:
        label = 1.0 if outcome.target_argmax_matches_candidate else 0.0
        squared_errors.append((runtime.raw_draft_probability - label) ** 2)
    return _mean(squared_errors)


def _fixed_bin_diagnostics(
    pairs: Sequence[TracePair],
    bin_edges: Sequence[float],
) -> tuple[ProbabilityBinDiagnostic, ...]:
    diagnostics: list[ProbabilityBinDiagnostic] = []
    for index, lower_bound in enumerate(bin_edges[:-1]):
        upper_bound = bin_edges[index + 1]
        bin_pairs = [
            pair
            for pair in pairs
            if pair[0].raw_draft_probability >= lower_bound
            and pair[0].raw_draft_probability < upper_bound
        ]
        match_count = sum(1 for _, outcome in bin_pairs if outcome.target_argmax_matches_candidate)
        if bin_pairs:
            observed_match_rate = match_count / len(bin_pairs)
            mean_probability = _mean([runtime.raw_draft_probability for runtime, _ in bin_pairs])
            calibration_gap = abs(observed_match_rate - mean_probability)
        else:
            observed_match_rate = None
            mean_probability = None
            calibration_gap = None
        upper_label = "1.0" if upper_bound > 1.0 else f"{upper_bound:.1f}"
        diagnostics.append(
            ProbabilityBinDiagnostic(
                bin_id=f"raw_prob_{lower_bound:.1f}_{upper_label}",
                lower_inclusive=lower_bound,
                upper_exclusive=upper_bound,
                record_count=len(bin_pairs),
                match_count=match_count,
                observed_match_rate=observed_match_rate,
                mean_raw_draft_probability=mean_probability,
                absolute_calibration_gap=calibration_gap,
            )
        )
    return tuple(diagnostics)


def build_trace_calibration_diagnostic_report(
    archive_path: Path,
    trace_analysis_report_path: Path,
    trace_replay_report_path: Path,
    bin_edges: Sequence[float] = DEFAULT_CALIBRATION_BIN_EDGES,
) -> KaggleTraceCalibrationDiagnosticReport:
    """Build a deterministic diagnostic calibration report from retained traces."""

    archive_sha256, manifest, pairs = _trace_pairs(archive_path)
    trace_analysis_report_sha256 = sha256_file(trace_analysis_report_path)
    trace_replay_report_sha256 = sha256_file(trace_replay_report_path)
    analysis_report = KaggleTraceAnalysisReport.model_validate_json(
        trace_analysis_report_path.read_text(encoding="utf-8")
    )
    KaggleTraceReplayReport.model_validate_json(
        trace_replay_report_path.read_text(encoding="utf-8")
    )

    bin_diagnostics = _fixed_bin_diagnostics(pairs, bin_edges)
    expected_calibration_error = sum(
        (item.record_count / len(pairs)) * item.absolute_calibration_gap
        for item in bin_diagnostics
        if item.record_count > 0
    )
    maximum_calibration_error = max(
        item.absolute_calibration_gap for item in bin_diagnostics if item.record_count > 0
    )
    match_count = sum(1 for _, outcome in pairs if outcome.target_argmax_matches_candidate)
    nonmatch_count = len(pairs) - match_count
    signal_passed = (
        analysis_report.signal_diagnostics.raw_draft_probability_pairwise_separation_rate
        >= MINIMUM_SIGNAL_SEPARATION_RATE
    )

    return KaggleTraceCalibrationDiagnosticReport(
        schema_version="specsafe-kaggle-trace-calibration-diagnostic-report-v1",
        diagnostic_id="v5-kaggle-trace-calibration-diagnostic-v1",
        collection_id=manifest.collection_id,
        collection_attempt_id=manifest.collection_attempt_id,
        source_commit_sha=manifest.source_commit_sha,
        preflight_attempt_id=manifest.preflight_attempt_id,
        archive_sha256=archive_sha256,
        trace_analysis_report_sha256=trace_analysis_report_sha256,
        trace_replay_report_sha256=trace_replay_report_sha256,
        runtime_record_count=len(pairs),
        expected_outcome_record_count=len(pairs),
        target_argmax_match_count=match_count,
        target_argmax_nonmatch_count=nonmatch_count,
        raw_draft_probability_brier_diagnostic=_brier_diagnostic(pairs),
        fixed_bin_expected_calibration_error=expected_calibration_error,
        fixed_bin_maximum_calibration_error=maximum_calibration_error,
        fixed_probability_bins=bin_diagnostics,
        readiness_gate=CalibrationReadinessGate(
            minimum_record_count_for_calibration_fit=MINIMUM_RECORD_COUNT_FOR_CALIBRATION_FIT,
            minimum_positive_count_for_calibration_fit=MINIMUM_POSITIVE_COUNT_FOR_CALIBRATION_FIT,
            minimum_negative_count_for_calibration_fit=MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT,
            observed_record_count=len(pairs),
            observed_positive_count=match_count,
            observed_negative_count=nonmatch_count,
            signal_diagnostic_passed=signal_passed,
            calibration_fit_readiness_status=(
                "insufficient_sample_for_calibration_fit_signal_supportive"
                if signal_passed
                else "insufficient_signal_for_calibration_fit"
            ),
            next_authorized_step="expand_trace_corpus_before_calibration_fit",
        ),
        interpretation_boundary=CalibrationInterpretationBoundary(
            calibration_scope="retained_archive_calibration_diagnostic",
            runtime_signal="raw_draft_probability",
            target_label="target_argmax_matches_candidate",
            calibration_fit_performed=False,
            calibration_model_retained=False,
            threshold_policy_selected=False,
            policy_utility_promotion_authorized=False,
            throughput_or_latency_measurement_performed=False,
            public_dataset_release_authorized=False,
            production_readiness_claimed=False,
        ),
    )


def write_trace_calibration_diagnostic_report(
    report: KaggleTraceCalibrationDiagnosticReport,
    output_path: Path,
) -> None:
    """Write a calibration diagnostic report in canonical JSON form."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
