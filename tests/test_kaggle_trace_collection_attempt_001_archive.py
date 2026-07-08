from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from specsafe.kaggle_trace_collection import (
    KaggleTraceCollectionExpectedOutcomeRecord,
    KaggleTraceCollectionManifest,
    KaggleTraceCollectionRuntimeRecord,
)

ATTEMPT_DIR = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-governed-trace-collection-v1/attempt-001-t4"
)
ARCHIVE_PATH = ATTEMPT_DIR / "specsafe_v5_qwen_trace_collection_v1_attempt_001.zip"
RETENTION_MANIFEST_PATH = ATTEMPT_DIR / "retention_manifest.json"
TRACE_SUMMARY_PATH = ATTEMPT_DIR / "trace_summary.json"

EXPECTED_ARCHIVE_SHA256 = (
    "03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c"
)
EXPECTED_INNER_SHA256 = {
    "runtime_records.jsonl": (
        "19f9b35ad6d5bec552a92e835cdf92ee1cabfff26f4e502722389402e9f216b9"
    ),
    "expected_outcomes.jsonl": (
        "f42cb4222dbdfe27af4b5ca10dc9b59ba705b559c14362c019f707c6edee8060"
    ),
    "manifest.json": "550f6a370ecd8a914738634cef7c9d5e3af48867bb8c92c19d60202a82024a62",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_jsonl(payload: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]


def archive_payloads() -> dict[str, bytes]:
    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        names = sorted(archive.namelist())
        assert names == [
            "expected_outcomes.jsonl",
            "manifest.json",
            "runtime_records.jsonl",
        ]
        return {name: archive.read(name) for name in names}


def test_attempt_001_archive_is_hash_addressed_and_retained() -> None:
    assert ARCHIVE_PATH.exists()
    assert sha256_bytes(ARCHIVE_PATH.read_bytes()) == EXPECTED_ARCHIVE_SHA256

    payloads = archive_payloads()
    for relative_path, expected_hash in EXPECTED_INNER_SHA256.items():
        assert sha256_bytes(payloads[relative_path]) == expected_hash


def test_attempt_001_archive_manifest_and_records_validate_contracts() -> None:
    payloads = archive_payloads()
    manifest = KaggleTraceCollectionManifest.model_validate_json(
        payloads["manifest.json"]
    )
    runtime_records = [
        KaggleTraceCollectionRuntimeRecord.model_validate(record)
        for record in read_jsonl(payloads["runtime_records.jsonl"])
    ]
    expected_outcomes = [
        KaggleTraceCollectionExpectedOutcomeRecord.model_validate(record)
        for record in read_jsonl(payloads["expected_outcomes.jsonl"])
    ]

    assert manifest.collection_id == "v5-qwen-governed-trace-collection-v1"
    assert manifest.collection_attempt_id == "attempt-001-t4"
    assert manifest.source_commit_sha == "cff5905075044770010653c637d3c52c4ccb6fbe"
    assert manifest.preflight_attempt_id == "attempt-003-t4-pass"
    assert manifest.runtime_record_count == 24
    assert manifest.expected_outcome_record_count == 24
    assert len(runtime_records) == manifest.runtime_record_count
    assert len(expected_outcomes) == manifest.expected_outcome_record_count
    assert {record.case_id for record in runtime_records} == {
        "KTC5-001",
        "KTC5-002",
        "KTC5-003",
        "KTC5-004",
        "KTC5-005",
        "KTC5-006",
    }


def test_attempt_001_runtime_and_outcome_records_share_keys_without_leakage() -> None:
    payloads = archive_payloads()
    runtime_records = read_jsonl(payloads["runtime_records.jsonl"])
    expected_outcomes = read_jsonl(payloads["expected_outcomes.jsonl"])

    key_fields = ("trace_id", "case_id", "decode_round", "block_position_index")
    runtime_keys = {
        tuple(record[field] for field in key_fields) for record in runtime_records
    }
    outcome_keys = {
        tuple(record[field] for field in key_fields) for record in expected_outcomes
    }

    assert runtime_keys == outcome_keys

    forbidden_runtime_fields = {
        "candidate_token_id",
        "candidate_text",
        "decoded_candidate",
        "target_probability",
        "target_entropy",
        "target_argmax_matches_candidate",
        "raw_logits",
        "prompt_text",
    }
    for record in runtime_records:
        assert forbidden_runtime_fields.isdisjoint(record)


def test_attempt_001_trace_summary_matches_archive_records() -> None:
    payloads = archive_payloads()
    runtime_records = read_jsonl(payloads["runtime_records.jsonl"])
    expected_outcomes = read_jsonl(payloads["expected_outcomes.jsonl"])
    summary = json.loads(TRACE_SUMMARY_PATH.read_text(encoding="utf-8"))

    match_count = sum(
        1 for outcome in expected_outcomes if outcome["target_argmax_matches_candidate"]
    )

    assert summary["archive_sha256"] == EXPECTED_ARCHIVE_SHA256
    assert summary["runtime_record_count"] == len(runtime_records) == 24
    assert summary["expected_outcome_record_count"] == len(expected_outcomes) == 24
    assert summary["target_argmax_match_count"] == match_count == 15
    assert summary["target_argmax_nonmatch_count"] == 9
    assert summary["target_argmax_match_rate"] == pytest.approx(0.625)
    assert summary["interpretation_boundary"]["calibration_fit_performed"] is False
    assert (
        summary["interpretation_boundary"]["policy_utility_evaluation_performed"]
        is False
    )


def test_terminal_result_json_absence_is_explicitly_documented() -> None:
    retention_manifest = json.loads(
        RETENTION_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert retention_manifest["archive"]["sha256"] == EXPECTED_ARCHIVE_SHA256
    assert retention_manifest["terminal_result_json"]["retained"] is False
    assert (
        retention_manifest["terminal_result_json"]["manual_recreation_allowed"]
        is False
    )
    assert (
        retention_manifest["terminal_result_json"]["rerun_to_recreate_allowed"]
        is False
    )
    assert (
        retention_manifest["promotion_authorization"]["local_trace_analysis_authorized"]
        is True
    )
    assert (
        retention_manifest["promotion_authorization"]["calibration_refit_authorized"]
        is False
    )
