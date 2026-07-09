from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

COLLECTION_ID = "v5-qwen-negative-case-expansion-v1"
ATTEMPT_ID = "attempt-001-t4"
SOURCE_CORPUS_ID = "kaggle_negative_case_expansion_v1"
SOURCE_CORPUS_PATH = Path("data/fixtures/kaggle_negative_case_expansion_v1/prompt_corpus.json")
SOURCE_MANIFEST_PATH = Path("data/fixtures/kaggle_negative_case_expansion_v1/manifest.json")
PRE_COLLECTION_PATH = Path(
    "evidence/kaggle-trace-collection"
    "/v5-qwen-negative-case-expansion-v1/pre-collection/pre_collection_manifest.json"
)
READINESS_BUNDLE_PATH = Path(
    "evidence/kaggle-trace-collection"
    "/v5-qwen-negative-case-expansion-v1/readiness/collection_readiness_bundle.json"
)

DRAFT_MODEL_ID = "Qwen/Qwen2.5-0.5B"
TARGET_MODEL_ID = "Qwen/Qwen2.5-1.5B"
MODEL_PAIR_ID = "qwen2.5-0.5b-draft-qwen2.5-1.5b-target"
TRACE_SCHEMA_VERSION = "kaggle_trace_collection_v2"
DECODING_CONFIGURATION_ID = "greedy_argmax_4_positions_v1"
PLANNED_OUTPUT_ARCHIVE = "specsafe_v5_qwen_negative_case_expansion_v1_attempt_001_t4.zip"

FORBIDDEN_DOWNSTREAM_ACTIONS = [
    "fit_kaggle_derived_calibrator_from_planned_corpus",
    "promote_threshold_policy_from_planned_corpus",
    "promote_scheduler_utility_from_planned_corpus",
    "publish_without_public_safety_review",
    "claim_production_speedup_or_serving_readiness",
]

PERMITTED_OUTPUT_ARTIFACTS = [
    "runtime_records.jsonl",
    "expected_outcome_records.jsonl",
    "timing_records.jsonl",
    "trace_summary.json",
    "environment_report.json",
    "retention_manifest.json",
]


