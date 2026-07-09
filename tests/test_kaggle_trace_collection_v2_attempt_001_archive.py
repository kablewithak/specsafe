from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

ATTEMPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
ARCHIVE_PATH = ATTEMPT_DIR / "specsafe_v5_qwen_trace_collection_v2_attempt_001_t4.zip"
EXPECTED_ARCHIVE_SHA256 = "b8803ea500378a6b91af6b0a5206fc4359d9b3f8bf1888a01907ded6f11e0e7a"
EXPECTED_COLLECTION_ID = "v5-qwen-governed-trace-collection-v2"
EXPECTED_ATTEMPT_ID = "attempt-001-t4"
EXPECTED_REQUIRED_FILES = {
    "environment_report.json",
    "expected_outcome_records.jsonl",
    "retention_manifest.json",
    "runtime_records.jsonl",
    "timing_records.jsonl",
    "trace_summary.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_retained_archive_exists_and_hash_matches() -> None:
    assert ARCHIVE_PATH.exists()
    assert _sha256(ARCHIVE_PATH) == EXPECTED_ARCHIVE_SHA256


def test_retained_archive_contains_only_attempt_files() -> None:
    expected_prefix = (
        "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/attempt-001-t4/"
    )

    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        names = set(archive.namelist())

    assert all(name.startswith(expected_prefix) for name in names)
    assert {name.removeprefix(expected_prefix) for name in names} == EXPECTED_REQUIRED_FILES


def test_extracted_attempt_files_are_present() -> None:
    present = {path.name for path in ATTEMPT_DIR.iterdir() if path.is_file()}

    assert EXPECTED_REQUIRED_FILES.issubset(present)
    assert ARCHIVE_PATH.name in present


def test_manifest_hashes_match_extracted_files() -> None:
    manifest = _load_json(ATTEMPT_DIR / "retention_manifest.json")

    assert manifest["collection_id"] == EXPECTED_COLLECTION_ID
    assert manifest["attempt_id"] == EXPECTED_ATTEMPT_ID

    for filename, expected_hash in manifest["file_hashes"].items():
        assert _sha256(ATTEMPT_DIR / filename) == expected_hash


def test_summary_counts_and_boundaries_match_collection_output() -> None:
    summary = _load_json(ATTEMPT_DIR / "trace_summary.json")
    manifest = _load_json(ATTEMPT_DIR / "retention_manifest.json")
    environment = _load_json(ATTEMPT_DIR / "environment_report.json")

    assert summary["collection_id"] == EXPECTED_COLLECTION_ID
    assert summary["attempt_id"] == EXPECTED_ATTEMPT_ID
    assert summary["runtime_record_count"] == 120
    assert summary["expected_outcome_record_count"] == 120
    assert summary["case_count"] == 30
    assert summary["target_argmax_match_count"] == 97
    assert summary["target_argmax_nonmatch_count"] == 23
    assert summary["target_argmax_match_rate"] == 97 / 120
    assert summary["calibration_fit_status"] == "not_authorized"
    assert summary["threshold_promotion_status"] == "not_authorized"
    assert summary["scheduler_promotion_status"] == "not_authorized"
    assert summary["production_claim_status"] == "not_authorized"
    assert summary["raw_prompt_text_retained"] is False

    assert manifest["runtime_record_count"] == summary["runtime_record_count"]
    assert manifest["expected_outcome_record_count"] == summary["expected_outcome_record_count"]
    assert manifest["case_count"] == summary["case_count"]
    assert manifest["calibration_fit_status"] == "not_authorized"
    assert manifest["threshold_promotion_status"] == "not_authorized"
    assert manifest["raw_prompt_text_retained"] is False

    assert environment["cuda_available"] is True
    assert environment["cuda_devices"] == ["Tesla T4", "Tesla T4"]
    assert environment["draft_model_id"] == "Qwen/Qwen2.5-0.5B"
    assert environment["target_model_id"] == "Qwen/Qwen2.5-1.5B"
    assert environment["secrets_printed"] is False


def test_runtime_and_outcome_records_join_one_to_one_without_runtime_labels() -> None:
    runtime_records = _load_jsonl(ATTEMPT_DIR / "runtime_records.jsonl")
    outcome_records = _load_jsonl(ATTEMPT_DIR / "expected_outcome_records.jsonl")

    assert len(runtime_records) == 120
    assert len(outcome_records) == 120

    runtime_trace_ids = {record["trace_id"] for record in runtime_records}
    outcome_trace_ids = {record["trace_id"] for record in outcome_records}

    assert runtime_trace_ids == outcome_trace_ids

    forbidden_runtime_fields = {
        "target_argmax_token_id",
        "target_probability",
        "target_candidate_probability",
        "conditional_acceptance_label",
        "observed_acceptance",
        "prefix_survival_label",
    }

    for record in runtime_records:
        assert record["record_type"] == "runtime"
        assert record["raw_confidence"] == record["draft_probability"]
        assert record["runtime_metadata"]["raw_prompt_text_retained"] is False
        assert not forbidden_runtime_fields.intersection(record)

    for record in outcome_records:
        assert record["record_type"] == "expected_outcome"
        assert record["outcome_metadata"]["label_available_to_runtime_policy"] is False
        assert record["outcome_metadata"]["calibration_fit_allowed"] is False
        assert record["outcome_metadata"]["threshold_tuning_allowed"] is False


def test_split_and_workload_counts_are_balanced_as_planned() -> None:
    summary = _load_json(ATTEMPT_DIR / "trace_summary.json")

    assert summary["split_record_counts"] == {
        "adversarial_regression": 12,
        "calibration": 36,
        "development": 36,
        "final_evaluation": 36,
    }
    assert summary["workload_record_counts"] == {
        "code": 40,
        "open_ended_chat": 40,
        "structured_text": 40,
    }


def test_retention_note_preserves_non_claim_boundary() -> None:
    note_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "experiments"
        / "v5-kaggle-trace-collection-v2-attempt-001-retention.md"
    )
    content = note_path.read_text(encoding="utf-8")

    assert EXPECTED_ARCHIVE_SHA256 in content
    assert "calibration_fit_status=not_authorized" in content
    assert "threshold_promotion_status=not_authorized" in content
    assert "production_claim_status=not_authorized" in content
