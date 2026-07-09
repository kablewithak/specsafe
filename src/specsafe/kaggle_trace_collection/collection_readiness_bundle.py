from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

COLLECTION_ID = "v5-qwen-governed-trace-collection-v2"
READINESS_BUNDLE_ID = "v5-qwen-governed-trace-collection-v2-readiness"

PRE_COLLECTION_MANIFEST_PATH = (
    Path("evidence")
    / "kaggle-trace-collection"
    / COLLECTION_ID
    / "pre-collection"
    / ("pre_collection_manifest.json")
)
READINESS_BUNDLE_PATH = (
    Path("evidence")
    / "kaggle-trace-collection"
    / COLLECTION_ID
    / "readiness"
    / ("collection_readiness_bundle.json")
)
NOTEBOOK_PATH = (
    Path("notebooks") / "kaggle" / "specsafe_v5_qwen_trace_collection_v2_readiness.ipynb"
)
NOTEBOOK_README_PATH = (
    Path("notebooks") / "kaggle" / "specsafe_v5_qwen_trace_collection_v2_README.md"
)

REQUIRED_KAGGLE_CONTROLS = (
    "use_pre_collection_manifest_without_editing_prompt_splits",
    "record_exact_model_and_tokenizer_revisions",
    "record_kaggle_gpu_and_package_versions",
    "export_runtime_records_separately_from_expected_outcomes",
    "retain_sanitized_archive_and_manifest_only",
    "do_not_print_or_commit_tokens_secrets_or_credentials",
)
ALLOWED_OUTPUT_ARTIFACTS = (
    "runtime_records.jsonl",
    "expected_outcomes.jsonl",
    "trace_summary.json",
    "retention_manifest.json",
    "sanitized_trace_archive.zip",
)
FORBIDDEN_OUTPUT_ARTIFACTS = (
    "kaggle_derived_calibrator.json",
    "promoted_threshold_policy.json",
    "scheduler_utility_claim.json",
    "production_speedup_report.json",
    "raw_secret_or_credential_dump.txt",
)
NON_CLAIMS = (
    "not_model_execution_evidence",
    "not_calibration_fit",
    "not_threshold_promotion",
    "not_scheduler_utility_promotion",
    "not_public_release_authorization",
    "not_production_serving_evidence",
)


class CollectionReadinessBundle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["specsafe.kaggle_trace_collection_readiness.v1"]
    readiness_bundle_id: str
    collection_id: str
    source_pre_collection_manifest_path: str
    source_pre_collection_manifest_sha256: str
    source_pre_collection_manifest_id: str
    source_corpus_path: str
    source_corpus_sha256: str
    corpus_id: str
    evidence_class: Literal["kaggle_environment_planned"]
    data_role: Literal["trace_collection_readiness"]
    model_execution_status: Literal["not_started"]
    notebook_execution_status: Literal["not_started"]
    calibration_fit_status: Literal["not_authorized"]
    threshold_promotion_status: Literal["not_authorized"]
    planned_runtime_records: int = Field(ge=100)
    minimum_record_count_for_calibration_fit: int = Field(ge=100)
    minimum_positive_count_for_calibration_fit: int = Field(ge=30)
    minimum_negative_count_for_calibration_fit: int = Field(ge=30)
    split_summary: list[dict[str, Any]]
    workload_summary: list[dict[str, Any]]
    prompt_family_assignment_count: int = Field(ge=1)
    notebook_path: str
    notebook_readme_path: str
    required_kaggle_controls: tuple[str, ...]
    allowed_output_artifacts: tuple[str, ...]
    forbidden_output_artifacts: tuple[str, ...]
    non_claims: tuple[str, ...]
    readiness_gates: dict[str, str]
    next_authorized_step: str

    @field_validator("required_kaggle_controls", "allowed_output_artifacts", mode="after")
    @classmethod
    def _require_non_empty_tuple(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("readiness tuple must not be empty")
        return values


def load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise TypeError(f"Expected JSON object at {path}")
    return loaded


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def build_readiness_bundle(
    pre_collection_manifest: dict[str, Any],
    source_manifest_path: Path,
) -> CollectionReadinessBundle:
    record_plan = pre_collection_manifest["record_plan"]
    readiness_gates = dict(pre_collection_manifest["pre_collection_gates"])
    readiness_gates.update(
        {
            "collection_readiness_bundle_created": "passed",
            "notebook_execution_not_started": "passed",
            "output_artifact_allowlist_declared": "passed",
        }
    )

    bundle = CollectionReadinessBundle(
        schema_version="specsafe.kaggle_trace_collection_readiness.v1",
        readiness_bundle_id=READINESS_BUNDLE_ID,
        collection_id=COLLECTION_ID,
        source_pre_collection_manifest_path=source_manifest_path.as_posix(),
        source_pre_collection_manifest_sha256=sha256_file(source_manifest_path),
        source_pre_collection_manifest_id=pre_collection_manifest["manifest_id"],
        source_corpus_path=pre_collection_manifest["source_corpus_path"],
        source_corpus_sha256=pre_collection_manifest["source_corpus_sha256"],
        corpus_id=pre_collection_manifest["corpus_id"],
        evidence_class="kaggle_environment_planned",
        data_role="trace_collection_readiness",
        model_execution_status="not_started",
        notebook_execution_status="not_started",
        calibration_fit_status="not_authorized",
        threshold_promotion_status="not_authorized",
        planned_runtime_records=record_plan["planned_runtime_records"],
        minimum_record_count_for_calibration_fit=record_plan[
            "minimum_record_count_for_calibration_fit"
        ],
        minimum_positive_count_for_calibration_fit=record_plan[
            "minimum_positive_count_for_calibration_fit"
        ],
        minimum_negative_count_for_calibration_fit=record_plan[
            "minimum_negative_count_for_calibration_fit"
        ],
        split_summary=list(pre_collection_manifest["split_summary"]),
        workload_summary=list(pre_collection_manifest["workload_summary"]),
        prompt_family_assignment_count=len(pre_collection_manifest["prompt_family_assignments"]),
        notebook_path=NOTEBOOK_PATH.as_posix(),
        notebook_readme_path=NOTEBOOK_README_PATH.as_posix(),
        required_kaggle_controls=REQUIRED_KAGGLE_CONTROLS,
        allowed_output_artifacts=ALLOWED_OUTPUT_ARTIFACTS,
        forbidden_output_artifacts=FORBIDDEN_OUTPUT_ARTIFACTS,
        non_claims=NON_CLAIMS,
        readiness_gates=readiness_gates,
        next_authorized_step=(
            "run_readiness_notebook_then_execute_second_kaggle_collection_without_"
            "calibration_fit_or_threshold_promotion"
        ),
    )
    return bundle


def write_readiness_bundle(repo_root: Path) -> CollectionReadinessBundle:
    source_manifest_path = repo_root / PRE_COLLECTION_MANIFEST_PATH
    output_path = repo_root / READINESS_BUNDLE_PATH
    manifest = load_json(source_manifest_path)
    bundle = build_readiness_bundle(manifest, PRE_COLLECTION_MANIFEST_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(stable_json_bytes(bundle.model_dump(mode="json")))
    return bundle
