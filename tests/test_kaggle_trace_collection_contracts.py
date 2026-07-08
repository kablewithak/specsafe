from __future__ import annotations

import pytest
from pydantic import ValidationError

from specsafe.kaggle_trace_collection import (
    KaggleModelIdentity,
    KaggleTraceCollectionExpectedOutcomeRecord,
    KaggleTraceCollectionFailure,
    KaggleTraceCollectionFailureCode,
    KaggleTraceCollectionManifest,
    KaggleTraceCollectionManifestFile,
    KaggleTraceCollectionResult,
    KaggleTraceCollectionRuntimeRecord,
    KaggleTraceCollectionStatus,
)


def make_runtime_record() -> KaggleTraceCollectionRuntimeRecord:
    return KaggleTraceCollectionRuntimeRecord(
        schema_version="specsafe-kaggle-trace-runtime-record-v1",
        trace_id="KTC5-001-trace",
        case_id="KTC5-001",
        request_id="KTC5-001-request",
        workload_type="code",
        data_role="trace_collection",
        collection_partition="unassigned",
        source_type="kaggle_export",
        prompt_sha256="a" * 64,
        prompt_token_count=5,
        model_pair_id="qwen-pair-v1",
        draft_model=KaggleModelIdentity(model_id="draft", revision="1234567"),
        target_model=KaggleModelIdentity(model_id="target", revision="1234567"),
        tokenizer_source_model=KaggleModelIdentity(model_id="draft", revision="1234567"),
        seed=1,
        decoding_configuration_id="greedy-v1",
        decode_round=0,
        block_position_index=1,
        raw_draft_probability=0.5,
        raw_draft_entropy=1.0,
        conditional_survival_confidence=0.5,
    )


def make_manifest() -> KaggleTraceCollectionManifest:
    model_identity = KaggleModelIdentity(model_id="Qwen/example", revision="1" * 40)
    return KaggleTraceCollectionManifest(
        schema_version="specsafe-kaggle-trace-collection-manifest-v1",
        collection_id="v5-qwen-governed-trace-collection-v1",
        collection_attempt_id="attempt-001-t4",
        source_commit_sha="c" * 40,
        preflight_attempt_id="attempt-003-t4-pass",
        preflight_source_commit_sha="a" * 40,
        preflight_result_sha256="b" * 64,
        prompt_corpus_id="kaggle-trace-collection-v1",
        prompt_corpus_sha256="d" * 64,
        data_role="trace_collection",
        collection_partition="unassigned",
        source_type="kaggle_export",
        model_pair_id="qwen2.5-0.5b-to-1.5b",
        draft_model=model_identity,
        target_model=model_identity,
        tokenizer_source_model=model_identity,
        seed=17,
        decoding_configuration_id="greedy-next-token-block-4-v1",
        case_count=6,
        runtime_record_count=24,
        expected_outcome_record_count=24,
        environment={"gpu_name": "Tesla T4", "cuda_available": True},
        files=(
            KaggleTraceCollectionManifestFile(
                relative_path="runtime_records.jsonl",
                sha256="e" * 64,
                byte_count=1,
                record_count=24,
            ),
            KaggleTraceCollectionManifestFile(
                relative_path="expected_outcomes.jsonl",
                sha256="f" * 64,
                byte_count=1,
                record_count=24,
            ),
        ),
    )


def test_runtime_record_rejects_target_derived_outcome_fields() -> None:
    payload = make_runtime_record().model_dump()
    payload["target_probability"] = 0.7

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        KaggleTraceCollectionRuntimeRecord.model_validate(payload)


def test_runtime_record_requires_visible_prefix_to_match_position() -> None:
    payload = make_runtime_record().model_dump()
    payload["block_position_index"] = 2

    with pytest.raises(ValidationError, match="block_position_index"):
        KaggleTraceCollectionRuntimeRecord.model_validate(payload)


def test_expected_outcome_record_keeps_candidate_and_target_fields_out_of_runtime() -> None:
    record = KaggleTraceCollectionExpectedOutcomeRecord(
        schema_version="specsafe-kaggle-trace-expected-outcome-record-v1",
        trace_id="KTC5-001-trace",
        case_id="KTC5-001",
        decode_round=0,
        block_position_index=1,
        candidate_token_id=42,
        target_probability=0.3,
        target_entropy=2.0,
        target_argmax_matches_candidate=True,
        prefix_target_argmax_match=True,
    )

    assert record.candidate_token_id == 42
    assert record.target_argmax_matches_candidate is True


def test_manifest_requires_preflight_provenance_fields() -> None:
    manifest = make_manifest()

    assert manifest.preflight_attempt_id == "attempt-003-t4-pass"
    assert manifest.preflight_source_commit_sha == "a" * 40

    payload = manifest.model_dump()
    del payload["preflight_attempt_id"]

    with pytest.raises(ValidationError, match="preflight_attempt_id"):
        KaggleTraceCollectionManifest.model_validate(payload)


def test_passing_result_requires_archive_and_hashes() -> None:
    with pytest.raises(ValidationError, match="passing result"):
        KaggleTraceCollectionResult(
            schema_version="specsafe-kaggle-trace-collection-result-v1",
            collection_id="collection",
            collection_attempt_id="attempt",
            status=KaggleTraceCollectionStatus.PASSES_GOVERNED_TRACE_COLLECTION,
            trace_collection_performed=False,
            trace_collection_archive_created=False,
        )


def test_failing_result_requires_bounded_failure() -> None:
    with pytest.raises(ValidationError, match="failing result"):
        KaggleTraceCollectionResult(
            schema_version="specsafe-kaggle-trace-collection-result-v1",
            collection_id="collection",
            collection_attempt_id="attempt",
            status=KaggleTraceCollectionStatus.FAILS_GOVERNED_TRACE_COLLECTION,
            trace_collection_performed=False,
            trace_collection_archive_created=False,
        )

    result = KaggleTraceCollectionResult(
        schema_version="specsafe-kaggle-trace-collection-result-v1",
        collection_id="collection",
        collection_attempt_id="attempt",
        status=KaggleTraceCollectionStatus.FAILS_GOVERNED_TRACE_COLLECTION,
        trace_collection_performed=False,
        trace_collection_archive_created=False,
        failure=KaggleTraceCollectionFailure(
            code=KaggleTraceCollectionFailureCode.PROMPT_CORPUS_MISMATCH,
            message="Corpus drift.",
        ),
    )

    assert result.failure is not None
