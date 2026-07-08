"""Threshold replay over retained Kaggle trace archives."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

from specsafe.kaggle_trace_analysis.analysis import TracePair, load_trace_archive
from specsafe.kaggle_trace_analysis.models import KaggleTraceAnalysisReport
from specsafe.kaggle_trace_replay.models import (
    KaggleTraceReplayReport,
    ReplayInterpretationBoundary,
    ReplayUtilityDiagnostic,
    ThresholdReplayDiagnostic,
)

DEFAULT_REPLAY_THRESHOLDS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
DEFAULT_MISMATCH_PENALTIES = (1.0, 2.0, 4.0, 8.0)
TRACE_ANALYSIS_REPORT_SHA256 = "90915a600bc481fa451ef07366cb2a8b8dba7b89e1cb16375f64896c03f9552d"


def sha256_file(path: Path) -> str:
    """Return SHA-256 for a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _threshold_replay_diagnostic(
    pairs: Sequence[TracePair],
    threshold: float,
    mismatch_penalties: Sequence[float],
) -> ThresholdReplayDiagnostic:
    selected = [pair for pair in pairs if pair[0].raw_draft_probability >= threshold]
    rejected = [pair for pair in pairs if pair[0].raw_draft_probability < threshold]

    selected_match_count = sum(
        1 for _, outcome in selected if outcome.target_argmax_matches_candidate
    )
    selected_nonmatch_count = len(selected) - selected_match_count
    rejected_match_count = sum(
        1 for _, outcome in rejected if outcome.target_argmax_matches_candidate
    )
    rejected_nonmatch_count = len(rejected) - rejected_match_count

    total_match_count = selected_match_count + rejected_match_count
    total_nonmatch_count = selected_nonmatch_count + rejected_nonmatch_count
    selected_match_rate = selected_match_count / len(selected) if selected else None
    selected_mismatch_rate = selected_nonmatch_count / len(selected) if selected else None

    utility_diagnostics = tuple(
        ReplayUtilityDiagnostic(
            mismatch_penalty=penalty,
            saved_target_verification_count=len(selected),
            unverified_mismatch_count=selected_nonmatch_count,
            diagnostic_utility_units=len(selected) - penalty * selected_nonmatch_count,
        )
        for penalty in mismatch_penalties
    )

    return ThresholdReplayDiagnostic(
        raw_draft_probability_threshold=threshold,
        selected_record_count=len(selected),
        selected_fraction=len(selected) / len(pairs),
        selected_match_count=selected_match_count,
        selected_nonmatch_count=selected_nonmatch_count,
        selected_match_rate=selected_match_rate,
        selected_mismatch_rate=selected_mismatch_rate,
        rejected_record_count=len(rejected),
        rejected_match_count=rejected_match_count,
        rejected_nonmatch_count=rejected_nonmatch_count,
        match_recall=(selected_match_count / total_match_count if total_match_count else 0.0),
        mismatch_capture_rate=(
            selected_nonmatch_count / total_nonmatch_count if total_nonmatch_count else 0.0
        ),
        utility_diagnostics=utility_diagnostics,
    )


def build_trace_replay_report(
    archive_path: Path,
    trace_analysis_report_path: Path,
    thresholds: Sequence[float] = DEFAULT_REPLAY_THRESHOLDS,
    mismatch_penalties: Sequence[float] = DEFAULT_MISMATCH_PENALTIES,
) -> KaggleTraceReplayReport:
    """Build a deterministic diagnostic replay report from retained trace evidence."""

    archive_sha256, _, manifest, _, runtime_records, expected_outcomes = load_trace_archive(
        archive_path
    )
    analysis_report_sha256 = sha256_file(trace_analysis_report_path)
    analysis_report = KaggleTraceAnalysisReport.model_validate_json(
        trace_analysis_report_path.read_text(encoding="utf-8")
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

    threshold_replay = tuple(
        _threshold_replay_diagnostic(pairs, threshold, mismatch_penalties)
        for threshold in thresholds
    )
    zero_mismatch_thresholds = tuple(
        item.raw_draft_probability_threshold
        for item in threshold_replay
        if item.selected_record_count > 0 and item.selected_nonmatch_count == 0
    )

    return KaggleTraceReplayReport(
        schema_version="specsafe-kaggle-trace-replay-report-v1",
        replay_id="v5-kaggle-trace-threshold-replay-v1",
        collection_id=manifest.collection_id,
        collection_attempt_id=manifest.collection_attempt_id,
        source_commit_sha=manifest.source_commit_sha,
        preflight_attempt_id=manifest.preflight_attempt_id,
        archive_sha256=archive_sha256,
        trace_analysis_report_sha256=analysis_report_sha256,
        runtime_record_count=len(runtime_records),
        expected_outcome_record_count=len(expected_outcomes),
        target_argmax_match_count=analysis_report.target_argmax_match_count,
        target_argmax_nonmatch_count=analysis_report.target_argmax_nonmatch_count,
        target_argmax_match_rate=analysis_report.target_argmax_match_rate,
        threshold_replay=threshold_replay,
        high_confidence_zero_mismatch_thresholds=zero_mismatch_thresholds,
        replay_gate_status="passes_diagnostic_trace_replay_gate",
        next_authorized_step="calibration_replay_harness_authorized_no_threshold_selected",
        interpretation_boundary=ReplayInterpretationBoundary(
            replay_scope="retained_archive_threshold_diagnostic_replay",
            target_label="target_argmax_matches_candidate",
            runtime_signal="raw_draft_probability",
            threshold_policy_selected=False,
            calibration_fit_performed=False,
            policy_utility_promotion_authorized=False,
            throughput_or_latency_measurement_performed=False,
            public_dataset_release_authorized=False,
            production_readiness_claimed=False,
        ),
    )


def write_trace_replay_report(report: KaggleTraceReplayReport, output_path: Path) -> None:
    """Write a replay report with deterministic LF line endings."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
