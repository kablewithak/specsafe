from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "kaggle_negative_case_expansion_v1"
)
CORPUS_PATH = FIXTURE_DIR / "prompt_corpus.json"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
LEDGER_PATH = FIXTURE_DIR / "authoring_ledger.md"

ALLOWED_SPLITS = {
    "negative_probe_calibration_candidate",
    "negative_probe_holdout",
}
ALLOWED_WORKLOAD_TYPES = {"open_ended_chat", "code", "structured_text"}
FORBIDDEN_FIELD_NAMES = {
    "target_argmax_token_id",
    "target_probability",
    "target_entropy",
    "observed_acceptance",
    "conditional_acceptance_label",
    "prefix_survival_label",
    "calibration_fit_result",
    "promoted_threshold",
}
FORBIDDEN_TEXT_MARKERS = {
    "api_key",
    "apikey",
    "bearer ",
    "client transcript",
    "password",
    "private key",
    "secret",
    "token=",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for nested_value in value.values():
            keys.update(_walk_keys(nested_value))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_walk_keys(item))
        return keys
    return set()


def test_manifest_hash_and_shape_match_prompt_corpus() -> None:
    manifest = _load_json(MANIFEST_PATH)

    assert manifest["corpus_id"] == "kaggle_negative_case_expansion_v1"
    assert manifest["data_role"] == "negative_case_trace_collection_planning"
    assert manifest["status"] == "planned_pre_collection_not_model_evidence"
    assert manifest["corpus_path"] == (
        "data/fixtures/kaggle_negative_case_expansion_v1/prompt_corpus.json"
    )
    assert manifest["prompt_corpus_sha256"] == _sha256(CORPUS_PATH)
    assert manifest["source_corpus_sha256"] == manifest["prompt_corpus_sha256"]
    assert manifest["planned_prompt_count"] == 16
    assert manifest["planned_candidate_positions_per_prompt"] == 4
    assert manifest["planned_runtime_records"] == 64


def test_negative_case_planning_counts_and_prior_diagnostic_boundary() -> None:
    corpus = _load_json(CORPUS_PATH)
    prompts = corpus["prompts"]
    planning = corpus["planning"]
    prior = corpus["prior_diagnostic_summary"]

    assert len(prompts) == 16
    assert planning["planned_prompt_count"] == 16
    assert planning["planned_candidate_positions_per_prompt"] == 4
    assert planning["planned_runtime_records"] == 64
    assert planning["minimum_additional_negative_records_needed"] == 7
    assert prior["v2_observed_record_count"] == 120
    assert prior["v2_observed_positive_count"] == 97
    assert prior["v2_observed_negative_count"] == 23
    assert prior["minimum_negative_count_for_calibration_fit"] == 30
    assert prior["calibration_fit_authorized"] is False
    assert prior["readiness_status"] == (
        "insufficient_negative_count_for_calibration_fit_signal_supportive"
    )

    planned_records_from_prompts = sum(
        len(prompt["planned_candidate_positions"]) for prompt in prompts
    )
    assert planned_records_from_prompts == planning["planned_runtime_records"]


def test_prompt_family_split_isolation_and_workload_balance() -> None:
    corpus = _load_json(CORPUS_PATH)
    prompts = corpus["prompts"]

    family_to_splits: dict[str, set[str]] = defaultdict(set)
    split_counts = Counter(prompt["split"] for prompt in prompts)
    workload_counts = Counter(prompt["workload_type"] for prompt in prompts)

    for prompt in prompts:
        family_to_splits[prompt["family_id"]].add(prompt["split"])
        assert prompt["split"] in ALLOWED_SPLITS
        assert prompt["workload_type"] in ALLOWED_WORKLOAD_TYPES
        assert prompt["source_type"] == "self_authored_public_safe"
        assert prompt["planned_candidate_positions"] == [1, 2, 3, 4]

    assert all(len(splits) == 1 for splits in family_to_splits.values())
    assert split_counts == {
        "negative_probe_calibration_candidate": 8,
        "negative_probe_holdout": 8,
    }
    assert workload_counts == {
        "open_ended_chat": 6,
        "code": 6,
        "structured_text": 4,
    }


def test_corpus_contains_no_outcome_labels_or_promotion_fields() -> None:
    corpus = _load_json(CORPUS_PATH)
    keys = _walk_keys(corpus)

    assert keys.isdisjoint(FORBIDDEN_FIELD_NAMES)
    assert corpus["split_policy"]["threshold_tuning_from_this_corpus"] is False
    assert corpus["split_policy"]["calibration_fit_from_planned_corpus"] is False
    assert corpus["split_policy"]["post_collection_role_requires_diagnostic_gate"] is True
    assert (
        "fit_kaggle_derived_calibrator_from_planned_corpus"
        in corpus["forbidden_downstream_actions"]
    )
    assert "promote_threshold_policy_from_planned_corpus" in corpus["forbidden_downstream_actions"]
    assert "claim_production_speedup_or_serving_readiness" in corpus["forbidden_downstream_actions"]


def test_prompts_are_public_safe_and_self_authored() -> None:
    corpus = _load_json(CORPUS_PATH)
    for prompt in corpus["prompts"]:
        prompt_text = prompt["prompt_text"]
        prompt_text_lower = prompt_text.lower()

        for marker in FORBIDDEN_TEXT_MARKERS:
            assert marker not in prompt_text_lower
        assert len(prompt_text) <= 220
        assert "@" not in prompt_text
        assert not re.search(r"\d{10,}", prompt_text)
        assert prompt["source_type"] == "self_authored_public_safe"

    privacy = corpus["privacy_controls"]
    assert privacy["raw_private_prompts_allowed"] is False
    assert privacy["client_data_allowed"] is False
    assert privacy["secrets_allowed"] is False
    assert privacy["pii_allowed"] is False
    assert privacy["public_release_authorized"] is False


def test_authoring_ledger_records_non_claim_boundary() -> None:
    ledger = LEDGER_PATH.read_text(encoding="utf-8")

    assert "observed_negative_count=23" in ledger
    assert "calibration_fit_authorized=false" in ledger
    assert "planned_runtime_records=64" in ledger
    assert "Do not use this corpus" in ledger
    assert "production readiness" in ledger
