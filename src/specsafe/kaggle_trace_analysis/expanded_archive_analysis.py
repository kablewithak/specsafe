from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

V2_COLLECTION_ID = "v5-qwen-governed-trace-collection-v2"
V2_ATTEMPT_ID = "attempt-001-t4"
REPORT_ID = "v5_qwen_trace_collection_v2_attempt_001_analysis"
ANALYSIS_STATUS = "diagnostic_analysis_only"

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

PROBABILITY_BINS: tuple[tuple[float, float], ...] = (
    (0.0, 0.2),
    (0.2, 0.4),
    (0.4, 0.6),
    (0.6, 0.8),
    (0.8, 1.0),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_json_lf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }

    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
    }


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
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


def _match_rates_by_key(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    key: str,
) -> dict[str, dict[str, float | int]]:
    buckets: dict[Any, dict[str, int]] = defaultdict(lambda: {"record_count": 0, "match_count": 0})

    for runtime_record, outcome_record in joined:
        bucket = buckets[runtime_record[key]]
        bucket["record_count"] += 1
        if outcome_record["conditional_acceptance_label"]:
            bucket["match_count"] += 1

    result: dict[str, dict[str, float | int]] = {}
    for value in sorted(buckets, key=str):
        record_count = buckets[value]["record_count"]
        match_count = buckets[value]["match_count"]
        result[str(value)] = {
            "record_count": record_count,
            "match_count": match_count,
            "nonmatch_count": record_count - match_count,
            "match_rate": _rate(match_count, record_count),
        }

    return result


def _is_in_probability_bin(value: float, lower: float, upper: float) -> bool:
    if upper == 1.0:
        return lower <= value <= upper
    return lower <= value < upper


