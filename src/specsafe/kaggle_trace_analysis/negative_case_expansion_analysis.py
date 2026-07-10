from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

COLLECTION_ID = "v5-qwen-negative-case-expansion-v1"
ATTEMPT_ID = "attempt-001-t4"
ANALYSIS_REPORT_ID = "v5_qwen_negative_case_expansion_v1_attempt_001_analysis"
REPLAY_REPORT_ID = "v5_qwen_negative_case_expansion_v1_attempt_001_replay"
ANALYSIS_STATUS = "diagnostic_analysis_only"
REPLAY_STATUS = "diagnostic_replay_only"
ARCHIVE_SHA256 = "557c7519aa6012c4770d9e24df1e15815a3295447f3eac2080b1b28c511c601e"

V2_RECORD_COUNT = 120
V2_MATCH_COUNT = 97
V2_NONMATCH_COUNT = 23
MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT = 30

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

REPLAY_THRESHOLDS: tuple[float, ...] = (
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


def _negative_case_intent_match_rates(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[str, dict[str, float | int]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"record_count": 0, "match_count": 0})

    for runtime_record, outcome_record in joined:
        intent = str(runtime_record["runtime_metadata"]["negative_case_intent"])
        bucket = buckets[intent]
        bucket["record_count"] += 1
        if outcome_record["conditional_acceptance_label"]:
            bucket["match_count"] += 1

    result: dict[str, dict[str, float | int]] = {}
    for intent in sorted(buckets):
        record_count = buckets[intent]["record_count"]
        match_count = buckets[intent]["match_count"]
        result[intent] = {
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


def _brier_score(joined: list[tuple[dict[str, Any], dict[str, Any]]]) -> float:
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


def _threshold_reports(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[dict[str, float | int | str]]:
    reports: list[dict[str, float | int | str]] = []
    total_count = len(joined)

    for threshold in REPLAY_THRESHOLDS:
        selected = [
            (runtime_record, outcome_record)
            for runtime_record, outcome_record in joined
            if float(runtime_record["raw_confidence"]) >= threshold
        ]
        selected_count = len(selected)
        match_count = sum(
            1 for _, outcome_record in selected if outcome_record["conditional_acceptance_label"]
        )
        nonmatch_count = selected_count - match_count

        reports.append(
            {
                "threshold": f"{threshold:.1f}",
                "threshold_value": threshold,
                "selected_count": selected_count,
                "selected_fraction": _rate(selected_count, total_count),
                "selected_match_count": match_count,
                "selected_nonmatch_count": nonmatch_count,
                "selected_match_rate": _rate(match_count, selected_count),
                "selected_nonmatch_rate": _rate(nonmatch_count, selected_count),
            }
        )

    return reports


def _load_attempt_inputs(
    attempt_dir: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    runtime_records = load_jsonl(attempt_dir / "runtime_records.jsonl")
    outcome_records = load_jsonl(attempt_dir / "expected_outcome_records.jsonl")
    timing_records = load_jsonl(attempt_dir / "timing_records.jsonl")
    trace_summary = load_json(attempt_dir / "trace_summary.json")
    environment_report = load_json(attempt_dir / "environment_report.json")
    retention_manifest = load_json(attempt_dir / "retention_manifest.json")

    return (
        runtime_records,
        outcome_records,
        timing_records,
        trace_summary,
        environment_report,
        retention_manifest,
    )


def _input_file_hashes(attempt_dir: Path) -> dict[str, str]:
    return {
        "environment_report.json": sha256_file(attempt_dir / "environment_report.json"),
        "expected_outcome_records.jsonl": sha256_file(
            attempt_dir / "expected_outcome_records.jsonl"
        ),
        "retention_manifest.json": sha256_file(attempt_dir / "retention_manifest.json"),
        "runtime_records.jsonl": sha256_file(attempt_dir / "runtime_records.jsonl"),
        "timing_records.jsonl": sha256_file(attempt_dir / "timing_records.jsonl"),
        "trace_summary.json": sha256_file(attempt_dir / "trace_summary.json"),
    }


def _manifest_hash_status(
    input_file_hashes: dict[str, str],
    retention_manifest: dict[str, Any],
) -> dict[str, bool]:
    expected_hashes = retention_manifest["file_hashes"]
    return {
        name: input_file_hashes[name] == expected_hashes[name] for name in sorted(expected_hashes)
    }


def _combined_raw_count_implication(match_count: int, nonmatch_count: int) -> dict[str, Any]:
    combined_records = V2_RECORD_COUNT + match_count + nonmatch_count
    combined_matches = V2_MATCH_COUNT + match_count
    combined_nonmatches = V2_NONMATCH_COUNT + nonmatch_count
    shortfall_after_collection = max(
        0,
        MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT - combined_nonmatches,
    )

    return {
        "v2_record_count": V2_RECORD_COUNT,
        "v2_match_count": V2_MATCH_COUNT,
        "v2_nonmatch_count": V2_NONMATCH_COUNT,
        "negative_case_record_count": match_count + nonmatch_count,
        "negative_case_match_count": match_count,
        "negative_case_nonmatch_count": nonmatch_count,
        "combined_record_count": combined_records,
        "combined_match_count": combined_matches,
        "combined_nonmatch_count": combined_nonmatches,
        "minimum_negative_count_for_calibration_fit": (MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT),
        "negative_count_floor_crossed_on_raw_count": (
            combined_nonmatches >= MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT
        ),
        "negative_count_shortfall_after_collection": shortfall_after_collection,
        "calibration_fit_authorized_by_this_report": False,
    }


def build_negative_case_analysis_report(attempt_dir: Path) -> dict[str, Any]:
    (
        runtime_records,
        outcome_records,
        timing_records,
        trace_summary,
        environment_report,
        retention_manifest,
    ) = _load_attempt_inputs(attempt_dir)

    joined = _joined_records(runtime_records, outcome_records)
    runtime_forbidden_fields = sorted(
        {
            field
            for record in runtime_records
            for field in FORBIDDEN_RUNTIME_FIELDS
            if field in record
        }
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
    file_hashes = _input_file_hashes(attempt_dir)

    return {
        "analysis_status": ANALYSIS_STATUS,
        "attempt_id": trace_summary["attempt_id"],
        "calibration_fit_status": "not_authorized_by_analysis",
        "collection_id": trace_summary["collection_id"],
        "combined_raw_count_implication": _combined_raw_count_implication(
            match_count,
            nonmatch_count,
        ),
        "data_role": "post_collection_analysis",
        "evidence_class": trace_summary["evidence_class"],
        "input_file_hashes": file_hashes,
        "manifest_hash_status": _manifest_hash_status(file_hashes, retention_manifest),
        "model_pair_id": environment_report["draft_model_id"].lower().replace("/", "-")
        + "-draft-"
        + environment_report["target_model_id"].lower().replace("/", "-")
        + "-target",
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
        "report_id": ANALYSIS_REPORT_ID,
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
            "archive_sha256": ARCHIVE_SHA256,
            "raw_prompt_text_retained": trace_summary["raw_prompt_text_retained"],
            "secrets_printed": environment_report["secrets_printed"],
            "source_commit": environment_report["source_commit"],
        },
        "stratification": {
            "negative_case_intent_match_rates": _negative_case_intent_match_rates(joined),
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


def build_negative_case_replay_report(attempt_dir: Path) -> dict[str, Any]:
    (
        runtime_records,
        outcome_records,
        timing_records,
        trace_summary,
        environment_report,
        retention_manifest,
    ) = _load_attempt_inputs(attempt_dir)
    del timing_records
    del retention_manifest

    joined = _joined_records(runtime_records, outcome_records)
    threshold_reports = _threshold_reports(joined)
    match_count = sum(
        1 for _, outcome_record in joined if outcome_record["conditional_acceptance_label"]
    )
    nonmatch_count = len(joined) - match_count

    return {
        "attempt_id": trace_summary["attempt_id"],
        "calibration_fit_status": "not_authorized_by_replay",
        "collection_id": trace_summary["collection_id"],
        "combined_raw_count_implication": _combined_raw_count_implication(
            match_count,
            nonmatch_count,
        ),
        "data_role": "post_collection_diagnostic_replay",
        "evidence_class": trace_summary["evidence_class"],
        "nonclaim_boundaries": {
            "production_claim_status": "not_authorized",
            "public_release_status": "not_authorized",
            "scheduler_promotion_status": "not_authorized",
            "threshold_promotion_status": "not_authorized",
        },
        "record_counts": {
            "expected_outcome_record_count": len(outcome_records),
            "runtime_record_count": len(runtime_records),
        },
        "replay_status": REPLAY_STATUS,
        "report_id": REPLAY_REPORT_ID,
        "source_archive_boundary": {
            "archive_sha256": ARCHIVE_SHA256,
            "raw_prompt_text_retained": trace_summary["raw_prompt_text_retained"],
            "secrets_printed": environment_report["secrets_printed"],
            "source_commit": environment_report["source_commit"],
        },
        "threshold_diagnostics": threshold_reports,
        "threshold_promotion_status": "not_authorized_by_replay",
        "trace_schema_version": trace_summary["trace_schema_version"],
    }


def write_negative_case_reports(attempt_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    analysis_report = build_negative_case_analysis_report(attempt_dir)
    replay_report = build_negative_case_replay_report(attempt_dir)

    write_json_lf(attempt_dir / "trace_analysis_report.json", analysis_report)
    write_json_lf(attempt_dir / "trace_replay_report.json", replay_report)

    return analysis_report, replay_report
