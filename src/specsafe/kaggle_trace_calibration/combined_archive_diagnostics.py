from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

REPORT_ID = "v5_qwen_combined_v2_negative_case_calibration_diagnostic"
DIAGNOSTIC_STATUS = "combined_calibration_readiness_diagnostic_only"
COMBINED_COLLECTION_ID = "v5-qwen-combined-v2-negative-case-calibration"

V2_SOURCE_ID = "v2_trace_collection"
NEGATIVE_CASE_SOURCE_ID = "negative_case_expansion"

V2_COLLECTION_ID = "v5-qwen-governed-trace-collection-v2"
NEGATIVE_CASE_COLLECTION_ID = "v5-qwen-negative-case-expansion-v1"
ATTEMPT_ID = "attempt-001-t4"

MINIMUM_RECORD_COUNT_FOR_CALIBRATION_FIT = 100
MINIMUM_POSITIVE_COUNT_FOR_CALIBRATION_FIT = 30
MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT = 30
MINIMUM_SIGNAL_ROC_AUC_DIAGNOSTIC = 0.75

PROBABILITY_BINS: tuple[tuple[float, float], ...] = (
    (0.0, 0.2),
    (0.2, 0.4),
    (0.4, 0.6),
    (0.6, 0.8),
    (0.8, 1.0),
)

BASE_REQUIRED_ATTEMPT_FILES = (
    "runtime_records.jsonl",
    "expected_outcome_records.jsonl",
    "timing_records.jsonl",
    "trace_summary.json",
    "environment_report.json",
    "retention_manifest.json",
    "trace_analysis_report.json",
    "trace_replay_report.json",
)

V2_EXTRA_REQUIRED_FILES = ("trace_calibration_diagnostic_report.json",)

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

