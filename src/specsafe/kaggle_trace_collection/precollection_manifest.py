from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CORPUS_ID = "kaggle_trace_corpus_expansion_v1"
CORPUS_SCHEMA_VERSION = "specsafe.kaggle_prompt_corpus.v1"
MANIFEST_ID = "v5-qwen-governed-trace-collection-v2-precollection"
MANIFEST_SCHEMA_VERSION = "specsafe.kaggle_precollection_manifest.v1"
SOURCE_CORPUS_PATH = "data/fixtures/kaggle_trace_corpus_expansion_v1/prompt_corpus.json"

_ALLOWED_SOURCES = {"self_authored_public_safe"}
_ALLOWED_SPLITS = {
    "adversarial_regression",
    "calibration",
    "development",
    "final_evaluation",
}
_FORBIDDEN_PROMPT_FIELDS = {
    "accepted_token_count",
    "calibrated_probability",
    "conditional_acceptance_label",
    "observed_acceptance",
    "prefix_survival_label",
    "promoted_threshold",
    "target_argmax_match",
    "target_probability",
}
_FORBIDDEN_DOWNSTREAM_ACTIONS = [
    "fit_kaggle_derived_calibrator_from_planned_corpus",
    "promote_threshold_policy_from_planned_corpus",
    "promote_scheduler_utility_from_planned_corpus",
    "publish_public_dataset_from_planned_corpus_without_public_safety_review",
    "claim_production_speedup_or_serving_readiness",
]


class SplitSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    split: str
    prompt_count: int = Field(ge=1)
    planned_runtime_records: int = Field(ge=1)
    workload_counts: dict[str, int]


class WorkloadSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workload_type: str
    prompt_count: int = Field(ge=1)
    planned_runtime_records: int = Field(ge=1)
    split_counts: dict[str, int]


class PromptFamilyAssignment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family_id: str
    split: str
    workload_type: str
    prompt_ids: list[str]


class RecordPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    planned_prompt_count: int = Field(ge=1)
    planned_candidate_positions_per_prompt: int = Field(ge=1)
    planned_runtime_records: int = Field(ge=1)
    minimum_record_count_for_calibration_fit: int = Field(ge=1)
    minimum_positive_count_for_calibration_fit: int = Field(ge=1)
    minimum_negative_count_for_calibration_fit: int = Field(ge=1)
    positive_negative_balance_status: Literal["cannot_be_known_before_model_execution"]
    next_gate: str


class PrecollectionManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["specsafe.kaggle_precollection_manifest.v1"]
    manifest_id: Literal["v5-qwen-governed-trace-collection-v2-precollection"]
    corpus_id: Literal["kaggle_trace_corpus_expansion_v1"]
    source_corpus_path: str
    source_corpus_sha256: str
    data_role: Literal["trace_collection"]
    evidence_class: Literal["kaggle_environment_planned"]
    model_execution_status: Literal["not_started"]
    collection_status: Literal["pre_collection_ready"]
    calibration_fit_status: Literal["not_authorized"]
    threshold_promotion_status: Literal["not_authorized"]
    record_plan: RecordPlan
    split_summary: list[SplitSummary]
    workload_summary: list[WorkloadSummary]
    prompt_family_assignments: list[PromptFamilyAssignment]
    pre_collection_gates: dict[str, Literal["passed"]]
    forbidden_downstream_actions: list[str]
    next_authorized_step: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_precollection_manifest(
    corpus: dict[str, Any],
    *,
    source_corpus_path: str = SOURCE_CORPUS_PATH,
    source_corpus_sha256: str,
) -> PrecollectionManifest:
    _validate_corpus_header(corpus)
    prompts = _validated_prompts(corpus)
    record_plan = _validated_record_plan(corpus, prompts)
    family_assignments = _build_family_assignments(prompts)

    split_summary = _build_split_summary(prompts)
    workload_summary = _build_workload_summary(prompts)

    return PrecollectionManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        manifest_id=MANIFEST_ID,
        corpus_id=CORPUS_ID,
        source_corpus_path=source_corpus_path,
        source_corpus_sha256=source_corpus_sha256,
        data_role="trace_collection",
        evidence_class="kaggle_environment_planned",
        model_execution_status="not_started",
        collection_status="pre_collection_ready",
        calibration_fit_status="not_authorized",
        threshold_promotion_status="not_authorized",
        record_plan=record_plan,
        split_summary=split_summary,
        workload_summary=workload_summary,
        prompt_family_assignments=family_assignments,
        pre_collection_gates={
            "no_calibration_fit": "passed",
            "no_outcome_labels": "passed",
            "no_threshold_promotion": "passed",
            "planned_record_count_minimum": "passed",
            "prompt_family_split_isolation": "passed",
            "public_safe_source_policy": "passed",
        },
        forbidden_downstream_actions=_FORBIDDEN_DOWNSTREAM_ACTIONS,
        next_authorized_step=("run_second_kaggle_trace_collection_against_this_manifest"),
    )