def _probability_bin_report(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[dict[str, float | int | str | None]]:
    reports: list[dict[str, float | int | str | None]] = []

    for lower, upper in PROBABILITY_BINS:
        records = [
            (runtime_record, outcome_record)
            for runtime_record, outcome_record in joined
            if _is_in_probability_bin(
                float(runtime_record["raw_confidence"]),
                lower,
                upper,
            )
        ]
        match_count = sum(
            1 for _, outcome_record in records if outcome_record["conditional_acceptance_label"]
        )
        confidences = [float(runtime_record["raw_confidence"]) for runtime_record, _ in records]
        record_count = len(records)
        observed_match_rate = _rate(match_count, record_count)
        mean_confidence = mean(confidences) if confidences else None
        calibration_gap = None
        if mean_confidence is not None:
            calibration_gap = abs(observed_match_rate - mean_confidence)

        reports.append(
            {
                "bin": f"[{lower:.1f}, {upper:.1f}{']' if upper == 1.0 else ')'}",
                "lower": lower,
                "upper": upper,
                "record_count": record_count,
                "match_count": match_count,
                "nonmatch_count": record_count - match_count,
                "mean_confidence": mean_confidence,
                "observed_match_rate": observed_match_rate,
                "calibration_gap": calibration_gap,
            }
        )

    return reports


def _brier_score(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
) -> float:
    squared_errors = []
    for runtime_record, outcome_record in joined:
        confidence = float(runtime_record["raw_confidence"])
        label = 1.0 if outcome_record["conditional_acceptance_label"] else 0.0
        squared_errors.append((confidence - label) ** 2)

    return mean(squared_errors)


def _expected_calibration_error(
    bin_reports: list[dict[str, Any]],
    total_count: int,
) -> float:
    weighted_gaps = []
    for bin_report in bin_reports:
        record_count = int(bin_report["record_count"])
        calibration_gap = bin_report["calibration_gap"]
        if record_count == 0 or calibration_gap is None:
            continue
        weighted_gaps.append((record_count / total_count) * float(calibration_gap))

    return sum(weighted_gaps)


def _maximum_calibration_error(bin_reports: list[dict[str, Any]]) -> float:
    gaps = [
        float(bin_report["calibration_gap"])
        for bin_report in bin_reports
        if bin_report["calibration_gap"] is not None
    ]
    if not gaps:
        return 0.0
    return max(gaps)


def _roc_auc(pos_scores: list[float], neg_scores: list[float]) -> float | None:
    if not pos_scores or not neg_scores:
        return None

    wins = 0.0
    for pos_score in pos_scores:
        for neg_score in neg_scores:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5

    return wins / (len(pos_scores) * len(neg_scores))


def build_trace_analysis_report(attempt_dir: Path) -> dict[str, Any]:
    runtime_path = attempt_dir / "runtime_records.jsonl"
    outcome_path = attempt_dir / "expected_outcome_records.jsonl"
    timing_path = attempt_dir / "timing_records.jsonl"
    summary_path = attempt_dir / "trace_summary.json"
    environment_path = attempt_dir / "environment_report.json"
    retention_manifest_path = attempt_dir / "retention_manifest.json"

    runtime_records = load_jsonl(runtime_path)
    outcome_records = load_jsonl(outcome_path)
    timing_records = load_jsonl(timing_path)
    trace_summary = load_json(summary_path)
    environment_report = load_json(environment_path)
    retention_manifest = load_json(retention_manifest_path)

    joined = _joined_records(runtime_records, outcome_records)
    runtime_forbidden_fields = sorted(
        field for record in runtime_records for field in FORBIDDEN_RUNTIME_FIELDS if field in record
    )

    match_confidences = [
        float(runtime_record["raw_confidence"])
        for runtime_record, outcome_record in joined
        if outcome_record["conditional_acceptance_label"]
    ]
    nonmatch_confidences = [
        float(runtime_record["raw_confidence"])
        for runtime_record, outcome_record in joined
        if not outcome_record["conditional_acceptance_label"]
    ]
    match_entropies = [
        float(runtime_record["draft_entropy"])
        for runtime_record, outcome_record in joined
        if outcome_record["conditional_acceptance_label"]
    ]
    nonmatch_entropies = [
        float(runtime_record["draft_entropy"])
        for runtime_record, outcome_record in joined
        if not outcome_record["conditional_acceptance_label"]
    ]

    bin_reports = _probability_bin_report(joined)
    match_count = len(match_confidences)
    nonmatch_count = len(nonmatch_confidences)
    total_count = len(joined)

    input_file_hashes = {
        "environment_report.json": sha256_file(environment_path),
        "expected_outcome_records.jsonl": sha256_file(outcome_path),
        "retention_manifest.json": sha256_file(retention_manifest_path),
        "runtime_records.jsonl": sha256_file(runtime_path),
        "timing_records.jsonl": sha256_file(timing_path),
        "trace_summary.json": sha256_file(summary_path),
    }

    expected_hashes = retention_manifest["file_hashes"]
    manifest_hash_status = {
        name: input_file_hashes[name] == expected_hashes[name] for name in sorted(expected_hashes)
    }

    return {
        "analysis_status": ANALYSIS_STATUS,
        "attempt_id": trace_summary["attempt_id"],
        "calibration_fit_status": "not_authorized_by_analysis",
        "collection_id": trace_summary["collection_id"],
        "data_role": "post_collection_analysis",
        "evidence_class": trace_summary["evidence_class"],
        "input_file_hashes": input_file_hashes,
        "manifest_hash_status": manifest_hash_status,
        "model_pair_id": _model_pair_id_from_env(environment_report),
        "nonclaim_boundaries": {
            "production_claim_status": "not_authorized",
            "scheduler_promotion_status": "not_authorized",
            "threshold_promotion_status": "not_authorized",
        },
        "record_counts": {
            "case_count": trace_summary["case_count"],
            "expected_outcome_record_count": len(outcome_records),
            "runtime_record_count": len(runtime_records),
            "timing_record_count": len(timing_records),
        },
        "report_id": REPORT_ID,
        "runtime_outcome_join_status": {
            "one_to_one_join_passed": True,
            "joined_record_count": total_count,
            "runtime_forbidden_fields_present": runtime_forbidden_fields,
        },
        "signal_diagnostics": {
            "draft_entropy_by_acceptance": {
                "matches": _numeric_summary(match_entropies),
                "nonmatches": _numeric_summary(nonmatch_entropies),
            },
            "fixed_probability_bins": bin_reports,
            "raw_confidence_by_acceptance": {
                "all_records": _numeric_summary(
                    [float(runtime_record["raw_confidence"]) for runtime_record, _ in joined]
                ),
                "matches": _numeric_summary(match_confidences),
                "nonmatches": _numeric_summary(nonmatch_confidences),
            },
            "raw_confidence_brier_diagnostic": _brier_score(joined),
            "raw_confidence_roc_auc_diagnostic": _roc_auc(
                match_confidences,
                nonmatch_confidences,
            ),
            "target_argmax_match_count": match_count,
            "target_argmax_match_rate": _rate(match_count, total_count),
            "target_argmax_nonmatch_count": nonmatch_count,
            "fixed_bin_expected_calibration_error": _expected_calibration_error(
                bin_reports,
                total_count,
            ),
            "fixed_bin_maximum_calibration_error": _maximum_calibration_error(
                bin_reports,
            ),
        },
        "source_archive_boundary": {
            "archive_sha256": "b8803ea500378a6b91af6b0a5206fc4359d9b3f8bf1888a01907ded6f11e0e7a",
            "raw_prompt_text_retained": trace_summary["raw_prompt_text_retained"],
            "secrets_printed": environment_report["secrets_printed"],
            "source_commit": environment_report["source_commit"],
        },
        "stratification": {
            "position_match_rates": _match_rates_by_key(joined, "block_position_index"),
            "split_match_rates": _match_rates_by_key(joined, "split"),
            "workload_match_rates": _match_rates_by_key(joined, "workload_type"),
            "split_record_counts": _count_dict(
                Counter(runtime_record["split"] for runtime_record in runtime_records)
            ),
            "workload_record_counts": _count_dict(
                Counter(runtime_record["workload_type"] for runtime_record in runtime_records)
            ),
        },
        "threshold_promotion_status": "not_authorized_by_analysis",
        "trace_schema_version": trace_summary["trace_schema_version"],
    }


def _model_pair_id_from_env(environment_report: dict[str, Any]) -> str:
    draft = environment_report["draft_model_id"].lower().replace("/", "-")
    target = environment_report["target_model_id"].lower().replace("/", "-")
    return f"{draft}-draft-{target}-target"
