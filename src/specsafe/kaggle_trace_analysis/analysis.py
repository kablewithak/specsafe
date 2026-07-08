"""Local diagnostic analysis for retained Kaggle trace-collection archives."""

from __future__ import annotations

import hashlib
import json
import statistics
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from specsafe.kaggle_trace_analysis.models import (
    CandidateNumericStats,
    KaggleTraceAnalysisReport,
    ThresholdDiagnostic,
    TraceAnalysisBoundary,
    TraceSignalDiagnostics,
    TraceStratumSummary,
)
from specsafe.kaggle_trace_collection import (
    KaggleTraceCollectionExpectedOutcomeRecord,
    KaggleTraceCollectionManifest,
    KaggleTraceCollectionRuntimeRecord,
)

EXPECTED_ARCHIVE_MEMBERS = (
    "expected_outcomes.jsonl",
    "manifest.json",
    "runtime_records.jsonl",
)
DEFAULT_THRESHOLDS = (0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9)


TraceKey = tuple[str, int, int]
TracePair = tuple[
    KaggleTraceCollectionRuntimeRecord,
    KaggleTraceCollectionExpectedOutcomeRecord,
]


def sha256_bytes(payload: bytes) -> str:
    """Return SHA-256 for a byte payload."""

    return hashlib.sha256(payload).hexdigest()


