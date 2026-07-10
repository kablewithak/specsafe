from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPORT_ID = "v5-qwen-combined-v2-negative-case-calibrator-fit-v1"
MODEL_ID = "v5-qwen-combined-fixed-bin-isotonic-calibrator-v1"
MODEL_SCHEMA_VERSION = "kaggle_calibrator_model_v1"
FIT_REPORT_SCHEMA_VERSION = "kaggle_calibrator_fit_report_v1"
CALIBRATION_EVIDENCE_ID = "v5-qwen-combined-v2-negative-case"
CALIBRATOR_TYPE = "fixed_bin_laplace_isotonic_v1"
INPUT_FEATURE = "raw_confidence"
OUTPUT_FEATURE = "calibrated_acceptance_probability"
LAPLACE_ALPHA = 1.0
LAPLACE_BETA = 1.0
BIN_EDGES = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.000000001)

V2_ARCHIVE_ID = "v5-qwen-governed-trace-collection-v2/attempt-001-t4"
NEGATIVE_CASE_ARCHIVE_ID = "v5-qwen-negative-case-expansion-v1/attempt-001-t4"

V2_ROOT = Path(
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/attempt-001-t4"
)
NEGATIVE_CASE_ROOT = Path(
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/attempt-001-t4"
)
OUTPUT_DIR = Path("evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case")
DIAGNOSTIC_REPORT_PATH = OUTPUT_DIR / "combined_calibration_diagnostic_report.json"
CALIBRATOR_MODEL_PATH = OUTPUT_DIR / "calibrator_model.json"
CALIBRATOR_FIT_REPORT_PATH = OUTPUT_DIR / "calibrator_fit_report.json"


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


@dataclass(frozen=True)
class BinSummary:
    lower_bound: float
    upper_bound: float
    record_count: int
    match_count: int
    nonmatch_count: int
    mean_raw_confidence: float | None
    empirical_acceptance_rate: float | None
    laplace_acceptance_rate: float | None


@dataclass(frozen=True)
class CalibratorBlock:
    lower_bound: float
    upper_bound: float
    record_count: int
    match_count: int
    nonmatch_count: int
    calibrated_probability: float
    source_bin_indexes: tuple[int, ...]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _load_archive_records(
    *,
    root: Path,
    archive_id: str,
) -> list[JoinedRecord]:
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

    expected_runtime_count = summary["runtime_record_count"]
    if len(runtime_records) != expected_runtime_count:
        raise ValueError(f"runtime count mismatch for {archive_id}")
    if len(outcome_records) != summary["expected_outcome_record_count"]:
        raise ValueError(f"outcome count mismatch for {archive_id}")
    if retention["runtime_record_count"] != expected_runtime_count:
        raise ValueError(f"retention runtime count mismatch for {archive_id}")

    outcomes_by_trace_id = {record["trace_id"]: record for record in outcome_records}
    if set(outcomes_by_trace_id) != {record["trace_id"] for record in runtime_records}:
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


def _bin_index(score: float) -> int:
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score outside [0, 1]: {score}")
    for index in range(len(BIN_EDGES) - 1):
        lower_bound = BIN_EDGES[index]
        upper_bound = BIN_EDGES[index + 1]
        if lower_bound <= score < upper_bound:
            return index
    return len(BIN_EDGES) - 2


def _rate(match_count: int, record_count: int) -> float | None:
    if record_count == 0:
        return None
    return match_count / record_count


def _laplace_rate(match_count: int, record_count: int) -> float | None:
    if record_count == 0:
        return None
    return (match_count + LAPLACE_ALPHA) / (record_count + LAPLACE_ALPHA + LAPLACE_BETA)