def write_precollection_manifest(
    manifest: PrecollectionManifest,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump(mode="json")
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_and_write_precollection_manifest(
    corpus_path: Path,
    output_path: Path,
) -> PrecollectionManifest:
    corpus = load_json(corpus_path)
    manifest = build_precollection_manifest(
        corpus,
        source_corpus_path=SOURCE_CORPUS_PATH,
        source_corpus_sha256=sha256_file(corpus_path),
    )
    write_precollection_manifest(manifest, output_path)
    return manifest


def _validate_corpus_header(corpus: dict[str, Any]) -> None:
    expected_values = {
        "calibration_fit_status": "not_authorized",
        "corpus_id": CORPUS_ID,
        "corpus_status": "planned_pre_collection",
        "data_role": "trace_collection",
        "evidence_class": "kaggle_environment_planned",
        "model_execution_status": "not_started",
        "schema_version": CORPUS_SCHEMA_VERSION,
        "threshold_promotion_status": "not_authorized",
    }
    for key, expected in expected_values.items():
        actual = corpus.get(key)
        if actual != expected:
            raise ValueError(f"{key} must be {expected!r}; got {actual!r}")

    forbidden_actions = corpus.get("forbidden_downstream_actions", [])
    for action in _FORBIDDEN_DOWNSTREAM_ACTIONS:
        if action not in forbidden_actions:
            raise ValueError(f"missing forbidden downstream action: {action}")

    source_policy = corpus.get("source_policy", {})
    allowed_sources = set(source_policy.get("allowed_sources", []))
    if allowed_sources != _ALLOWED_SOURCES:
        raise ValueError("corpus source policy must allow only self-authored public-safe prompts")

    split_policy = corpus.get("split_policy", {})
    if split_policy.get("split_unit") != "prompt_family":
        raise ValueError("split unit must be prompt_family")
    if split_policy.get("final_evaluation_may_influence_before_final_report") is not False:
        raise ValueError("final evaluation may not influence decisions before final report")
    if split_policy.get("threshold_tuning_from_final_evaluation") is not False:
        raise ValueError("threshold tuning from final evaluation must remain blocked")
    if set(split_policy.get("allowed_splits", [])) != _ALLOWED_SPLITS:
        raise ValueError("allowed splits do not match the governed split set")


def _validated_prompts(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    prompts = corpus.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        raise ValueError("corpus must contain at least one prompt")

    seen_prompt_ids: set[str] = set()
    for prompt in prompts:
        if not isinstance(prompt, dict):
            raise ValueError("each prompt must be an object")
        forbidden_fields = _FORBIDDEN_PROMPT_FIELDS.intersection(prompt)
        if forbidden_fields:
            joined = ", ".join(sorted(forbidden_fields))
            raise ValueError(f"prompt contains forbidden outcome/execution fields: {joined}")

        prompt_id = _required_string(prompt, "prompt_id")
        if prompt_id in seen_prompt_ids:
            raise ValueError(f"duplicate prompt_id: {prompt_id}")
        seen_prompt_ids.add(prompt_id)

        split = _required_string(prompt, "split")
        if split not in _ALLOWED_SPLITS:
            raise ValueError(f"unsupported split: {split}")
        source_type = _required_string(prompt, "source_type")
        if source_type not in _ALLOWED_SOURCES:
            raise ValueError(f"unsupported source_type: {source_type}")

        planned_positions = prompt.get("planned_candidate_positions")
        if planned_positions != [1, 2, 3, 4]:
            raise ValueError(f"{prompt_id} must plan candidate positions [1, 2, 3, 4]")

        prompt_text = _required_string(prompt, "prompt_text")
        if _looks_private_or_secret(prompt_text):
            raise ValueError(f"{prompt_id} contains private-looking or secret-looking text")

    return prompts


def _validated_record_plan(
    corpus: dict[str, Any],
    prompts: list[dict[str, Any]],
) -> RecordPlan:
    record_plan = RecordPlan.model_validate(corpus.get("record_planning"))
    planned_records = sum(len(prompt["planned_candidate_positions"]) for prompt in prompts)
    if record_plan.planned_prompt_count != len(prompts):
        raise ValueError("planned prompt count does not match prompt corpus")
    if record_plan.planned_runtime_records != planned_records:
        raise ValueError("planned runtime record count does not match candidate positions")
    if record_plan.planned_runtime_records < record_plan.minimum_record_count_for_calibration_fit:
        raise ValueError("planned runtime records must meet the calibration-fit count floor")
    if record_plan.minimum_positive_count_for_calibration_fit != 30:
        raise ValueError("minimum positive count must remain 30")
    if record_plan.minimum_negative_count_for_calibration_fit != 30:
        raise ValueError("minimum negative count must remain 30")
    return record_plan


def _build_family_assignments(
    prompts: list[dict[str, Any]],
) -> list[PromptFamilyAssignment]:
    family_splits: dict[str, set[str]] = defaultdict(set)
    family_workloads: dict[str, set[str]] = defaultdict(set)
    family_prompt_ids: dict[str, list[str]] = defaultdict(list)

    for prompt in prompts:
        family_id = _required_string(prompt, "family_id")
        family_splits[family_id].add(_required_string(prompt, "split"))
        family_workloads[family_id].add(_required_string(prompt, "workload_type"))
        family_prompt_ids[family_id].append(_required_string(prompt, "prompt_id"))

    assignments: list[PromptFamilyAssignment] = []
    for family_id in sorted(family_prompt_ids):
        splits = family_splits[family_id]
        if len(splits) != 1:
            raise ValueError(f"prompt family leaks across splits: {family_id}")
        workloads = family_workloads[family_id]
        if len(workloads) != 1:
            raise ValueError(f"prompt family spans multiple workloads: {family_id}")
        assignments.append(
            PromptFamilyAssignment(
                family_id=family_id,
                split=next(iter(splits)),
                workload_type=next(iter(workloads)),
                prompt_ids=sorted(family_prompt_ids[family_id]),
            )
        )
    return assignments


def _build_split_summary(prompts: list[dict[str, Any]]) -> list[SplitSummary]:
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prompt in prompts:
        by_split[prompt["split"]].append(prompt)

    summaries: list[SplitSummary] = []
    for split in sorted(by_split):
        split_prompts = by_split[split]
        workload_counts = Counter(prompt["workload_type"] for prompt in split_prompts)
        planned_records = sum(
            len(prompt["planned_candidate_positions"]) for prompt in split_prompts
        )
        summaries.append(
            SplitSummary(
                split=split,
                prompt_count=len(split_prompts),
                planned_runtime_records=planned_records,
                workload_counts=dict(sorted(workload_counts.items())),
            )
        )
    return summaries


def _build_workload_summary(prompts: list[dict[str, Any]]) -> list[WorkloadSummary]:
    by_workload: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prompt in prompts:
        by_workload[prompt["workload_type"]].append(prompt)

    summaries: list[WorkloadSummary] = []
    for workload_type in sorted(by_workload):
        workload_prompts = by_workload[workload_type]
        split_counts = Counter(prompt["split"] for prompt in workload_prompts)
        planned_records = sum(
            len(prompt["planned_candidate_positions"]) for prompt in workload_prompts
        )
        summaries.append(
            WorkloadSummary(
                workload_type=workload_type,
                prompt_count=len(workload_prompts),
                planned_runtime_records=planned_records,
                split_counts=dict(sorted(split_counts.items())),
            )
        )
    return summaries


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _looks_private_or_secret(text: str) -> bool:
    lowered = text.lower()
    private_markers = {
        "api key",
        "bearer ",
        "client name",
        "password",
        "private key",
        "secret",
        "ssn",
    }
    return any(marker in lowered for marker in private_markers)