def read_jsonl_bytes(payload: bytes) -> list[dict[str, Any]]:
    """Parse a UTF-8 JSONL payload into dictionaries."""

    lines = payload.decode("utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def _trace_key(record: Any) -> TraceKey:
    return (record.trace_id, record.decode_round, record.block_position_index)


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot compute a mean for an empty sequence")
    return sum(values) / len(values)


def _candidate_stats(pairs: Sequence[TracePair]) -> CandidateNumericStats:
    if not pairs:
        return CandidateNumericStats(record_count=0)

    draft_probabilities = [runtime.raw_draft_probability for runtime, _ in pairs]
    draft_entropies = [runtime.raw_draft_entropy for runtime, _ in pairs]
    target_probabilities = [outcome.target_probability for _, outcome in pairs]
    target_entropies = [outcome.target_entropy for _, outcome in pairs]

    return CandidateNumericStats(
        record_count=len(pairs),
        mean_raw_draft_probability=_mean(draft_probabilities),
        median_raw_draft_probability=statistics.median(draft_probabilities),
        min_raw_draft_probability=min(draft_probabilities),
        max_raw_draft_probability=max(draft_probabilities),
        mean_raw_draft_entropy=_mean(draft_entropies),
        mean_target_probability=_mean(target_probabilities),
        mean_target_entropy=_mean(target_entropies),
    )


def _stratum_summary(pairs: Sequence[TracePair]) -> TraceStratumSummary:
    if not pairs:
        raise ValueError("cannot summarize an empty stratum")

    match_count = sum(1 for _, outcome in pairs if outcome.target_argmax_matches_candidate)
    return TraceStratumSummary(
        record_count=len(pairs),
        target_argmax_match_count=match_count,
        target_argmax_match_rate=match_count / len(pairs),
        mean_raw_draft_probability=_mean([runtime.raw_draft_probability for runtime, _ in pairs]),
        mean_raw_draft_entropy=_mean([runtime.raw_draft_entropy for runtime, _ in pairs]),
    )


def _group_by_key(
    pairs: Iterable[TracePair],
    key_name: str,
) -> dict[str, TraceStratumSummary]:
    groups: dict[str, list[TracePair]] = {}
    for pair in pairs:
        runtime, _ = pair
        if key_name == "workload_type":
            key_value = getattr(
                runtime.workload_type,
                "value",
                str(runtime.workload_type),
            )
        elif key_name == "case_id":
            key_value = runtime.case_id
        elif key_name == "block_position_index":
            key_value = str(runtime.block_position_index)
        else:
            raise ValueError(f"unsupported grouping key: {key_name}")
        groups.setdefault(str(key_value), []).append(pair)

    return {key: _stratum_summary(groups[key]) for key in sorted(groups)}


def _threshold_diagnostics(
    pairs: Sequence[TracePair],
    thresholds: Sequence[float],
) -> tuple[ThresholdDiagnostic, ...]:
    total_count = len(pairs)
    diagnostics: list[ThresholdDiagnostic] = []
    for threshold in thresholds:
        selected = [pair for pair in pairs if pair[0].raw_draft_probability >= threshold]
        selected_match_count = sum(
            1 for _, outcome in selected if outcome.target_argmax_matches_candidate
        )
        selected_nonmatch_count = len(selected) - selected_match_count
        selected_match_rate = selected_match_count / len(selected) if selected else None
        diagnostics.append(
            ThresholdDiagnostic(
                raw_draft_probability_threshold=threshold,
                selected_record_count=len(selected),
                selected_match_count=selected_match_count,
                selected_nonmatch_count=selected_nonmatch_count,
                selected_match_rate=selected_match_rate,
                retained_candidate_fraction=len(selected) / total_count,
            )
        )
    return tuple(diagnostics)


def _pairwise_probability_separation(
    matched_pairs: Sequence[TracePair],
    nonmatched_pairs: Sequence[TracePair],
) -> float:
    pair_count = 0
    wins = 0
    ties = 0
    for matched_runtime, _ in matched_pairs:
        for nonmatched_runtime, _ in nonmatched_pairs:
            pair_count += 1
            matched_probability = matched_runtime.raw_draft_probability
            nonmatched_probability = nonmatched_runtime.raw_draft_probability
            if matched_probability > nonmatched_probability:
                wins += 1
            elif matched_probability == nonmatched_probability:
                ties += 1
    if pair_count == 0:
        raise ValueError("pairwise separation requires both matched and nonmatched records")
    return (wins + 0.5 * ties) / pair_count


def _pairwise_entropy_separation(
    matched_pairs: Sequence[TracePair],
    nonmatched_pairs: Sequence[TracePair],
) -> float:
    pair_count = 0
    wins = 0
    ties = 0
    for matched_runtime, _ in matched_pairs:
        for nonmatched_runtime, _ in nonmatched_pairs:
            pair_count += 1
            matched_entropy = matched_runtime.raw_draft_entropy
            nonmatched_entropy = nonmatched_runtime.raw_draft_entropy
            if matched_entropy < nonmatched_entropy:
                wins += 1
            elif matched_entropy == nonmatched_entropy:
                ties += 1
    if pair_count == 0:
        raise ValueError("pairwise separation requires both matched and nonmatched records")
    return (wins + 0.5 * ties) / pair_count


def _raw_draft_probability_brier_diagnostic(pairs: Sequence[TracePair]) -> float:
    squared_errors = []
    for runtime, outcome in pairs:
        label = 1.0 if outcome.target_argmax_matches_candidate else 0.0
        squared_errors.append((runtime.raw_draft_probability - label) ** 2)
    return _mean(squared_errors)


def load_trace_archive(
    archive_path: Path,
) -> tuple[
    str,
    dict[str, bytes],
    KaggleTraceCollectionManifest,
    dict[str, Any],
    list[KaggleTraceCollectionRuntimeRecord],
    list[KaggleTraceCollectionExpectedOutcomeRecord],
]:
    """Load and validate the retained Kaggle trace archive."""

    archive_bytes = archive_path.read_bytes()
    archive_sha256 = sha256_bytes(archive_bytes)

    with zipfile.ZipFile(archive_path) as archive:
        names = tuple(sorted(archive.namelist()))
        if names != EXPECTED_ARCHIVE_MEMBERS:
            raise ValueError(f"unexpected trace archive members: {names}")
        payloads = {name: archive.read(name) for name in names}

    manifest_payload = json.loads(payloads["manifest.json"].decode("utf-8"))
    manifest_contract_payload = {
        key: value
        for key, value in manifest_payload.items()
        if key in KaggleTraceCollectionManifest.model_fields
    }
    manifest = KaggleTraceCollectionManifest.model_validate(manifest_contract_payload)
    runtime_records = [
        KaggleTraceCollectionRuntimeRecord.model_validate(record)
        for record in read_jsonl_bytes(payloads["runtime_records.jsonl"])
    ]
    expected_outcomes = [
        KaggleTraceCollectionExpectedOutcomeRecord.model_validate(record)
        for record in read_jsonl_bytes(payloads["expected_outcomes.jsonl"])
    ]

    return (
        archive_sha256,
        payloads,
        manifest,
        manifest_payload,
        runtime_records,
        expected_outcomes,
    )


def join_trace_records(
    runtime_records: Sequence[KaggleTraceCollectionRuntimeRecord],
    expected_outcomes: Sequence[KaggleTraceCollectionExpectedOutcomeRecord],
) -> list[TracePair]:
    """Join runtime records to post-hoc outcomes using stable trace keys."""

    outcome_by_key: dict[TraceKey, KaggleTraceCollectionExpectedOutcomeRecord] = {}
    for outcome in expected_outcomes:
        key = _trace_key(outcome)
        if key in outcome_by_key:
            raise ValueError(f"duplicate expected outcome key: {key}")
        outcome_by_key[key] = outcome

    pairs: list[TracePair] = []
    seen_runtime_keys: set[TraceKey] = set()
    for runtime in runtime_records:
        key = _trace_key(runtime)
        if key in seen_runtime_keys:
            raise ValueError(f"duplicate runtime record key: {key}")
        seen_runtime_keys.add(key)
        outcome = outcome_by_key.get(key)
        if outcome is None:
            raise ValueError(f"missing expected outcome for runtime key: {key}")
        if runtime.case_id != outcome.case_id:
            raise ValueError(f"case_id mismatch for trace key: {key}")
        pairs.append((runtime, outcome))

    extra_outcome_keys = set(outcome_by_key).difference(seen_runtime_keys)
    if extra_outcome_keys:
        raise ValueError(f"outcomes without runtime records: {sorted(extra_outcome_keys)}")

    return pairs


def analyze_trace_archive(
    archive_path: Path,
    thresholds: Sequence[float] = DEFAULT_THRESHOLDS,
) -> KaggleTraceAnalysisReport:
    """Produce a deterministic diagnostic report for a retained trace archive."""

    (
        archive_sha256,
        payloads,
        manifest,
        manifest_payload,
        runtime_records,
        expected_outcomes,
    ) = load_trace_archive(archive_path)
    pairs = join_trace_records(runtime_records, expected_outcomes)

    matched_pairs = [pair for pair in pairs if pair[1].target_argmax_matches_candidate]
    nonmatched_pairs = [pair for pair in pairs if not pair[1].target_argmax_matches_candidate]

    match_count = len(matched_pairs)
    runtime_record_count = len(runtime_records)

    return KaggleTraceAnalysisReport(
        schema_version="specsafe-kaggle-trace-analysis-report-v1",
        collection_id=manifest.collection_id,
        collection_attempt_id=manifest.collection_attempt_id,
        source_commit_sha=manifest.source_commit_sha,
        preflight_attempt_id=str(manifest_payload["preflight_attempt_id"]),
        archive_sha256=archive_sha256,
        manifest_sha256=sha256_bytes(payloads["manifest.json"]),
        runtime_records_sha256=sha256_bytes(payloads["runtime_records.jsonl"]),
        expected_outcomes_sha256=sha256_bytes(payloads["expected_outcomes.jsonl"]),
        case_count=manifest.case_count,
        runtime_record_count=runtime_record_count,
        expected_outcome_record_count=len(expected_outcomes),
        target_argmax_match_count=match_count,
        target_argmax_nonmatch_count=len(nonmatched_pairs),
        target_argmax_match_rate=match_count / runtime_record_count,
        matched_candidate_stats=_candidate_stats(matched_pairs),
        nonmatched_candidate_stats=_candidate_stats(nonmatched_pairs),
        signal_diagnostics=TraceSignalDiagnostics(
            raw_draft_probability_pairwise_separation_rate=(
                _pairwise_probability_separation(matched_pairs, nonmatched_pairs)
            ),
            raw_draft_entropy_pairwise_lower_for_match_rate=(
                _pairwise_entropy_separation(matched_pairs, nonmatched_pairs)
            ),
            raw_draft_probability_brier_diagnostic=(_raw_draft_probability_brier_diagnostic(pairs)),
            support_interpretation=("directionally_supportive_small_sample_not_calibration_claim"),
        ),
        by_workload_type=_group_by_key(pairs, "workload_type"),
        by_case_id=_group_by_key(pairs, "case_id"),
        by_block_position_index=_group_by_key(pairs, "block_position_index"),
        raw_draft_probability_threshold_sensitivity=_threshold_diagnostics(
            pairs,
            thresholds,
        ),
        interpretation_boundary=TraceAnalysisBoundary(
            analysis_scope="local_retained_archive_diagnostics",
            calibration_fit_performed=False,
            policy_threshold_selected=False,
            policy_utility_evaluation_performed=False,
            throughput_or_latency_measurement_performed=False,
            public_dataset_release_authorized=False,
            production_readiness_claimed=False,
        ),
    )


def write_trace_analysis_report(
    archive_path: Path,
    output_path: Path,
) -> KaggleTraceAnalysisReport:
    """Analyze an archive and write a deterministic JSON report."""

    report = analyze_trace_archive(archive_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return report