def _fixed_bin_summaries(records: list[JoinedRecord]) -> list[BinSummary]:
    bins: list[list[JoinedRecord]] = [[] for _ in range(len(BIN_EDGES) - 1)]
    for record in records:
        bins[_bin_index(record.raw_confidence)].append(record)

    summaries: list[BinSummary] = []
    for index, bin_records in enumerate(bins):
        record_count = len(bin_records)
        match_count = sum(1 for record in bin_records if record.observed_acceptance)
        raw_confidence_sum = sum(record.raw_confidence for record in bin_records)
        mean_raw_confidence = None
        if record_count > 0:
            mean_raw_confidence = raw_confidence_sum / record_count
        summaries.append(
            BinSummary(
                lower_bound=BIN_EDGES[index],
                upper_bound=BIN_EDGES[index + 1],
                record_count=record_count,
                match_count=match_count,
                nonmatch_count=record_count - match_count,
                mean_raw_confidence=mean_raw_confidence,
                empirical_acceptance_rate=_rate(match_count, record_count),
                laplace_acceptance_rate=_laplace_rate(match_count, record_count),
            )
        )
    return summaries


def _fit_isotonic_blocks(bin_summaries: list[BinSummary]) -> list[CalibratorBlock]:
    blocks: list[CalibratorBlock] = []
    for index, bin_summary in enumerate(bin_summaries):
        if bin_summary.record_count == 0:
            continue
        block = CalibratorBlock(
            lower_bound=bin_summary.lower_bound,
            upper_bound=bin_summary.upper_bound,
            record_count=bin_summary.record_count,
            match_count=bin_summary.match_count,
            nonmatch_count=bin_summary.nonmatch_count,
            calibrated_probability=float(bin_summary.laplace_acceptance_rate or 0.0),
            source_bin_indexes=(index,),
        )
        blocks.append(block)
        while len(blocks) >= 2:
            left = blocks[-2]
            right = blocks[-1]
            if left.calibrated_probability <= right.calibrated_probability:
                break
            merged_count = left.record_count + right.record_count
            merged_matches = left.match_count + right.match_count
            merged_probability = float(_laplace_rate(merged_matches, merged_count) or 0.0)
            merged = CalibratorBlock(
                lower_bound=left.lower_bound,
                upper_bound=right.upper_bound,
                record_count=merged_count,
                match_count=merged_matches,
                nonmatch_count=merged_count - merged_matches,
                calibrated_probability=merged_probability,
                source_bin_indexes=left.source_bin_indexes + right.source_bin_indexes,
            )
            blocks = blocks[:-2]
            blocks.append(merged)
    return blocks


def _predict_calibrated_probability(score: float, blocks: list[CalibratorBlock]) -> float:
    if not blocks:
        raise ValueError("no calibrator blocks available")
    for block in blocks:
        if block.lower_bound <= score < block.upper_bound:
            return block.calibrated_probability
    if math.isclose(score, 1.0):
        return blocks[-1].calibrated_probability
    raise ValueError(f"score not covered by calibrator blocks: {score}")


def _brier_score(records: list[JoinedRecord], scores: list[float]) -> float:
    if len(records) != len(scores):
        raise ValueError("record/score length mismatch")
    total = 0.0
    for record, score in zip(records, scores, strict=True):
        label = 1.0 if record.observed_acceptance else 0.0
        total += (score - label) ** 2
    return total / len(records)


def _ece_mce(records: list[JoinedRecord], scores: list[float]) -> tuple[float, float]:
    if len(records) != len(scores):
        raise ValueError("record/score length mismatch")
    total_count = len(records)
    ece = 0.0
    mce = 0.0
    for index in range(len(BIN_EDGES) - 1):
        bin_records: list[tuple[JoinedRecord, float]] = []
        for record, score in zip(records, scores, strict=True):
            if _bin_index(record.raw_confidence) == index:
                bin_records.append((record, score))
        if not bin_records:
            continue
        accuracy = sum(1 for record, _ in bin_records if record.observed_acceptance)
        accuracy_rate = accuracy / len(bin_records)
        mean_score = sum(score for _, score in bin_records) / len(bin_records)
        gap = abs(mean_score - accuracy_rate)
        ece += (len(bin_records) / total_count) * gap
        mce = max(mce, gap)
    return ece, mce


