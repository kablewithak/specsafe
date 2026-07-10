from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPORT_ID = "v5-qwen-combined-v2-negative-case-calibrator-replay-v1"
REPLAY_REPORT_SCHEMA_VERSION = "kaggle_calibrator_replay_report_v1"
CALIBRATION_EVIDENCE_ID = "v5-qwen-combined-v2-negative-case"
MODEL_ID = "v5-qwen-combined-fixed-bin-isotonic-calibrator-v1"

V2_ARCHIVE_ID = "v5-qwen-governed-trace-collection-v2/attempt-001-t4"
NEGATIVE_CASE_ARCHIVE_ID = "v5-qwen-negative-case-expansion-v1/attempt-001-t4"

V2_ROOT = Path(
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/attempt-001-t4"
)
NEGATIVE_CASE_ROOT = Path(
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/attempt-001-t4"
)
OUTPUT_DIR = Path("evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case")
CALIBRATOR_MODEL_PATH = OUTPUT_DIR / "calibrator_model.json"
CALIBRATOR_FIT_REPORT_PATH = OUTPUT_DIR / "calibrator_fit_report.json"
CALIBRATOR_REPLAY_REPORT_PATH = OUTPUT_DIR / "calibrator_replay_report.json"

CALIBRATED_THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)


@dataclass(frozen=True)
class JoinedRecord:
    source_archive_id: str
    trace_id: str
    source_trace_id: str
    case_id: str
    split: str
    workload_type: str
    raw_confidence: float
    draft_entropy: float
    observed_acceptance: bool


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def _load_archive_records(*, root: Path, archive_id: str) -> list[JoinedRecord]:
    runtime_path = root / "runtime_records.jsonl"
    outcome_path = root / "expected_outcome_records.jsonl"
    summary_path = root / "trace_summary.json"
    retention_path = root / "retention_manifest.json"

    for path in [runtime_path, outcome_path, summary_path, retention_path]:
        _require_file(path)

    runtime_records = read_jsonl(runtime_path)
    outcome_records = read_jsonl(outcome_path)
    summary = read_json(summary_path)
    retention = read_json(retention_path)

    if len(runtime_records) != summary["runtime_record_count"]:
        raise ValueError(f"runtime count mismatch for {archive_id}")
    if len(outcome_records) != summary["expected_outcome_record_count"]:
        raise ValueError(f"outcome count mismatch for {archive_id}")
    if retention["runtime_record_count"] != summary["runtime_record_count"]:
        raise ValueError(f"retention count mismatch for {archive_id}")

    outcomes_by_trace_id = {record["trace_id"]: record for record in outcome_records}
    runtime_trace_ids = {record["trace_id"] for record in runtime_records}
    if set(outcomes_by_trace_id) != runtime_trace_ids:
        raise ValueError(f"runtime/outcome trace join mismatch for {archive_id}")

    joined_records: list[JoinedRecord] = []
    for runtime_record in runtime_records:
        source_trace_id = str(runtime_record["trace_id"])
        outcome_record = outcomes_by_trace_id[source_trace_id]
        joined_records.append(
            JoinedRecord(
                source_archive_id=archive_id,
                trace_id=f"{archive_id}:{source_trace_id}",
                source_trace_id=source_trace_id,
                case_id=str(runtime_record["case_id"]),
                split=str(runtime_record["split"]),
                workload_type=str(runtime_record["workload_type"]),
                raw_confidence=float(runtime_record["raw_confidence"]),
                draft_entropy=float(runtime_record["draft_entropy"]),
                observed_acceptance=bool(outcome_record["observed_acceptance"]),
            )
        )
    return joined_records


def _load_combined_records(root: Path) -> list[JoinedRecord]:
    v2_records = _load_archive_records(root=root / V2_ROOT, archive_id=V2_ARCHIVE_ID)
    negative_case_records = _load_archive_records(
        root=root / NEGATIVE_CASE_ROOT,
        archive_id=NEGATIVE_CASE_ARCHIVE_ID,
    )
    return v2_records + negative_case_records


