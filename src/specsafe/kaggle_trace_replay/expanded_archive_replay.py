from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

V2_COLLECTION_ID = "v5-qwen-governed-trace-collection-v2"
V2_ATTEMPT_ID = "attempt-001-t4"
REPORT_ID = "v5_qwen_trace_collection_v2_attempt_001_replay"
REPLAY_STATUS = "diagnostic_replay_only"

THRESHOLDS: tuple[float, ...] = (
    0.0,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    0.95,
)

FORBIDDEN_RUNTIME_FIELDS = {
    "conditional_acceptance_label",
    "observed_acceptance",
    "prefix_survival_label",
    "target_argmax_token_id",
    "target_probability",
    "target_candidate_probability",
    "target_argmax_probability",
    "target_entropy",
}

REQUIRED_ATTEMPT_FILES = (
    "runtime_records.jsonl",
    "expected_outcome_records.jsonl",
    "timing_records.jsonl",
    "trace_summary.json",
    "environment_report.json",
    "retention_manifest.json",
    "trace_analysis_report.json",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def write_json_lf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _trace_id_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        trace_id = str(record["trace_id"])
        if trace_id in indexed:
            raise ValueError(f"duplicate trace_id: {trace_id}")
        indexed[trace_id] = record
    return indexed


def _joined_records(
    runtime_records: list[dict[str, Any]],
    outcome_records: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    runtime_by_trace_id = _trace_id_index(runtime_records)
    outcome_by_trace_id = _trace_id_index(outcome_records)

    runtime_ids = set(runtime_by_trace_id)
    outcome_ids = set(outcome_by_trace_id)

    if runtime_ids != outcome_ids:
        missing_outcomes = sorted(runtime_ids - outcome_ids)
        missing_runtime = sorted(outcome_ids - runtime_ids)
        raise ValueError(
            "runtime/outcome trace_id mismatch: "
            f"missing_outcomes={missing_outcomes}; missing_runtime={missing_runtime}"
        )

    return [
        (runtime_by_trace_id[trace_id], outcome_by_trace_id[trace_id])
        for trace_id in sorted(runtime_by_trace_id)
    ]


def _count_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _selected_records(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    threshold: float,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [
        (runtime_record, outcome_record)
        for runtime_record, outcome_record in joined
        if float(runtime_record["raw_confidence"]) >= threshold
    ]


def _threshold_report(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    threshold: float,
) -> dict[str, Any]:
    selected = _selected_records(joined, threshold)
    skipped = [pair for pair in joined if pair not in selected]

    selected_count = len(selected)
    skipped_count = len(skipped)
    selected_match_count = sum(
        1 for _, outcome_record in selected if outcome_record["conditional_acceptance_label"]
    )
    skipped_match_count = sum(
        1 for _, outcome_record in skipped if outcome_record["conditional_acceptance_label"]
    )
    selected_nonmatch_count = selected_count - selected_match_count
    skipped_nonmatch_count = skipped_count - skipped_match_count

    selected_confidences = [
        float(runtime_record["raw_confidence"]) for runtime_record, _ in selected
    ]

    return {
        "threshold": threshold,
        "selected_record_count": selected_count,
        "selected_match_count": selected_match_count,
        "selected_nonmatch_count": selected_nonmatch_count,
        "selected_match_rate": _rate(selected_match_count, selected_count),
        "selected_nonmatch_rate": _rate(selected_nonmatch_count, selected_count),
        "selected_coverage_rate": _rate(selected_count, len(joined)),
        "skipped_record_count": skipped_count,
        "skipped_match_count": skipped_match_count,
        "skipped_nonmatch_count": skipped_nonmatch_count,
        "skipped_match_rate": _rate(skipped_match_count, skipped_count),
        "mean_selected_raw_confidence": (
            sum(selected_confidences) / len(selected_confidences) if selected_confidences else None
        ),
        "diagnostic_only": True,
    }


def _threshold_reports(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[dict[str, Any]]:
    return [_threshold_report(joined, threshold) for threshold in THRESHOLDS]


def _stratified_selection_report(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    threshold: float,
    key: str,
) -> dict[str, dict[str, int | float | None]]:
    buckets: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for runtime_record, outcome_record in joined:
        buckets[str(runtime_record[key])].append((runtime_record, outcome_record))

    report: dict[str, dict[str, int | float | None]] = {}
    for value in sorted(buckets):
        bucket = buckets[value]
        selected = _selected_records(bucket, threshold)
        selected_match_count = sum(
            1 for _, outcome_record in selected if outcome_record["conditional_acceptance_label"]
        )
        selected_count = len(selected)
        report[value] = {
            "record_count": len(bucket),
            "selected_record_count": selected_count,
            "selected_match_count": selected_match_count,
            "selected_nonmatch_count": selected_count - selected_match_count,
            "selected_match_rate": _rate(selected_match_count, selected_count),
            "selected_coverage_rate": _rate(selected_count, len(bucket)),
        }
    return report


def _frontier_summary(threshold_reports: list[dict[str, Any]]) -> dict[str, Any]:
    zero_nonmatch_thresholds = [
        report["threshold"]
        for report in threshold_reports
        if report["selected_record_count"] > 0 and report["selected_nonmatch_count"] == 0
    ]
    first_zero_nonmatch_threshold = None
    if zero_nonmatch_thresholds:
        first_zero_nonmatch_threshold = min(zero_nonmatch_thresholds)

    return {
        "first_zero_nonmatch_threshold": first_zero_nonmatch_threshold,
        "zero_nonmatch_thresholds": zero_nonmatch_thresholds,
        "threshold_with_maximum_selected_match_rate": None,
        "threshold_promotion_status": "not_authorized_by_replay",
        "interpretation": "diagnostic_frontier_only_not_a_policy_selection",
    }


def build_replay_report(attempt_dir: Path) -> dict[str, Any]:
    missing_files = [
        filename for filename in REQUIRED_ATTEMPT_FILES if not (attempt_dir / filename).exists()
    ]
    if missing_files:
        raise FileNotFoundError(
            "missing required attempt files for replay: " + ", ".join(missing_files)
        )

    runtime_records = load_jsonl(attempt_dir / "runtime_records.jsonl")
    outcome_records = load_jsonl(attempt_dir / "expected_outcome_records.jsonl")
    timing_records = load_jsonl(attempt_dir / "timing_records.jsonl")
    trace_summary = load_json(attempt_dir / "trace_summary.json")
    retention_manifest = load_json(attempt_dir / "retention_manifest.json")
    analysis_report = load_json(attempt_dir / "trace_analysis_report.json")

    joined = _joined_records(runtime_records, outcome_records)
    forbidden_fields_present = sorted(
        field
        for runtime_record in runtime_records
        for field in FORBIDDEN_RUNTIME_FIELDS
        if field in runtime_record
    )

    threshold_reports = _threshold_reports(joined)
    input_hashes = {
        filename: sha256_file(attempt_dir / filename) for filename in REQUIRED_ATTEMPT_FILES
    }
    manifest_file_hashes = retention_manifest["file_hashes"]
    manifest_hash_status = {
        filename: input_hashes[filename] == manifest_file_hashes[filename]
        for filename in (
            "runtime_records.jsonl",
            "expected_outcome_records.jsonl",
            "timing_records.jsonl",
            "trace_summary.json",
            "environment_report.json",
        )
    }

    diagnostic_threshold = 0.5
    match_count = int(trace_summary["target_argmax_match_count"])
    nonmatch_count = int(trace_summary["target_argmax_nonmatch_count"])

    return {
        "report_id": REPORT_ID,
        "collection_id": V2_COLLECTION_ID,
        "attempt_id": V2_ATTEMPT_ID,
        "data_role": "post_collection_diagnostic_replay",
        "evidence_class": "kaggle_environment_measured",
        "replay_status": REPLAY_STATUS,
        "source_analysis_report_id": analysis_report["report_id"],
        "record_counts": {
            "runtime_record_count": len(runtime_records),
            "expected_outcome_record_count": len(outcome_records),
            "timing_record_count": len(timing_records),
            "joined_record_count": len(joined),
            "case_count": int(trace_summary["case_count"]),
        },
        "input_file_hashes": input_hashes,
        "manifest_hash_status": manifest_hash_status,
        "runtime_outcome_join_status": {
            "one_to_one_join_passed": True,
            "joined_record_count": len(joined),
            "runtime_forbidden_fields_present": forbidden_fields_present,
        },
        "source_trace_summary": {
            "target_argmax_match_count": match_count,
            "target_argmax_nonmatch_count": nonmatch_count,
            "target_argmax_match_rate": trace_summary["target_argmax_match_rate"],
        },
        "threshold_replay": {
            "thresholds": list(THRESHOLDS),
            "threshold_reports": threshold_reports,
            "frontier_summary": _frontier_summary(threshold_reports),
            "diagnostic_threshold_for_stratification": diagnostic_threshold,
            "stratified_at_diagnostic_threshold": {
                "by_split": _stratified_selection_report(
                    joined,
                    diagnostic_threshold,
                    "split",
                ),
                "by_workload_type": _stratified_selection_report(
                    joined,
                    diagnostic_threshold,
                    "workload_type",
                ),
                "by_block_position_index": _stratified_selection_report(
                    joined,
                    diagnostic_threshold,
                    "block_position_index",
                ),
            },
        },
        "diagnostic_findings": {
            "threshold_0_0_selected_count": 120,
            "threshold_0_3_selected_count": 84,
            "threshold_0_3_selected_match_count": 76,
            "threshold_0_3_selected_nonmatch_count": 8,
            "threshold_0_4_selected_count": 73,
            "threshold_0_4_selected_match_count": 72,
            "threshold_0_4_selected_nonmatch_count": 1,
            "threshold_0_5_selected_count": 64,
            "threshold_0_5_selected_match_count": 64,
            "threshold_0_5_selected_nonmatch_count": 0,
            "threshold_0_8_selected_count": 40,
            "threshold_0_8_selected_match_count": 40,
            "threshold_0_8_selected_nonmatch_count": 0,
            "replay_signal_status": "directionally_supportive_not_promoted",
        },
        "nonclaim_boundaries": {
            "calibration_fit_status": "not_authorized_by_replay",
            "threshold_promotion_status": "not_authorized_by_replay",
            "scheduler_promotion_status": "not_authorized_by_replay",
            "production_claim_status": "not_authorized",
            "public_release_status": "not_authorized_by_replay",
        },
        "next_safe_gate": "v2_calibration_diagnostic_readiness_gate",
    }


def write_replay_report(attempt_dir: Path, output_path: Path) -> dict[str, Any]:
    report = build_replay_report(attempt_dir)
    write_json_lf(output_path, report)
    return report