def _bin_summary_to_json(bin_summary: BinSummary) -> dict[str, Any]:
    return {
        "lower_bound": bin_summary.lower_bound,
        "upper_bound": bin_summary.upper_bound,
        "record_count": bin_summary.record_count,
        "match_count": bin_summary.match_count,
        "nonmatch_count": bin_summary.nonmatch_count,
        "mean_raw_confidence": bin_summary.mean_raw_confidence,
        "empirical_acceptance_rate": bin_summary.empirical_acceptance_rate,
        "laplace_acceptance_rate": bin_summary.laplace_acceptance_rate,
    }


def _block_to_json(block: CalibratorBlock) -> dict[str, Any]:
    return {
        "lower_bound": block.lower_bound,
        "upper_bound": block.upper_bound,
        "record_count": block.record_count,
        "match_count": block.match_count,
        "nonmatch_count": block.nonmatch_count,
        "calibrated_probability": block.calibrated_probability,
        "source_bin_indexes": list(block.source_bin_indexes),
    }


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _source_archive_summary(records: list[JoinedRecord]) -> dict[str, Any]:
    return {
        "record_count": len(records),
        "match_count": sum(1 for record in records if record.observed_acceptance),
        "nonmatch_count": sum(1 for record in records if not record.observed_acceptance),
        "split_counts": _counter_to_dict(Counter(record.split for record in records)),
        "workload_counts": _counter_to_dict(Counter(record.workload_type for record in records)),
    }


