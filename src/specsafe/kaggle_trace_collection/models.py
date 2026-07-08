"""Strict contracts for Kaggle-exported SpecSafe trace-collection artifacts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import StrictContract, WorkloadType


class KaggleTraceCollectionStatus(StrEnum):
    """Terminal status for one governed Kaggle trace-collection attempt."""

    PASSES_GOVERNED_TRACE_COLLECTION = "passes_governed_trace_collection"
    FAILS_GOVERNED_TRACE_COLLECTION = "fails_governed_trace_collection"


class KaggleTraceCollectionFailureCode(StrEnum):
    """Bounded failure taxonomy for Kaggle trace collection."""

    GPU_UNAVAILABLE = "gpu_unavailable"
    GPU_ARCHITECTURE_UNSUPPORTED = "gpu_architecture_unsupported"
    SOURCE_COMMIT_SHA_MISSING = "source_commit_sha_missing"
    SOURCE_COMMIT_SHA_INVALID = "source_commit_sha_invalid"
    PROMPT_CORPUS_MISMATCH = "prompt_corpus_mismatch"
    MODEL_OUTPUT_NON_FINITE = "model_output_non_finite"
    MODEL_VOCABULARY_MISMATCH = "model_vocabulary_mismatch"
    OUTPUT_ALREADY_EXISTS = "output_already_exists"
    UNEXPECTED_COLLECTION_FAILURE = "unexpected_collection_failure"


class KaggleModelIdentity(StrictContract):
    """Pinned public model identity retained with every exported trace artifact."""

    model_id: str = Field(min_length=1, max_length=200)
    revision: str = Field(min_length=7, max_length=128)


class KaggleTraceCollectionRuntimeRecord(StrictContract):
    """Candidate-time fields separated from target-derived evaluation outcomes."""

    schema_version: Literal["specsafe-kaggle-trace-runtime-record-v1"]
    trace_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    workload_type: WorkloadType
    data_role: Literal["trace_collection"]
    collection_partition: Literal["unassigned"]
    source_type: Literal["kaggle_export"]
    prompt_sha256: str = Field(min_length=64, max_length=64)
    prompt_token_count: int = Field(ge=1)
    model_pair_id: str = Field(min_length=1, max_length=200)
    draft_model: KaggleModelIdentity
    target_model: KaggleModelIdentity
    tokenizer_source_model: KaggleModelIdentity
    seed: int = Field(ge=0)
    decoding_configuration_id: str = Field(min_length=1, max_length=128)
    decode_round: int = Field(ge=0)
    block_position_index: int = Field(ge=1)
    visible_prefix_token_ids: tuple[int, ...] = ()
    raw_draft_probability: float = Field(ge=0.0, le=1.0)
    raw_draft_entropy: float = Field(ge=0.0)
    conditional_survival_confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_visible_prefix_position(self) -> KaggleTraceCollectionRuntimeRecord:
        expected_position = len(self.visible_prefix_token_ids) + 1
        if self.block_position_index != expected_position:
            raise ValueError("block_position_index must equal len(visible_prefix_token_ids) + 1")
        return self


class KaggleTraceCollectionExpectedOutcomeRecord(StrictContract):
    """Post-hoc target-derived labels that must not enter a runtime policy input."""

    schema_version: Literal["specsafe-kaggle-trace-expected-outcome-record-v1"]
    trace_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    decode_round: int = Field(ge=0)
    block_position_index: int = Field(ge=1)
    candidate_token_id: int = Field(ge=0)
    target_probability: float = Field(ge=0.0, le=1.0)
    target_entropy: float = Field(ge=0.0)
    target_argmax_matches_candidate: bool
    prefix_target_argmax_match: bool


class KaggleTraceCollectionManifestFile(StrictContract):
    """Hash-addressed exported file entry."""

    relative_path: str = Field(min_length=1, max_length=300)
    sha256: str = Field(min_length=64, max_length=64)
    byte_count: int = Field(ge=1)
    record_count: int = Field(ge=0)


class KaggleTraceCollectionManifest(StrictContract):
    """Machine-readable provenance manifest for one trace-collection attempt."""

    schema_version: Literal["specsafe-kaggle-trace-collection-manifest-v1"]
    collection_id: str = Field(min_length=1, max_length=128)
    collection_attempt_id: str = Field(min_length=1, max_length=128)
    source_commit_sha: str = Field(min_length=7, max_length=128)
    preflight_result_sha256: str = Field(min_length=64, max_length=64)
    prompt_corpus_id: str = Field(min_length=1, max_length=128)
    prompt_corpus_sha256: str = Field(min_length=64, max_length=64)
    data_role: Literal["trace_collection"]
    collection_partition: Literal["unassigned"]
    source_type: Literal["kaggle_export"]
    model_pair_id: str = Field(min_length=1, max_length=200)
    draft_model: KaggleModelIdentity
    target_model: KaggleModelIdentity
    tokenizer_source_model: KaggleModelIdentity
    seed: int = Field(ge=0)
    decoding_configuration_id: str = Field(min_length=1, max_length=128)
    case_count: int = Field(ge=1)
    runtime_record_count: int = Field(ge=1)
    expected_outcome_record_count: int = Field(ge=1)
    environment: dict[str, str | bool | list[str]]
    files: tuple[KaggleTraceCollectionManifestFile, ...] = Field(min_length=2)


class KaggleTraceCollectionFailure(StrictContract):
    """Bounded retained failure envelope."""

    code: KaggleTraceCollectionFailureCode
    message: str = Field(min_length=1, max_length=500)


class KaggleTraceCollectionResult(StrictContract):
    """Terminal result for one governed Kaggle trace-collection execution."""

    schema_version: Literal["specsafe-kaggle-trace-collection-result-v1"]
    collection_id: str = Field(min_length=1, max_length=128)
    collection_attempt_id: str = Field(min_length=1, max_length=128)
    status: KaggleTraceCollectionStatus
    trace_collection_performed: bool
    trace_collection_archive_created: bool
    source_commit_sha: str | None = Field(default=None, min_length=7, max_length=128)
    manifest_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    archive_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    failure: KaggleTraceCollectionFailure | None = None

    @model_validator(mode="after")
    def validate_terminal_state(self) -> KaggleTraceCollectionResult:
        if self.status is KaggleTraceCollectionStatus.PASSES_GOVERNED_TRACE_COLLECTION:
            if not self.trace_collection_performed or not self.trace_collection_archive_created:
                raise ValueError("a passing result must retain the completed trace archive")
            if self.failure is not None:
                raise ValueError("a passing result cannot contain a failure")
            if self.manifest_sha256 is None or self.archive_sha256 is None:
                raise ValueError("a passing result requires manifest and archive hashes")
        if self.status is KaggleTraceCollectionStatus.FAILS_GOVERNED_TRACE_COLLECTION:
            if self.trace_collection_performed or self.trace_collection_archive_created:
                raise ValueError("a failing result cannot claim completed trace collection")
            if self.failure is None:
                raise ValueError("a failing result requires a bounded failure")
        return self