def _label(record: JoinedRecord) -> float:
    return 1.0 if record.observed_acceptance else 0.0


def _brier(records: list[JoinedRecord], scores: list[float]) -> float:
    if len(records) != len(scores):
        raise ValueError("record/score length mismatch")
    return sum((score - _label(record)) ** 2 for record, score in zip(records, scores)) / len(
        records
    )


def _predict_calibrated_probability(score: float, model: dict[str, Any]) -> float:
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score outside [0, 1]: {score}")
    for block in model["calibrator_blocks"]:
        lower_bound = float(block["lower_bound"])
        upper_bound = float(block["upper_bound"])
        if lower_bound <= score < upper_bound:
            return float(block["calibrated_probability"])
    if score == 1.0:
        return float(model["calibrator_blocks"][-1]["calibrated_probability"])
    raise ValueError(f"score not covered by calibrator model: {score}")


def _rate(match_count: int, record_count: int) -> float | None:
    if record_count == 0:
        return None
    return match_count / record_count


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _calibrated_block_replay(
    *,
    records: list[JoinedRecord],
    calibrated_scores: list[float],
    model: dict[str, Any],
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for block in model["calibrator_blocks"]:
        lower_bound = float(block["lower_bound"])
        upper_bound = float(block["upper_bound"])
        selected = [
            record for record in records if lower_bound <= record.raw_confidence < upper_bound
        ]
        calibrated_probability = float(block["calibrated_probability"])
        match_count = sum(1 for record in selected if record.observed_acceptance)
        record_count = len(selected)
        empirical_acceptance_rate = _rate(match_count, record_count)
        calibration_gap = None
        if empirical_acceptance_rate is not None:
            calibration_gap = abs(calibrated_probability - empirical_acceptance_rate)
        reports.append(
            {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "calibrated_probability": calibrated_probability,
                "record_count": record_count,
                "match_count": match_count,
                "nonmatch_count": record_count - match_count,
                "empirical_acceptance_rate": empirical_acceptance_rate,
                "absolute_calibration_gap": calibration_gap,
                "source_bin_indexes": block["source_bin_indexes"],
            }
        )
    if len(calibrated_scores) != len(records):
        raise ValueError("calibrated score length mismatch")
    return reports


def _threshold_report(
    *,
    records: list[JoinedRecord],
    calibrated_scores: list[float],
    threshold: float,
) -> dict[str, Any]:
    selected = [
        record
        for record, score in zip(records, calibrated_scores, strict=True)
        if score >= threshold
    ]
    selected_count = len(selected)
    selected_match_count = sum(1 for record in selected if record.observed_acceptance)
    selected_nonmatch_count = selected_count - selected_match_count
    return {
        "threshold": threshold,
        "selected_count": selected_count,
        "selected_match_count": selected_match_count,
        "selected_nonmatch_count": selected_nonmatch_count,
        "selected_acceptance_rate": _rate(selected_match_count, selected_count),
        "coverage_rate": selected_count / len(records),
    }


def _source_replay_summary(
    *,
    records: list[JoinedRecord],
    raw_scores: list[float],
    calibrated_scores: list[float],
) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for source_archive_id in sorted({record.source_archive_id for record in records}):
        source_indexes = [
            index
            for index, record in enumerate(records)
            if record.source_archive_id == source_archive_id
        ]
        source_records = [records[index] for index in source_indexes]
        source_raw_scores = [raw_scores[index] for index in source_indexes]
        source_calibrated_scores = [calibrated_scores[index] for index in source_indexes]
        raw_brier = _brier(source_records, source_raw_scores)
        calibrated_brier = _brier(source_records, source_calibrated_scores)
        match_count = sum(1 for record in source_records if record.observed_acceptance)
        summaries[source_archive_id] = {
            "record_count": len(source_records),
            "match_count": match_count,
            "nonmatch_count": len(source_records) - match_count,
            "raw_brier_diagnostic": raw_brier,
            "calibrated_brier_fit_pool_replay_diagnostic": calibrated_brier,
            "fit_pool_brier_delta": raw_brier - calibrated_brier,
            "split_counts": _counter_to_dict(Counter(record.split for record in source_records)),
            "workload_counts": _counter_to_dict(
                Counter(record.workload_type for record in source_records)
            ),
        }
    return summaries


def build_combined_calibrator_replay(
    *,
    root: Path | str = Path("."),
    write_outputs: bool = True,
) -> dict[str, Any]:
    repo_root = Path(root)
    model_path = repo_root / CALIBRATOR_MODEL_PATH
    fit_report_path = repo_root / CALIBRATOR_FIT_REPORT_PATH
    _require_file(model_path)
    _require_file(fit_report_path)

    model = read_json(model_path)
    fit_report = read_json(fit_report_path)
    if model.get("model_id") != MODEL_ID:
        raise ValueError("unexpected calibrator model id")
    if fit_report.get("calibrator_promotion_status") != "not_authorized":
        raise ValueError("replay expects an unpromoted candidate calibrator")
    if fit_report.get("calibrator_model_sha256") != sha256_json(model):
        raise ValueError("calibrator model hash mismatch")

    records = _load_combined_records(repo_root)
    raw_scores = [record.raw_confidence for record in records]
    calibrated_scores = [
        _predict_calibrated_probability(record.raw_confidence, model) for record in records
    ]

    match_count = sum(1 for record in records if record.observed_acceptance)
    raw_brier = _brier(records, raw_scores)
    calibrated_brier = _brier(records, calibrated_scores)
    threshold_reports = [
        _threshold_report(
            records=records,
            calibrated_scores=calibrated_scores,
            threshold=threshold,
        )
        for threshold in CALIBRATED_THRESHOLDS
    ]

    replay_report = {
        "replay_report_schema_version": REPLAY_REPORT_SCHEMA_VERSION,
        "report_id": REPORT_ID,
        "calibration_evidence_id": CALIBRATION_EVIDENCE_ID,
        "calibrator_model_id": MODEL_ID,
        "calibrator_model_sha256": sha256_json(model),
        "source_calibrator_model": str(CALIBRATOR_MODEL_PATH).replace("\\", "/"),
        "source_calibrator_fit_report": str(CALIBRATOR_FIT_REPORT_PATH).replace("\\", "/"),
        "source_calibrator_fit_report_sha256": sha256_file(fit_report_path),
        "fit_pool_replay_record_count": len(records),
        "fit_pool_replay_positive_count": match_count,
        "fit_pool_replay_negative_count": len(records) - match_count,
        "raw_brier_diagnostic": raw_brier,
        "calibrated_brier_fit_pool_replay_diagnostic": calibrated_brier,
        "fit_pool_brier_delta": raw_brier - calibrated_brier,
        "source_archive_replay_summaries": _source_replay_summary(
            records=records,
            raw_scores=raw_scores,
            calibrated_scores=calibrated_scores,
        ),
        "calibrated_block_replay": _calibrated_block_replay(
            records=records,
            calibrated_scores=calibrated_scores,
            model=model,
        ),
        "calibrated_threshold_replay": threshold_reports,
        "split_counts": _counter_to_dict(Counter(record.split for record in records)),
        "workload_counts": _counter_to_dict(Counter(record.workload_type for record in records)),
        "holdout_status": "not_available_fit_pool_replay_only",
        "calibrator_replay_status": "fit_pool_replay_passed",
        "calibrator_promotion_status": "not_authorized_no_holdout",
        "threshold_promotion_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "public_release_status": "not_authorized",
        "production_claim_status": "not_authorized",
        "next_authorized_step": "holdout_or_promotion_governance_decision",
        "non_claims": [
            "does_not_promote_calibrator",
            "does_not_tune_or_promote_thresholds",
            "does_not_promote_scheduler_utility",
            "does_not_publish_public_artifacts",
            "does_not_claim_production_speedup_or_readiness",
        ],
    }

    if write_outputs:
        write_json(repo_root / CALIBRATOR_REPLAY_REPORT_PATH, replay_report)

    return replay_report


if __name__ == "__main__":
    build_combined_calibrator_replay()