def build_combined_calibrator_fit(
    *,
    root: Path | str = Path("."),
    write_outputs: bool = True,
) -> dict[str, Any]:
    repo_root = Path(root)
    diagnostic_path = repo_root / DIAGNOSTIC_REPORT_PATH
    _require_file(diagnostic_path)
    diagnostic_report = read_json(diagnostic_path)
    readiness = diagnostic_report.get("calibration_fit_readiness", {})
    if readiness.get("calibration_fit_authorized") is not True:
        raise ValueError("combined diagnostic has not authorized calibration fitting")

    v2_records = _load_archive_records(
        root=repo_root / V2_ROOT,
        archive_id=V2_ARCHIVE_ID,
    )
    negative_case_records = _load_archive_records(
        root=repo_root / NEGATIVE_CASE_ROOT,
        archive_id=NEGATIVE_CASE_ARCHIVE_ID,
    )
    combined_records = v2_records + negative_case_records

    bin_summaries = _fixed_bin_summaries(combined_records)
    calibrator_blocks = _fit_isotonic_blocks(bin_summaries)

    raw_scores = [record.raw_confidence for record in combined_records]
    calibrated_scores = [
        _predict_calibrated_probability(record.raw_confidence, calibrator_blocks)
        for record in combined_records
    ]
    raw_ece, raw_mce = _ece_mce(combined_records, raw_scores)
    calibrated_ece, calibrated_mce = _ece_mce(combined_records, calibrated_scores)
    raw_brier = _brier_score(combined_records, raw_scores)
    calibrated_brier = _brier_score(combined_records, calibrated_scores)

    match_count = sum(1 for record in combined_records if record.observed_acceptance)
    nonmatch_count = len(combined_records) - match_count
    split_counts = Counter(record.split for record in combined_records)
    workload_counts = Counter(record.workload_type for record in combined_records)

    model = {
        "model_schema_version": MODEL_SCHEMA_VERSION,
        "model_id": MODEL_ID,
        "calibration_evidence_id": CALIBRATION_EVIDENCE_ID,
        "calibrator_type": CALIBRATOR_TYPE,
        "input_feature": INPUT_FEATURE,
        "output_feature": OUTPUT_FEATURE,
        "fit_record_count": len(combined_records),
        "fit_positive_count": match_count,
        "fit_negative_count": nonmatch_count,
        "bin_edges": list(BIN_EDGES),
        "laplace_alpha": LAPLACE_ALPHA,
        "laplace_beta": LAPLACE_BETA,
        "calibrator_blocks": [_block_to_json(block) for block in calibrator_blocks],
        "missing_or_out_of_range_input_policy": "fail_closed",
        "calibrator_fit_status": "fit_retained",
        "calibrator_promotion_status": "not_authorized",
        "threshold_promotion_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "public_release_status": "not_authorized",
        "production_claim_status": "not_authorized",
        "source_archives": [V2_ARCHIVE_ID, NEGATIVE_CASE_ARCHIVE_ID],
        "source_diagnostic_report": str(DIAGNOSTIC_REPORT_PATH).replace("\\", "/"),
        "evidence_boundary": (
            "Candidate calibrator fit only; no threshold, scheduler, public, or "
            "production promotion is authorized."
        ),
    }

    model_json = json.dumps(model, indent=2, sort_keys=True) + "\n"
    model_sha256 = hashlib.sha256(model_json.encode("utf-8")).hexdigest()

    report = {
        "fit_report_schema_version": FIT_REPORT_SCHEMA_VERSION,
        "report_id": REPORT_ID,
        "calibration_evidence_id": CALIBRATION_EVIDENCE_ID,
        "source_combined_diagnostic_report": str(DIAGNOSTIC_REPORT_PATH).replace("\\", "/"),
        "source_combined_diagnostic_sha256": sha256_file(diagnostic_path),
        "calibration_fit_authorized_by_combined_diagnostic": True,
        "calibrator_model_id": MODEL_ID,
        "calibrator_model_sha256": model_sha256,
        "calibrator_type": CALIBRATOR_TYPE,
        "fit_record_count": len(combined_records),
        "fit_positive_count": match_count,
        "fit_negative_count": nonmatch_count,
        "source_archive_summaries": {
            V2_ARCHIVE_ID: _source_archive_summary(v2_records),
            NEGATIVE_CASE_ARCHIVE_ID: _source_archive_summary(negative_case_records),
        },
        "split_counts": _counter_to_dict(split_counts),
        "workload_counts": _counter_to_dict(workload_counts),
        "fixed_bin_summaries": [_bin_summary_to_json(bin_summary) for bin_summary in bin_summaries],
        "calibrator_blocks": [_block_to_json(block) for block in calibrator_blocks],
        "raw_brier_diagnostic": raw_brier,
        "calibrated_brier_in_sample_diagnostic": calibrated_brier,
        "raw_fixed_bin_ece_diagnostic": raw_ece,
        "calibrated_fixed_bin_ece_in_sample_diagnostic": calibrated_ece,
        "raw_fixed_bin_mce_diagnostic": raw_mce,
        "calibrated_fixed_bin_mce_in_sample_diagnostic": calibrated_mce,
        "in_sample_brier_delta": raw_brier - calibrated_brier,
        "in_sample_ece_delta": raw_ece - calibrated_ece,
        "calibrator_fit_status": "fit_retained",
        "calibrator_promotion_status": "not_authorized",
        "threshold_promotion_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "public_release_status": "not_authorized",
        "production_claim_status": "not_authorized",
        "next_authorized_step": "holdout_or_replay_diagnostic_for_candidate_calibrator",
        "non_claims": [
            "does_not_promote_calibrator",
            "does_not_tune_or_promote_thresholds",
            "does_not_promote_scheduler_utility",
            "does_not_publish_public_artifacts",
            "does_not_claim_production_speedup_or_readiness",
        ],
    }

    if write_outputs:
        write_json(repo_root / CALIBRATOR_MODEL_PATH, model)
        write_json(repo_root / CALIBRATOR_FIT_REPORT_PATH, report)

    return {"calibrator_model": model, "calibrator_fit_report": report}


if __name__ == "__main__":
    build_combined_calibrator_fit()
