from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "kaggle_trace_corpus_expansion_v1"
)
CORPUS_PATH = FIXTURE_DIR / "prompt_corpus.json"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"

ALLOWED_SPLITS = {"development", "calibration", "final_evaluation", "adversarial_regression"}
REQUIRED_WORKLOADS = {"structured_text", "code", "open_ended_chat"}
FORBIDDEN_PROMPT_KEYS = {
    "observed_acceptance",
    "prefix_survival_label",
    "conditional_acceptance_label",
    "target_probability",
    "target_argmax_match",
    "target_outcome",
    "calibration_result",
    "threshold_decision",
}
FORBIDDEN_TEXT_MARKERS = (
    "api_key",
    "apikey",
    "password",
    "secret",
    "token=",
    "bearer ",
    "client confidential",
    "private source code",
    "customer data",
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_prompt_corpus_manifest_hash_matches_retained_file() -> None:
    manifest = _load_json(MANIFEST_PATH)

    assert (
        manifest["corpus_path"]
        == "data/fixtures/kaggle_trace_corpus_expansion_v1/prompt_corpus.json"
    )
    assert manifest["prompt_corpus_sha256"] == _sha256(CORPUS_PATH)
    assert manifest["status"] == "planned_pre_collection_not_model_evidence"


def test_prompt_corpus_has_expected_planned_record_shape() -> None:
    corpus = _load_json(CORPUS_PATH)
    prompts = corpus["prompts"]
    planning = corpus["record_planning"]

    assert corpus["schema_version"] == "specsafe.kaggle_prompt_corpus.v1"
    assert corpus["corpus_status"] == "planned_pre_collection"
    assert corpus["data_role"] == "trace_collection"
    assert corpus["model_execution_status"] == "not_started"
    assert corpus["calibration_fit_status"] == "not_authorized"
    assert corpus["threshold_promotion_status"] == "not_authorized"

    assert len(prompts) == planning["planned_prompt_count"] == 30
    assert planning["planned_candidate_positions_per_prompt"] == 4
    assert planning["planned_runtime_records"] == 120
    assert (
        planning["planned_runtime_records"] >= planning["minimum_record_count_for_calibration_fit"]
    )
    assert planning["minimum_positive_count_for_calibration_fit"] == 30
    assert planning["minimum_negative_count_for_calibration_fit"] == 30
    assert planning["positive_negative_balance_status"] == "cannot_be_known_before_model_execution"

    planned_records_from_prompts = sum(
        len(prompt["planned_candidate_positions"]) for prompt in prompts
    )
    assert planned_records_from_prompts == planning["planned_runtime_records"]


def test_prompt_ids_and_prompt_families_are_unique_and_split_isolated() -> None:
    corpus = _load_json(CORPUS_PATH)
    prompts = corpus["prompts"]

    prompt_ids = [prompt["prompt_id"] for prompt in prompts]
    family_ids = [prompt["family_id"] for prompt in prompts]
    family_to_splits: dict[str, set[str]] = defaultdict(set)

    for prompt in prompts:
        family_to_splits[prompt["family_id"]].add(prompt["split"])

    assert len(prompt_ids) == len(set(prompt_ids))
    assert len(family_ids) == len(set(family_ids))
    assert all(len(splits) == 1 for splits in family_to_splits.values())


def test_prompt_corpus_preserves_split_and_workload_balance() -> None:
    corpus = _load_json(CORPUS_PATH)
    prompts = corpus["prompts"]

    split_counts = Counter(prompt["split"] for prompt in prompts)
    workload_counts = Counter(prompt["workload_type"] for prompt in prompts)
    workload_split_counts = Counter(
        (prompt["workload_type"], prompt["split"]) for prompt in prompts
    )

    assert set(split_counts) == ALLOWED_SPLITS
    assert split_counts == {
        "development": 9,
        "calibration": 9,
        "final_evaluation": 9,
        "adversarial_regression": 3,
    }
    assert set(workload_counts) == REQUIRED_WORKLOADS
    assert workload_counts == {"structured_text": 10, "code": 10, "open_ended_chat": 10}

    for workload in REQUIRED_WORKLOADS:
        assert workload_split_counts[(workload, "development")] == 3
        assert workload_split_counts[(workload, "calibration")] == 3
        assert workload_split_counts[(workload, "final_evaluation")] == 3
        assert workload_split_counts[(workload, "adversarial_regression")] == 1


def test_prompts_are_public_safe_and_do_not_contain_outcome_labels() -> None:
    corpus = _load_json(CORPUS_PATH)

    for prompt in corpus["prompts"]:
        assert prompt["source_type"] == "self_authored_public_safe"
        assert set(prompt).isdisjoint(FORBIDDEN_PROMPT_KEYS)
        assert prompt["planned_candidate_positions"] == [1, 2, 3, 4]
        assert EMAIL_PATTERN.search(prompt["prompt_text"]) is None

        prompt_text_lower = prompt["prompt_text"].lower()
        assert not any(marker in prompt_text_lower for marker in FORBIDDEN_TEXT_MARKERS)


def test_corpus_declares_no_threshold_or_public_release_promotion() -> None:
    corpus = _load_json(CORPUS_PATH)

    assert corpus["split_policy"]["split_unit"] == "prompt_family"
    assert corpus["split_policy"]["final_evaluation_may_influence_before_final_report"] is False
    assert corpus["split_policy"]["threshold_tuning_from_final_evaluation"] is False
    assert (
        "fit_kaggle_derived_calibrator_from_planned_corpus"
        in corpus["forbidden_downstream_actions"]
    )
    assert "promote_threshold_policy_from_planned_corpus" in corpus["forbidden_downstream_actions"]
    assert "claim_production_speedup_or_serving_readiness" in corpus["forbidden_downstream_actions"]
