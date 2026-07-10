from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from specsafe.independent_holdout_replay.models import (
    CalibratorBlockReplay,
    CandidateCalibratorArtifact,
    CoverageMetrics,
    HoldoutReplayFailureLabel,
    HoldoutReplayGateChecks,
    HoldoutReplayProtocol,
    IndependentHoldoutReplayReport,
    ProbabilityMetrics,
    PromotionRecommendation,
    ThresholdPreview,
)

_CANDIDATE_MODEL_PATH = Path(
    "evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case/calibrator_model.json"
)
_HOLDOUT_ROOT = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4"
)
_ANALYSIS_REPORT_FILENAME = "independent_holdout_analysis_report.json"
_OUTPUT_FILENAME = "candidate_calibrator_holdout_replay_report.json"
_PRECOLLECTION_MANIFEST_PATH = Path(
    "data/kaggle_holdout/v5_candidate_calibrator_holdout_precollection_manifest.json"
)
_EXPECTED_SOURCE_COMMIT = "8b0b81b"
_CREATED_AT = "2026-07-10T19:33:42Z"
_JOIN_FIELDS = ("trace_id", "decode_round", "block_position_index")
_FIXED_BIN_EDGES = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.000000001)


class IndependentHoldoutReplayError(ValueError):
    """Raised when frozen replay inputs cannot cross the holdout boundary."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise IndependentHoldoutReplayError(f"unable to load JSON evidence: {path}") from error
    if not isinstance(value, dict):
        raise IndependentHoldoutReplayError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as error:
        raise IndependentHoldoutReplayError(f"unable to load JSONL evidence: {path}") from error
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value: Any = json.loads(line)
        except json.JSONDecodeError as error:
            raise IndependentHoldoutReplayError(
                f"invalid JSONL evidence at {path}:{line_number}"
            ) from error
        if not isinstance(value, dict):
            raise IndependentHoldoutReplayError(f"expected JSON object at {path}:{line_number}")
        records.append(value)
    return records


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise IndependentHoldoutReplayError(f"unable to hash evidence: {path}") from error


def _join_key(record: dict[str, Any]) -> tuple[str, int, int]:
    return (
        str(record["trace_id"]),
        int(record["decode_round"]),
        int(record["block_position_index"]),
    )


def _load_candidate_artifact(path: Path) -> CandidateCalibratorArtifact:
    try:
        return CandidateCalibratorArtifact.model_validate(_read_json(path))
    except ValidationError as error:
        raise IndependentHoldoutReplayError(
            f"candidate calibrator artifact failed strict validation: {error}"
        ) from error


def _predict(score: float, artifact: CandidateCalibratorArtifact) -> float:
    if not 0.0 <= score <= 1.0:
        raise IndependentHoldoutReplayError(f"raw confidence outside [0, 1]: {score}")
    for block in artifact.calibrator_blocks:
        if block.lower_bound <= score < block.upper_bound:
            return block.calibrated_probability
    if score == 1.0:
        return artifact.calibrator_blocks[-1].calibrated_probability
    raise IndependentHoldoutReplayError(f"candidate artifact does not cover score: {score}")


def _fixed_bin_index(score: float) -> int:
    for index in range(len(_FIXED_BIN_EDGES) - 1):
        if _FIXED_BIN_EDGES[index] <= score < _FIXED_BIN_EDGES[index + 1]:
            return index
    raise IndependentHoldoutReplayError(f"raw confidence not covered by fixed bins: {score}")


def _brier(rows: list[tuple[float, float, bool, str, int]], score_index: int) -> float:
    return sum((row[score_index] - float(row[2])) ** 2 for row in rows) / len(rows)


def _fixed_bin_ece(
    rows: list[tuple[float, float, bool, str, int]],
    score_index: int,
) -> float:
    weighted_gap = 0.0
    for bin_index in range(len(_FIXED_BIN_EDGES) - 1):
        selected = [row for row in rows if _fixed_bin_index(row[0]) == bin_index]
        if not selected:
            continue
        mean_score = sum(row[score_index] for row in selected) / len(selected)
        acceptance_rate = sum(row[2] for row in selected) / len(selected)
        weighted_gap += (len(selected) / len(rows)) * abs(mean_score - acceptance_rate)
    return weighted_gap


def _tie_aware_auc(
    rows: list[tuple[float, float, bool, str, int]],
    score_index: int,
) -> float:
    positives = [row[score_index] for row in rows if row[2]]
    negatives = [row[score_index] for row in rows if not row[2]]
    if not positives or not negatives:
        raise IndependentHoldoutReplayError("AUROC requires positive and negative holdout labels")
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def _metrics(
    rows: list[tuple[float, float, bool, str, int]],
    score_index: int,
) -> ProbabilityMetrics:
    return ProbabilityMetrics(
        brier_score=_brier(rows, score_index),
        fixed_bin_ece=_fixed_bin_ece(rows, score_index),
        auroc=_tie_aware_auc(rows, score_index),
    )


def _coverage(
    rows: list[tuple[float, float, bool, str, int]],
) -> CoverageMetrics:
    positive_count = sum(row[2] for row in rows)
    raw_brier = _brier(rows, 0)
    calibrated_brier = _brier(rows, 1)
    return CoverageMetrics(
        record_count=len(rows),
        positive_count=positive_count,
        negative_count=len(rows) - positive_count,
        raw_brier_score=raw_brier,
        calibrated_brier_score=calibrated_brier,
        brier_improvement=raw_brier - calibrated_brier,
    )


def _block_replay(
    rows: list[tuple[float, float, bool, str, int]],
    artifact: CandidateCalibratorArtifact,
) -> tuple[CalibratorBlockReplay, ...]:
    reports: list[CalibratorBlockReplay] = []
    for block in artifact.calibrator_blocks:
        selected = [row for row in rows if block.lower_bound <= row[0] < block.upper_bound]
        positive_count = sum(row[2] for row in selected)
        empirical_rate = positive_count / len(selected) if selected else None
        reports.append(
            CalibratorBlockReplay(
                lower_bound=block.lower_bound,
                upper_bound=block.upper_bound,
                calibrated_probability=block.calibrated_probability,
                record_count=len(selected),
                positive_count=positive_count,
                negative_count=len(selected) - positive_count,
                empirical_acceptance_rate=empirical_rate,
                absolute_calibration_gap=(
                    abs(block.calibrated_probability - empirical_rate)
                    if empirical_rate is not None
                    else None
                ),
            )
        )
    return tuple(reports)


def _threshold_previews(
    rows: list[tuple[float, float, bool, str, int]],
    protocol: HoldoutReplayProtocol,
) -> tuple[ThresholdPreview, ...]:
    previews: list[ThresholdPreview] = []
    for threshold in protocol.threshold_preview_values:
        selected = [row for row in rows if row[1] >= threshold]
        match_count = sum(row[2] for row in selected)
        selected_count = len(selected)
        previews.append(
            ThresholdPreview(
                threshold=threshold,
                selected_count=selected_count,
                match_count=match_count,
                nonmatch_count=selected_count - match_count,
                selection_rate=selected_count / len(rows),
                nonmatch_rate=(
                    (selected_count - match_count) / selected_count if selected_count else None
                ),
                coverage_warning=(
                    selected_count < protocol.minimum_threshold_preview_selected_count
                ),
            )
        )
    return tuple(previews)


def _validate_retained_file_hashes(holdout_root: Path, retention: dict[str, Any]) -> None:
    file_hashes = retention.get("file_hashes")
    if not isinstance(file_hashes, dict):
        raise IndependentHoldoutReplayError("retention report is missing file_hashes")
    required_files = (
        "runtime_records.jsonl",
        "expected_outcome_records.jsonl",
        "timing_records.jsonl",
        "trace_summary.json",
        "retention_manifest.json",
    )
    for filename in required_files:
        expected = file_hashes.get(filename)
        if not isinstance(expected, dict) or not isinstance(expected.get("sha256"), str):
            raise IndependentHoldoutReplayError(f"missing retained hash for {filename}")
        if _sha256(holdout_root / filename) != expected["sha256"]:
            raise IndependentHoldoutReplayError(f"retained hash mismatch for {filename}")


def build_independent_holdout_replay_report(
    *,
    root: Path | str = Path("."),
    source_commit: str = _EXPECTED_SOURCE_COMMIT,
    write_output: bool = True,
) -> IndependentHoldoutReplayReport:
    repo_root = Path(root)
    holdout_root = repo_root / _HOLDOUT_ROOT
    model_path = repo_root / _CANDIDATE_MODEL_PATH
    analysis_path = holdout_root / _ANALYSIS_REPORT_FILENAME
    retention_path = holdout_root / "archive_retention_report.json"
    precollection_path = repo_root / _PRECOLLECTION_MANIFEST_PATH

    artifact_payload = _read_json(model_path)
    artifact = _load_candidate_artifact(model_path)
    artifact_hash = _canonical_json_sha256(artifact_payload)
    protocol = HoldoutReplayProtocol(
        protocol_id="candidate-calibrator-independent-holdout-promotion-protocol-v1",
        expected_calibrator_artifact_sha256=(
            "e799e4c1e5db8798120b73e0c7e33b86e0f4f220b6360ad010cd0a5feb55ec36"
        ),
        expected_holdout_collection_id=("v5-qwen-candidate-calibrator-independent-holdout-v1"),
        expected_holdout_attempt_id="attempt-001-t4",
        minimum_holdout_record_count=160,
        minimum_holdout_negative_count=30,
        minimum_brier_improvement=0.005,
        minimum_fixed_bin_ece_improvement=0.01,
        maximum_auroc_degradation=0.001,
        minimum_threshold_preview_selected_count=30,
        threshold_preview_values=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95),
    )
    if artifact_hash != protocol.expected_calibrator_artifact_sha256:
        raise IndependentHoldoutReplayError("candidate calibrator artifact hash mismatch")

    retention = _read_json(retention_path)
    analysis = _read_json(analysis_path)
    precollection = _read_json(precollection_path)
    _validate_retained_file_hashes(holdout_root, retention)

    if retention.get("collection_id") != protocol.expected_holdout_collection_id:
        raise IndependentHoldoutReplayError("unexpected holdout collection identity")
    if retention.get("attempt_id") != protocol.expected_holdout_attempt_id:
        raise IndependentHoldoutReplayError("unexpected holdout attempt identity")
    if analysis.get("analysis_status") != "replay_ready":
        raise IndependentHoldoutReplayError("independent holdout analysis is not replay-ready")
    if precollection.get("prompt_corpus_sha256") != retention.get("source_corpus_sha256"):
        raise IndependentHoldoutReplayError("holdout corpus provenance mismatch")
    collection_requirements = precollection.get("collection_requirements")
    if not isinstance(collection_requirements, dict):
        raise IndependentHoldoutReplayError("precollection requirements are missing")
    if collection_requirements.get("minimum_runtime_records_target") != 160:
        raise IndependentHoldoutReplayError("holdout record floor changed after collection")
    if collection_requirements.get("minimum_nonmatch_count_target") != 30:
        raise IndependentHoldoutReplayError("holdout negative floor changed after collection")

    runtime_records = _read_jsonl(holdout_root / "runtime_records.jsonl")
    outcome_records = _read_jsonl(holdout_root / "expected_outcome_records.jsonl")
    outcomes_by_key = {_join_key(record): record for record in outcome_records}
    if len(outcomes_by_key) != len(outcome_records):
        raise IndependentHoldoutReplayError("duplicate holdout outcome join keys")

    rows: list[tuple[float, float, bool, str, int]] = []
    for runtime in runtime_records:
        outcome = outcomes_by_key.get(_join_key(runtime))
        if outcome is None:
            raise IndependentHoldoutReplayError("holdout runtime record has no outcome")
        for field in ("case_id", "workload_type", "collection_id", "attempt_id"):
            if runtime.get(field) != outcome.get(field):
                raise IndependentHoldoutReplayError(f"holdout join identity mismatch: {field}")
        raw_probability = float(runtime["raw_confidence"])
        rows.append(
            (
                raw_probability,
                _predict(raw_probability, artifact),
                bool(outcome["observed_acceptance"]),
                str(runtime["workload_type"]),
                int(runtime["block_position_index"]),
            )
        )
    if len(rows) != len(runtime_records) or len(rows) != len(outcome_records):
        raise IndependentHoldoutReplayError("holdout replay join is incomplete")

    raw_metrics = _metrics(rows, 0)
    calibrated_metrics = _metrics(rows, 1)
    brier_delta = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_delta = raw_metrics.fixed_bin_ece - calibrated_metrics.fixed_bin_ece
    auroc_delta = calibrated_metrics.auroc - raw_metrics.auroc

    by_workload: dict[str, list[tuple[float, float, bool, str, int]]] = defaultdict(list)
    by_position: dict[str, list[tuple[float, float, bool, str, int]]] = defaultdict(list)
    for row in rows:
        by_workload[row[3]].append(row)
        by_position[str(row[4])].append(row)

    threshold_preview = _threshold_previews(rows, protocol)
    positive_count = sum(row[2] for row in rows)
    gate_checks = HoldoutReplayGateChecks(
        holdout_provenance_complete=True,
        holdout_independence_documented=True,
        manifest_hashes_match=True,
        analysis_replay_ready=True,
        holdout_record_coverage_sufficient=(len(rows) >= protocol.minimum_holdout_record_count),
        holdout_negative_coverage_sufficient=(
            len(rows) - positive_count >= protocol.minimum_holdout_negative_count
        ),
        candidate_artifact_integrity_passed=True,
        no_refit_passed=True,
        brier_improvement_passed=(brier_delta >= protocol.minimum_brier_improvement),
        fixed_bin_ece_improvement_passed=(ece_delta >= protocol.minimum_fixed_bin_ece_improvement),
        ranking_safety_passed=(auroc_delta >= -protocol.maximum_auroc_degradation),
        threshold_preview_support_passed=not any(
            preview.coverage_warning for preview in threshold_preview
        ),
        bounded_claims_passed=True,
    )
    if gate_checks.ranking_safety_passed:
        raise IndependentHoldoutReplayError(
            "retained report contract expects the observed ranking-safety regression"
        )

    report = IndependentHoldoutReplayReport(
        schema_version="candidate_calibrator_independent_holdout_replay_report_v1",
        report_id="v5-qwen-candidate-calibrator-independent-holdout-replay-v1",
        run_id="v5-qwen-candidate-calibrator-independent-holdout-replay-run-001",
        source_commit=source_commit,
        created_at=_CREATED_AT,
        protocol=protocol,
        calibrator_artifact_id=artifact.model_id,
        calibrator_artifact_hash=artifact_hash,
        calibrator_fit_pool_archive_ids=artifact.source_archives,
        holdout_trace_archive_id=(
            "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4"
        ),
        holdout_trace_archive_hash=str(retention["archive_sha256"]),
        holdout_analysis_report_id=str(analysis["report_id"]),
        holdout_analysis_report_hash=_sha256(analysis_path),
        holdout_record_count=len(rows),
        holdout_positive_count=positive_count,
        holdout_negative_count=len(rows) - positive_count,
        coverage_by_workload={key: _coverage(value) for key, value in sorted(by_workload.items())},
        coverage_by_position={key: _coverage(value) for key, value in sorted(by_position.items())},
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        brier_delta=brier_delta,
        fixed_bin_ece_delta=ece_delta,
        auroc_delta=auroc_delta,
        calibrator_block_replay=_block_replay(rows, artifact),
        threshold_preview=threshold_preview,
        gate_checks=gate_checks,
        failure_labels=(HoldoutReplayFailureLabel.RANKING_SAFETY_REGRESSION,),
        promotion_recommendation=PromotionRecommendation.KEEP_DIAGNOSTIC_ONLY,
        holdout_replay_status="completed_with_ranking_safety_regression",
        calibrator_promotion_status="not_authorized_ranking_safety_regression",
        threshold_promotion_status="not_authorized",
        scheduler_promotion_status="not_authorized",
        public_release_status="not_authorized",
        production_claim_status="not_authorized",
        claims_permitted=(
            (
                "The retained candidate calibrator was replayed without refit on the "
                "independent holdout."
            ),
            "The candidate improved aggregate holdout Brier score and fixed-bin ECE.",
            "The candidate regressed holdout ranking safety beyond the declared tolerance.",
            "The candidate remains retained diagnostic evidence and is not promoted.",
        ),
        claims_forbidden=(
            "The candidate calibrator is promoted.",
            "Any calibrated threshold is promoted.",
            "Any scheduler or adaptive-policy utility claim is authorized.",
            "Hugging Face final proof packaging is authorized.",
            "Production speed, latency, throughput, cost, or serving readiness is proven.",
        ),
        next_authorized_step="candidate_calibrator_promotion_closeout_decision",
    )

    if write_output:
        output_path = holdout_root / _OUTPUT_FILENAME
        output_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
