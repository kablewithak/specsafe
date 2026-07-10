from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

NEGATIVE_CASE_BASE = Path(
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/attempt-001-t4"
)
V2_BASE = Path(
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/attempt-001-t4"
)
ARCHIVE_NAME = "specsafe_v5_qwen_negative_case_expansion_v1_attempt_001_t4.zip"
EXPECTED_ARCHIVE_SHA256 = "557c7519aa6012c4770d9e24df1e15815a3295447f3eac2080b1b28c511c601e"
EXPECTED_ARCHIVE_MEMBERS = {
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "attempt-001-t4/runtime_records.jsonl",
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "attempt-001-t4/expected_outcome_records.jsonl",
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "attempt-001-t4/timing_records.jsonl",
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "attempt-001-t4/trace_summary.json",
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "attempt-001-t4/environment_report.json",
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "attempt-001-t4/retention_manifest.json",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_negative_case_archive_is_retained_with_expected_hash_and_members() -> None:
    archive_path = NEGATIVE_CASE_BASE / ARCHIVE_NAME

    assert archive_path.exists()
    assert _sha256_file(archive_path) == EXPECTED_ARCHIVE_SHA256

    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == EXPECTED_ARCHIVE_MEMBERS
        assert all("\\" not in name for name in archive.namelist())


def test_extracted_artifacts_match_retention_manifest_hashes() -> None:
    manifest = _read_json(NEGATIVE_CASE_BASE / "retention_manifest.json")

    for filename, expected_hash in manifest["file_hashes"].items():
        artifact_path = NEGATIVE_CASE_BASE / filename
        assert artifact_path.exists()
        assert _sha256_file(artifact_path) == expected_hash


def test_negative_case_summary_counts_and_non_authorization_boundary() -> None:
    summary = _read_json(NEGATIVE_CASE_BASE / "trace_summary.json")
    manifest = _read_json(NEGATIVE_CASE_BASE / "retention_manifest.json")

    assert summary["collection_id"] == "v5-qwen-negative-case-expansion-v1"
    assert summary["attempt_id"] == "attempt-001-t4"
    assert summary["trace_schema_version"] == "kaggle_trace_collection_v2"
    assert summary["case_count"] == 16
    assert summary["planned_runtime_records"] == 64
    assert summary["runtime_record_count"] == 64
    assert summary["expected_outcome_record_count"] == 64
    assert summary["target_argmax_match_count"] == 51
    assert summary["target_argmax_nonmatch_count"] == 13
    assert summary["target_argmax_match_rate"] == 0.796875
    assert summary["raw_prompt_text_retained"] is False

    assert manifest["calibration_fit_status"] == "not_authorized"
    assert manifest["threshold_promotion_status"] == "not_authorized"
    assert manifest["scheduler_promotion_status"] == "not_authorized"
    assert manifest["production_claim_status"] == "not_authorized"


def test_runtime_and_expected_outcome_records_are_joinable_and_separated() -> None:
    runtime_records = _read_jsonl(NEGATIVE_CASE_BASE / "runtime_records.jsonl")
    outcome_records = _read_jsonl(NEGATIVE_CASE_BASE / "expected_outcome_records.jsonl")

    assert len(runtime_records) == 64
    assert len(outcome_records) == 64
    assert {record["trace_id"] for record in runtime_records} == {
        record["trace_id"] for record in outcome_records
    }
    assert all(record["record_type"] == "runtime" for record in runtime_records)
    assert all(record["record_type"] == "expected_outcome" for record in outcome_records)

    assert all("observed_acceptance" not in record for record in runtime_records)
    assert all("conditional_acceptance_label" not in record for record in runtime_records)
    assert all("target_argmax_token_id" not in record for record in runtime_records)

    assert all("observed_acceptance" in record for record in outcome_records)
    assert all("conditional_acceptance_label" in record for record in outcome_records)
    assert all(
        record["outcome_metadata"]["label_available_to_runtime_policy"] is False
        for record in outcome_records
    )


def test_negative_case_split_and_workload_counts_are_preserved() -> None:
    summary = _read_json(NEGATIVE_CASE_BASE / "trace_summary.json")

    assert summary["split_record_counts"] == {
        "negative_probe_calibration_candidate": 32,
        "negative_probe_holdout": 32,
    }
    assert summary["workload_record_counts"] == {
        "code": 24,
        "open_ended_chat": 24,
        "structured_text": 16,
    }


def test_environment_report_preserves_model_and_runtime_provenance() -> None:
    environment = _read_json(NEGATIVE_CASE_BASE / "environment_report.json")

    assert environment["source_commit"] == "cd238e3e84391585be01e635ce74c4d400ba2dce"
    assert environment["draft_model_id"] == "Qwen/Qwen2.5-0.5B"
    assert environment["target_model_id"] == "Qwen/Qwen2.5-1.5B"
    assert environment["tokenizer_id"] == "Qwen/Qwen2.5-1.5B"
    assert environment["cuda_available"] is True
    assert environment["cuda_device_count"] == 2
    assert environment["cuda_devices"] == ["Tesla T4", "Tesla T4"]
    assert environment["secrets_printed"] is False
    assert environment["internet_required_for_model_download"] is True


def test_combined_raw_negative_count_crosses_prior_readiness_floor() -> None:
    v2_summary = _read_json(V2_BASE / "trace_summary.json")
    negative_case_summary = _read_json(NEGATIVE_CASE_BASE / "trace_summary.json")

    combined_records = (
        v2_summary["runtime_record_count"] + negative_case_summary["runtime_record_count"]
    )
    combined_matches = (
        v2_summary["target_argmax_match_count"] + negative_case_summary["target_argmax_match_count"]
    )
    combined_nonmatches = (
        v2_summary["target_argmax_nonmatch_count"]
        + negative_case_summary["target_argmax_nonmatch_count"]
    )

    assert v2_summary["target_argmax_nonmatch_count"] == 23
    assert negative_case_summary["target_argmax_nonmatch_count"] == 13
    assert combined_records == 184
    assert combined_matches == 148
    assert combined_nonmatches == 36
    assert combined_nonmatches >= 30

    assert negative_case_summary["calibration_fit_status"] == "not_authorized"
    assert negative_case_summary["threshold_promotion_status"] == "not_authorized"