class NegativeCasePrecollectionError(ValueError):
    """Raised when the negative-case pre-collection inputs are invalid."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise NegativeCasePrecollectionError(message)


def _load_source_inputs(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    corpus_path = repo_root / SOURCE_CORPUS_PATH
    source_manifest_path = repo_root / SOURCE_MANIFEST_PATH

    _require(corpus_path.exists(), f"Missing source corpus: {corpus_path}")
    _require(source_manifest_path.exists(), f"Missing source manifest: {source_manifest_path}")

    corpus = load_json(corpus_path)
    source_manifest = load_json(source_manifest_path)

    source_corpus_sha256 = sha256_file(corpus_path)
    declared_hashes = {
        source_manifest.get("prompt_corpus_sha256"),
        source_manifest.get("source_corpus_sha256"),
    }
    _require(
        declared_hashes == {source_corpus_sha256},
        "Source manifest hash fields do not match prompt corpus bytes.",
    )

    prompts = corpus.get("prompts", [])
    planning = corpus.get("planning", {})
    _require(corpus.get("corpus_id") == SOURCE_CORPUS_ID, "Unexpected corpus id.")
    _require(corpus.get("data_role") == "negative_case_trace_collection_planning", "Bad role.")
    _require(len(prompts) == 16, "Expected 16 negative-case prompts.")
    _require(planning.get("planned_runtime_records") == 64, "Expected 64 records.")
    _require(
        source_manifest.get("calibration_fit_status") == "not_authorized",
        "Calibration fitting must not be authorized in the source manifest.",
    )

    return corpus, source_manifest


def _split_counts(prompts: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(prompt["split"] for prompt in prompts).items()))


def _workload_counts(prompts: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(prompt["workload_type"] for prompt in prompts).items()))


def _family_counts(prompts: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(prompt["family_id"] for prompt in prompts).items()))


def build_negative_case_precollection_manifest(repo_root: Path) -> dict[str, Any]:
    corpus, source_manifest = _load_source_inputs(repo_root)
    prompts = corpus["prompts"]
    planning = corpus["planning"]
    prior_diagnostic = corpus["prior_diagnostic_summary"]

    return {
        "attempt_id": ATTEMPT_ID,
        "calibration_fit_status": "not_authorized",
        "collection_id": COLLECTION_ID,
        "data_role": "negative_case_trace_collection_pre_collection_manifest",
        "decoding_configuration_id": DECODING_CONFIGURATION_ID,
        "draft_model_id": DRAFT_MODEL_ID,
        "evidence_class": "planned_kaggle_environment_collection",
        "expected_effect": planning["negative_case_expansion_intent"],
        "family_counts": _family_counts(prompts),
        "forbidden_downstream_actions": FORBIDDEN_DOWNSTREAM_ACTIONS,
        "minimum_additional_negative_records_needed": planning[
            "minimum_additional_negative_records_needed"
        ],
        "model_execution_status": "not_started",
        "model_pair_id": MODEL_PAIR_ID,
        "notebook_execution_status": "not_started",
        "permitted_output_artifacts": PERMITTED_OUTPUT_ARTIFACTS,
        "planned_candidate_positions_per_prompt": planning[
            "planned_candidate_positions_per_prompt"
        ],
        "planned_output_archive": PLANNED_OUTPUT_ARCHIVE,
        "planned_prompt_count": planning["planned_prompt_count"],
        "planned_runtime_records": planning["planned_runtime_records"],
        "pre_collection_manifest_id": (
            "v5_qwen_negative_case_expansion_v1_pre_collection_manifest"
        ),
        "privacy_controls": corpus["privacy_controls"],
        "production_claim_status": "not_authorized",
        "prompt_family_split_policy": corpus["split_policy"],
        "public_release_status": "not_authorized",
        "raw_prompt_text_in_source_corpus": True,
        "raw_prompt_text_retention_in_output_archive": False,
        "readiness_status": "ready_for_negative_case_collection_inputs_only",
        "scheduler_promotion_status": "not_authorized",
        "source_corpus_id": corpus["corpus_id"],
        "source_corpus_path": SOURCE_CORPUS_PATH.as_posix(),
        "source_corpus_sha256": sha256_file(repo_root / SOURCE_CORPUS_PATH),
        "source_manifest_declared_corpus_sha256": source_manifest["source_corpus_sha256"],
        "source_manifest_path": SOURCE_MANIFEST_PATH.as_posix(),
        "source_manifest_sha256": sha256_file(repo_root / SOURCE_MANIFEST_PATH),
        "split_counts": _split_counts(prompts),
        "status": "planned_pre_collection_not_model_evidence",
        "target_model_id": TARGET_MODEL_ID,
        "target_minimum_negative_count_for_calibration_fit": prior_diagnostic[
            "minimum_negative_count_for_calibration_fit"
        ],
        "threshold_promotion_status": "not_authorized",
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "v2_calibration_fit_authorized": prior_diagnostic["calibration_fit_authorized"],
        "v2_observed_negative_count": prior_diagnostic["v2_observed_negative_count"],
        "workload_counts": _workload_counts(prompts),
    }


def build_negative_case_readiness_bundle(repo_root: Path) -> dict[str, Any]:
    pre_collection_manifest = build_negative_case_precollection_manifest(repo_root)
    source_corpus_sha256 = pre_collection_manifest["source_corpus_sha256"]

    temporary_manifest_path = repo_root / PRE_COLLECTION_PATH
    write_json(temporary_manifest_path, pre_collection_manifest)

    return {
        "attempt_id": ATTEMPT_ID,
        "calibration_fit_status": "not_authorized",
        "collection_id": COLLECTION_ID,
        "data_role": "negative_case_trace_collection_readiness_bundle",
        "draft_model_id": DRAFT_MODEL_ID,
        "evidence_class": "planned_kaggle_environment_collection",
        "forbidden_downstream_actions": FORBIDDEN_DOWNSTREAM_ACTIONS,
        "internet_required_for_model_download": True,
        "kaggle_dataset_visibility_required": "private",
        "minimum_additional_negative_records_needed": pre_collection_manifest[
            "minimum_additional_negative_records_needed"
        ],
        "model_execution_status": "not_started",
        "model_pair_id": MODEL_PAIR_ID,
        "notebook_execution_status": "not_started",
        "planned_candidate_positions_per_prompt": pre_collection_manifest[
            "planned_candidate_positions_per_prompt"
        ],
        "planned_output_archive": PLANNED_OUTPUT_ARCHIVE,
        "planned_prompt_count": pre_collection_manifest["planned_prompt_count"],
        "planned_runtime_records": pre_collection_manifest["planned_runtime_records"],
        "pre_collection_manifest_path": PRE_COLLECTION_PATH.as_posix(),
        "pre_collection_manifest_sha256": sha256_file(temporary_manifest_path),
        "production_claim_status": "not_authorized",
        "public_release_status": "not_authorized",
        "readiness_bundle_id": "v5_qwen_negative_case_expansion_v1_readiness_bundle",
        "readiness_status": "ready_for_private_kaggle_t4_collection",
        "required_kaggle_controls": [
            "private_input_dataset",
            "gpu_t4_accelerator",
            "internet_enabled_for_model_download_only",
            "no_secret_printing",
            "no_calibration_fit",
            "no_threshold_promotion",
            "no_scheduler_promotion",
        ],
        "scheduler_promotion_status": "not_authorized",
        "source_corpus_path": SOURCE_CORPUS_PATH.as_posix(),
        "source_corpus_sha256": source_corpus_sha256,
        "source_manifest_path": SOURCE_MANIFEST_PATH.as_posix(),
        "source_manifest_sha256": pre_collection_manifest["source_manifest_sha256"],
        "target_model_id": TARGET_MODEL_ID,
        "threshold_promotion_status": "not_authorized",
        "trace_schema_version": TRACE_SCHEMA_VERSION,
    }


def write_negative_case_precollection_bundle(repo_root: Path) -> tuple[Path, Path]:
    pre_collection_manifest = build_negative_case_precollection_manifest(repo_root)
    pre_collection_path = repo_root / PRE_COLLECTION_PATH
    write_json(pre_collection_path, pre_collection_manifest)

    readiness_bundle = build_negative_case_readiness_bundle(repo_root)
    readiness_bundle_path = repo_root / READINESS_BUNDLE_PATH
    write_json(readiness_bundle_path, readiness_bundle)

    return pre_collection_path, readiness_bundle_path
