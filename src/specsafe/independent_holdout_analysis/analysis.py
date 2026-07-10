from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from specsafe.independent_holdout_analysis.models import (
    AnalysisStatus,
    CoverageSummary,
    IndependentHoldoutAnalysisReport,
    PromotionStatus,
    ReplayFieldMap,
)

_JOIN_FIELDS = ("trace_id", "decode_round", "block_position_index")
_REQUIRED_RUNTIME_FIELDS = (
    "trace_id",
    "case_id",
    "decode_round",
    "block_position_index",
    "raw_confidence",
    "workload_type",
    "collection_id",
    "attempt_id",
    "trace_schema_version",
)
_REQUIRED_OUTCOME_FIELDS = (
    "trace_id",
    "case_id",
    "decode_round",
    "block_position_index",
    "observed_acceptance",
    "workload_type",
    "collection_id",
    "attempt_id",
    "trace_schema_version",
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object at {path}:{line_number}")
        records.append(value)
    return records


def _join_key(record: dict[str, Any]) -> tuple[str, int, int]:
    return (
        str(record["trace_id"]),
        int(record["decode_round"]),
        int(record["block_position_index"]),
    )


def _missing_fields(records: list[dict[str, Any]], required: tuple[str, ...]) -> set[str]:
    missing: set[str] = set()
    for record in records:
        missing.update(field for field in required if field not in record)
    return missing


def _coverage(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> CoverageSummary:
    positives = sum(bool(outcome["observed_acceptance"]) for _, outcome in rows)
    count = len(rows)
    return CoverageSummary(
        record_count=count,
        positive_count=positives,
        negative_count=count - positives,
        positive_rate=positives / count if count else 0.0,
        mean_raw_confidence=(
            sum(float(runtime["raw_confidence"]) for runtime, _ in rows) / count if count else 0.0
        ),
    )


def _pairwise_auc(labels_and_scores: list[tuple[bool, float]]) -> float:
    positives = [score for label, score in labels_and_scores if label]
    negatives = [score for label, score in labels_and_scores if not label]
    if not positives or not negatives:
        return 0.5
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def analyze_independent_holdout(
    archive_dir: Path,
    *,
    source_commit: str,
) -> IndependentHoldoutAnalysisReport:
    retention = _load_json(archive_dir / "archive_retention_report.json")
    summary = _load_json(archive_dir / "trace_summary.json")
    runtime_records = _load_jsonl(archive_dir / "runtime_records.jsonl")
    outcome_records = _load_jsonl(archive_dir / "expected_outcome_records.jsonl")
    timing_records = _load_jsonl(archive_dir / "timing_records.jsonl")

    missing_runtime_fields = _missing_fields(runtime_records, _REQUIRED_RUNTIME_FIELDS)
    missing_outcome_fields = _missing_fields(outcome_records, _REQUIRED_OUTCOME_FIELDS)

    runtime_keys = [_join_key(record) for record in runtime_records]
    outcome_keys = [_join_key(record) for record in outcome_records]
    timing_keys = [str(record["trace_id"]) for record in timing_records]
    duplicate_count = sum(count - 1 for count in Counter(runtime_keys).values() if count > 1)
    duplicate_count += sum(count - 1 for count in Counter(outcome_keys).values() if count > 1)
    duplicate_count += sum(count - 1 for count in Counter(timing_keys).values() if count > 1)

    outcomes_by_key = {_join_key(record): record for record in outcome_records}
    timing_trace_ids = set(timing_keys)
    joined_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    missing_outcomes = 0
    missing_timings = 0
    consistency_failures: list[str] = []

    for runtime in runtime_records:
        key = _join_key(runtime)
        outcome = outcomes_by_key.get(key)
        if outcome is None:
            missing_outcomes += 1
            continue
        if str(runtime["trace_id"]) not in timing_trace_ids:
            missing_timings += 1
        for field in ("case_id", "workload_type", "collection_id", "attempt_id"):
            if runtime[field] != outcome[field]:
                consistency_failures.append(f"join_field_mismatch:{field}:{runtime['trace_id']}")
        joined_rows.append((runtime, outcome))

    by_workload: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    by_position: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for runtime, outcome in joined_rows:
        by_workload[str(runtime["workload_type"])].append((runtime, outcome))
        by_position[str(runtime["block_position_index"])].append((runtime, outcome))

    labels_and_scores = [
        (bool(outcome["observed_acceptance"]), float(runtime["raw_confidence"]))
        for runtime, outcome in joined_rows
    ]
    raw_brier = (
        sum((score - int(label)) ** 2 for label, score in labels_and_scores)
        / len(labels_and_scores)
        if labels_and_scores
        else 0.0
    )
    scores = [score for _, score in labels_and_scores]

    blockers: list[str] = []
    if missing_runtime_fields:
        blockers.append("missing_required_runtime_fields")
    if missing_outcome_fields:
        blockers.append("missing_required_outcome_fields")
    if duplicate_count:
        blockers.append("duplicate_join_keys")
    if missing_outcomes:
        blockers.append("missing_runtime_outcomes")
    if missing_timings:
        blockers.append("missing_runtime_timings")
    if consistency_failures:
        blockers.append("cross_record_identity_mismatch")
    if len(joined_rows) != len(runtime_records):
        blockers.append("incomplete_runtime_outcome_join")

    status = AnalysisStatus.REPLAY_BLOCKED if blockers else AnalysisStatus.REPLAY_READY
    return IndependentHoldoutAnalysisReport(
        schema_version="independent_holdout_analysis_report_v1",
        report_id="v5-qwen-candidate-calibrator-independent-holdout-analysis-v1",
        source_commit=source_commit,
        collection_id=str(summary["collection_id"]),
        attempt_id=str(summary["attempt_id"]),
        data_role=str(summary["data_role"]),
        evidence_class=str(summary["evidence_class"]),
        trace_schema_version=str(summary["trace_schema_version"]),
        runtime_record_count=len(runtime_records),
        expected_outcome_record_count=len(outcome_records),
        timing_record_count=len(timing_records),
        unique_trace_count=len(set(str(record["trace_id"]) for record in runtime_records)),
        case_count=len(set(str(record["case_id"]) for record in runtime_records)),
        joined_record_count=len(joined_rows),
        duplicate_join_key_count=duplicate_count,
        missing_runtime_outcome_count=missing_outcomes,
        missing_runtime_timing_count=missing_timings,
        raw_prompt_text_retained=bool(retention["raw_prompt_text_retained"]),
        raw_brier_diagnostic=raw_brier,
        raw_discrimination_auc=_pairwise_auc(labels_and_scores),
        raw_confidence_min=min(scores) if scores else 0.0,
        raw_confidence_max=max(scores) if scores else 0.0,
        coverage_by_workload={key: _coverage(value) for key, value in sorted(by_workload.items())},
        coverage_by_position={key: _coverage(value) for key, value in sorted(by_position.items())},
        replay_field_map=ReplayFieldMap(
            join_key=_JOIN_FIELDS,
            calibrator_input_field="raw_confidence",
            diagnostic_label_field="observed_acceptance",
            workload_field="workload_type",
            position_field="block_position_index",
            provenance_fields=(
                "collection_id",
                "attempt_id",
                "trace_schema_version",
                "model_pair_id",
                "draft_model_revision",
                "target_model_revision",
                "tokenizer_revision",
                "split",
            ),
            forbidden_fit_actions=(
                "refit_candidate_calibrator_from_holdout_archive",
                "tune_thresholds_from_holdout_archive",
                "tune_scheduler_from_holdout_archive",
            ),
        ),
        required_runtime_fields_present=tuple(
            field for field in _REQUIRED_RUNTIME_FIELDS if field not in missing_runtime_fields
        ),
        required_outcome_fields_present=tuple(
            field for field in _REQUIRED_OUTCOME_FIELDS if field not in missing_outcome_fields
        ),
        analysis_status=status,
        replay_blockers=tuple(blockers),
        calibrator_promotion_status=PromotionStatus.NOT_AUTHORIZED,
        threshold_promotion_status="not_authorized",
        scheduler_promotion_status="not_authorized",
        claims_permitted=(
            "The retained independent holdout records are aligned for no-refit replay.",
            (
                "The archive contains sufficient positive and negative diagnostic labels "
                "for replay analysis."
            ),
        ),
        claims_forbidden=(
            "The candidate calibrator passed independent holdout replay.",
            "The candidate calibrator is promoted.",
            "Any threshold or scheduler is promoted.",
            "Production speed, latency, throughput, cost, or serving readiness is proven.",
        ),
    )


def write_analysis_report(
    archive_dir: Path,
    output_path: Path,
    *,
    source_commit: str,
) -> IndependentHoldoutAnalysisReport:
    report = analyze_independent_holdout(archive_dir, source_commit=source_commit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