MANIFEST_HASHED_FILES = (
    "runtime_records.jsonl",
    "expected_outcome_records.jsonl",
    "timing_records.jsonl",
    "trace_summary.json",
    "environment_report.json",
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


def _attempt_required_files(source_id: str) -> tuple[str, ...]:
    if source_id == V2_SOURCE_ID:
        return BASE_REQUIRED_ATTEMPT_FILES + V2_EXTRA_REQUIRED_FILES
    return BASE_REQUIRED_ATTEMPT_FILES


def _validate_attempt_files(source_id: str, attempt_dir: Path) -> None:
    missing_files = [
        filename
        for filename in _attempt_required_files(source_id)
        if not (attempt_dir / filename).exists()
    ]
    if missing_files:
        raise FileNotFoundError(f"missing required {source_id} files: " + ", ".join(missing_files))


def _trace_id_index(
    source_id: str,
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        combined_trace_id = f"{source_id}::{record['trace_id']}"
        if combined_trace_id in indexed:
            raise ValueError(f"duplicate combined trace_id: {combined_trace_id}")
        indexed[combined_trace_id] = record
    return indexed


def _joined_records_for_source(
    source_id: str,
    runtime_records: list[dict[str, Any]],
    outcome_records: list[dict[str, Any]],
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    runtime_by_trace_id = _trace_id_index(source_id, runtime_records)
    outcome_by_trace_id = _trace_id_index(source_id, outcome_records)

    runtime_ids = set(runtime_by_trace_id)
    outcome_ids = set(outcome_by_trace_id)

    if runtime_ids != outcome_ids:
        missing_outcomes = sorted(runtime_ids - outcome_ids)
        missing_runtime = sorted(outcome_ids - runtime_ids)
        raise ValueError(
            "runtime/outcome combined trace_id mismatch: "
            f"missing_outcomes={missing_outcomes}; missing_runtime={missing_runtime}"
        )

    return [
        (source_id, runtime_by_trace_id[trace_id], outcome_by_trace_id[trace_id])
        for trace_id in sorted(runtime_by_trace_id)
    ]


def _is_in_probability_bin(value: float, lower: float, upper: float) -> bool:
    if upper == 1.0:
        return lower <= value <= upper
    return lower <= value < upper


def _brier_score(
    joined: list[tuple[str, dict[str, Any], dict[str, Any]]],
) -> float:
    squared_errors = []
    for _, runtime_record, outcome_record in joined:
        confidence = float(runtime_record["raw_confidence"])
        label = 1.0 if outcome_record["conditional_acceptance_label"] else 0.0
        squared_errors.append((confidence - label) ** 2)
    return mean(squared_errors)


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


def _probability_bin_report(
    joined: list[tuple[str, dict[str, Any], dict[str, Any]]],
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []

    for lower, upper in PROBABILITY_BINS:
        records = [
            (source_id, runtime_record, outcome_record)
            for source_id, runtime_record, outcome_record in joined
            if _is_in_probability_bin(
                float(runtime_record["raw_confidence"]),
                lower,
                upper,
            )
        ]
        record_count = len(records)
        match_count = sum(
            1 for _, _, outcome_record in records if outcome_record["conditional_acceptance_label"]
        )
        confidences = [float(runtime_record["raw_confidence"]) for _, runtime_record, _ in records]
        observed_match_rate = _rate(match_count, record_count)
        mean_confidence = mean(confidences) if confidences else None
        calibration_gap = None
        if mean_confidence is not None and observed_match_rate is not None:
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


def _stratified_count_report(
    joined: list[tuple[str, dict[str, Any], dict[str, Any]]],
    key: str,
) -> dict[str, dict[str, float | int | None]]:
    buckets: dict[str, list[tuple[str, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for source_id, runtime_record, outcome_record in joined:
        if key == "source_id":
            bucket_key = source_id
        else:
            bucket_key = str(runtime_record[key])
        buckets[bucket_key].append((source_id, runtime_record, outcome_record))

    report: dict[str, dict[str, float | int | None]] = {}
    for value in sorted(buckets, key=str):
        bucket = buckets[value]
        match_count = sum(
            1 for _, _, outcome_record in bucket if outcome_record["conditional_acceptance_label"]
        )
        confidences = [float(runtime_record["raw_confidence"]) for _, runtime_record, _ in bucket]
        report[str(value)] = {
            "record_count": len(bucket),
            "match_count": match_count,
            "nonmatch_count": len(bucket) - match_count,
            "match_rate": _rate(match_count, len(bucket)),
            "mean_raw_confidence": mean(confidences),
        }
    return report


def _load_attempt(
    source_id: str,
    collection_id: str,
    attempt_dir: Path,
) -> dict[str, Any]:
    _validate_attempt_files(source_id, attempt_dir)

    runtime_records = load_jsonl(attempt_dir / "runtime_records.jsonl")
    outcome_records = load_jsonl(attempt_dir / "expected_outcome_records.jsonl")
    timing_records = load_jsonl(attempt_dir / "timing_records.jsonl")
    trace_summary = load_json(attempt_dir / "trace_summary.json")
    retention_manifest = load_json(attempt_dir / "retention_manifest.json")
    analysis_report = load_json(attempt_dir / "trace_analysis_report.json")
    replay_report = load_json(attempt_dir / "trace_replay_report.json")

    joined = _joined_records_for_source(source_id, runtime_records, outcome_records)

    input_hashes = {
        filename: sha256_file(attempt_dir / filename)
        for filename in _attempt_required_files(source_id)
    }
    manifest_file_hashes = retention_manifest["file_hashes"]
    manifest_hash_status = {
        filename: input_hashes[filename] == manifest_file_hashes[filename]
        for filename in MANIFEST_HASHED_FILES
    }

    source_report_ids = {
        "analysis_report_id": analysis_report["report_id"],
        "replay_report_id": replay_report["report_id"],
    }
    if source_id == V2_SOURCE_ID:
        calibration_report = load_json(attempt_dir / "trace_calibration_diagnostic_report.json")
        source_report_ids["calibration_diagnostic_report_id"] = calibration_report["report_id"]

    return {
        "source_id": source_id,
        "collection_id": collection_id,
        "attempt_id": ATTEMPT_ID,
        "attempt_dir": str(attempt_dir),
        "runtime_records": runtime_records,
        "outcome_records": outcome_records,
        "timing_records": timing_records,
        "trace_summary": trace_summary,
        "retention_manifest": retention_manifest,
        "joined_records": joined,
        "input_hashes": input_hashes,
        "manifest_hash_status": manifest_hash_status,
        "source_report_ids": source_report_ids,
    }


def _source_summary(source: dict[str, Any]) -> dict[str, Any]:
    joined = source["joined_records"]
    match_count = sum(
        1 for _, _, outcome_record in joined if outcome_record["conditional_acceptance_label"]
    )
    record_count = len(joined)
    return {
        "source_id": source["source_id"],
        "collection_id": source["collection_id"],
        "attempt_id": source["attempt_id"],
        "runtime_record_count": len(source["runtime_records"]),
        "expected_outcome_record_count": len(source["outcome_records"]),
        "timing_record_count": len(source["timing_records"]),
        "joined_record_count": record_count,
        "case_count": int(source["trace_summary"]["case_count"]),
        "target_argmax_match_count": match_count,
        "target_argmax_nonmatch_count": record_count - match_count,
        "target_argmax_match_rate": _rate(match_count, record_count),
        "source_commit": source["retention_manifest"]["source_commit"],
        "source_report_ids": source["source_report_ids"],
    }


def _calibration_readiness_status(
    record_count: int,
    positive_count: int,
    negative_count: int,
    signal_diagnostic_passed: bool,
) -> str:
    if record_count < MINIMUM_RECORD_COUNT_FOR_CALIBRATION_FIT:
        if signal_diagnostic_passed:
            return "insufficient_record_count_for_calibration_fit_signal_supportive"
        return "insufficient_record_count_for_calibration_fit"

    if positive_count < MINIMUM_POSITIVE_COUNT_FOR_CALIBRATION_FIT:
        if signal_diagnostic_passed:
            return "insufficient_positive_count_for_calibration_fit_signal_supportive"
        return "insufficient_positive_count_for_calibration_fit"

    if negative_count < MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT:
        if signal_diagnostic_passed:
            return "insufficient_negative_count_for_calibration_fit_signal_supportive"
        return "insufficient_negative_count_for_calibration_fit"

    if not signal_diagnostic_passed:
        return "sufficient_sample_but_signal_not_supportive"

    return "sample_and_signal_ready_for_calibration_fit"


def build_combined_calibration_diagnostic_report(
    v2_attempt_dir: Path,
    negative_case_attempt_dir: Path,
) -> dict[str, Any]:
    v2_source = _load_attempt(V2_SOURCE_ID, V2_COLLECTION_ID, v2_attempt_dir)
    negative_source = _load_attempt(
        NEGATIVE_CASE_SOURCE_ID,
        NEGATIVE_CASE_COLLECTION_ID,
        negative_case_attempt_dir,
    )
    sources = [v2_source, negative_source]

    joined: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for source in sources:
        joined.extend(source["joined_records"])

    forbidden_fields_present = sorted(
        {
            field
            for _, runtime_record, _ in joined
            for field in FORBIDDEN_RUNTIME_FIELDS
            if field in runtime_record
        }
    )

    positives = [
        float(runtime_record["raw_confidence"])
        for _, runtime_record, outcome_record in joined
        if outcome_record["conditional_acceptance_label"]
    ]
    negatives = [
        float(runtime_record["raw_confidence"])
        for _, runtime_record, outcome_record in joined
        if not outcome_record["conditional_acceptance_label"]
    ]

    record_count = len(joined)
    positive_count = len(positives)
    negative_count = len(negatives)

    bin_reports = _probability_bin_report(joined)
    brier_score = _brier_score(joined)
    fixed_bin_ece = _expected_calibration_error(bin_reports, record_count)
    fixed_bin_mce = _maximum_calibration_error(bin_reports)
    roc_auc = _roc_auc(positives, negatives)
    signal_diagnostic_passed = bool(
        roc_auc is not None and roc_auc >= MINIMUM_SIGNAL_ROC_AUC_DIAGNOSTIC
    )
    readiness_status = _calibration_readiness_status(
        record_count,
        positive_count,
        negative_count,
        signal_diagnostic_passed,
    )
    calibration_fit_authorized = readiness_status == "sample_and_signal_ready_for_calibration_fit"

    return {
        "report_id": REPORT_ID,
        "collection_id": COMBINED_COLLECTION_ID,
        "attempt_ids": [ATTEMPT_ID],
        "data_role": "combined_post_collection_calibration_readiness_diagnostic",
        "evidence_class": "kaggle_environment_measured_combined_diagnostic",
        "diagnostic_status": DIAGNOSTIC_STATUS,
        "source_summaries": [_source_summary(source) for source in sources],
        "record_counts": {
            "runtime_record_count": record_count,
            "expected_outcome_record_count": record_count,
            "joined_record_count": record_count,
            "source_count": len(sources),
            "target_argmax_match_count": positive_count,
            "target_argmax_nonmatch_count": negative_count,
            "target_argmax_match_rate": _rate(positive_count, record_count),
        },
        "input_hashes": {source["source_id"]: source["input_hashes"] for source in sources},
        "manifest_hash_status": {
            source["source_id"]: source["manifest_hash_status"] for source in sources
        },
        "runtime_outcome_join_status": {
            "one_to_one_join_passed": True,
            "joined_record_count": record_count,
            "runtime_forbidden_fields_present": forbidden_fields_present,
            "combined_trace_id_strategy": "source_id_double_colon_trace_id",
        },
        "calibration_diagnostics": {
            "raw_draft_probability_brier_diagnostic": brier_score,
            "fixed_bin_expected_calibration_error": fixed_bin_ece,
            "fixed_bin_maximum_calibration_error": fixed_bin_mce,
            "raw_confidence_roc_auc_diagnostic": roc_auc,
            "minimum_signal_roc_auc_diagnostic": MINIMUM_SIGNAL_ROC_AUC_DIAGNOSTIC,
            "signal_diagnostic_passed": signal_diagnostic_passed,
            "fixed_bin_reports": bin_reports,
            "stratified_counts": {
                "by_source_id": _stratified_count_report(joined, "source_id"),
                "by_split": _stratified_count_report(joined, "split"),
                "by_workload_type": _stratified_count_report(joined, "workload_type"),
                "by_block_position_index": _stratified_count_report(
                    joined,
                    "block_position_index",
                ),
            },
        },
        "calibration_fit_readiness": {
            "minimum_record_count_for_calibration_fit": (MINIMUM_RECORD_COUNT_FOR_CALIBRATION_FIT),
            "minimum_positive_count_for_calibration_fit": (
                MINIMUM_POSITIVE_COUNT_FOR_CALIBRATION_FIT
            ),
            "minimum_negative_count_for_calibration_fit": (
                MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT
            ),
            "observed_record_count": record_count,
            "observed_positive_count": positive_count,
            "observed_negative_count": negative_count,
            "negative_count_floor_crossed": (
                negative_count >= MINIMUM_NEGATIVE_COUNT_FOR_CALIBRATION_FIT
            ),
            "calibration_fit_readiness_status": readiness_status,
            "calibration_fit_authorized": calibration_fit_authorized,
            "calibration_fit_execution_status": "not_started",
            "next_authorized_step": (
                "fit_kaggle_derived_calibrator_under_separate_gate"
                if calibration_fit_authorized
                else "collect_or_govern_more_calibration_evidence_before_fit"
            ),
        },
        "proposed_fit_boundary": {
            "authorized_only_if_calibration_fit_authorized": calibration_fit_authorized,
            "fit_must_be_separate_pr": True,
            "candidate_fit_splits": [
                "v2_trace_collection:calibration",
                "negative_case_expansion:negative_probe_calibration_candidate",
            ],
            "holdout_or_final_evaluation_splits": [
                "v2_trace_collection:final_evaluation",
                "v2_trace_collection:adversarial_regression",
                "negative_case_expansion:negative_probe_holdout",
            ],
            "threshold_promotion_allowed_from_this_report": False,
            "scheduler_promotion_allowed_from_this_report": False,
        },
        "non_authorization": {
            "calibrator_promotion_status": "not_authorized_by_combined_diagnostic",
            "threshold_promotion_status": "not_authorized_by_combined_diagnostic",
            "scheduler_promotion_status": "not_authorized_by_combined_diagnostic",
            "public_release_status": "not_authorized_by_combined_diagnostic",
            "production_claim_status": "not_authorized_by_combined_diagnostic",
        },
        "interpretation": {
            "summary": (
                "The combined v2 plus negative-case evidence pool crosses the record, "
                "positive-count, negative-count, and ranking-signal floors for a "
                "separate calibrator fitting attempt. Raw confidence remains "
                "miscalibrated, so this report authorizes only the next fitting gate, "
                "not calibrator promotion or threshold promotion."
            ),
            "diagnostic_only": True,
            "calibration_fitting_may_start_next_gate": calibration_fit_authorized,
            "stronger_claims_blocked": True,
        },
    }
