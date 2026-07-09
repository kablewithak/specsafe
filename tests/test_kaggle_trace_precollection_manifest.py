from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from specsafe.kaggle_trace_collection.precollection_manifest import (
    SOURCE_CORPUS_PATH,
    build_precollection_manifest,
    load_json,
    sha256_file,
    write_precollection_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "fixtures" / "kaggle_trace_corpus_expansion_v1" / "prompt_corpus.json"
RETAINED_MANIFEST_PATH = (
    ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "pre-collection"
    / "pre_collection_manifest.json"
)


def _build_manifest_from_fixture():
    return build_precollection_manifest(
        load_json(CORPUS_PATH),
        source_corpus_path=SOURCE_CORPUS_PATH,
        source_corpus_sha256=sha256_file(CORPUS_PATH),
    )


def test_precollection_manifest_preserves_no_model_execution_boundary() -> None:
    manifest = _build_manifest_from_fixture()

    assert manifest.schema_version == "specsafe.kaggle_precollection_manifest.v1"
    assert manifest.manifest_id == "v5-qwen-governed-trace-collection-v2-precollection"
    assert manifest.corpus_id == "kaggle_trace_corpus_expansion_v1"
    assert manifest.data_role == "trace_collection"
    assert manifest.evidence_class == "kaggle_environment_planned"
    assert manifest.model_execution_status == "not_started"
    assert manifest.collection_status == "pre_collection_ready"
    assert manifest.calibration_fit_status == "not_authorized"
    assert manifest.threshold_promotion_status == "not_authorized"


def test_precollection_manifest_locks_corpus_hash_and_record_plan() -> None:
    manifest = _build_manifest_from_fixture()

    assert manifest.source_corpus_path == SOURCE_CORPUS_PATH
    assert manifest.source_corpus_sha256 == sha256_file(CORPUS_PATH)
    assert manifest.record_plan.planned_prompt_count == 30
    assert manifest.record_plan.planned_candidate_positions_per_prompt == 4
    assert manifest.record_plan.planned_runtime_records == 120
    assert manifest.record_plan.minimum_record_count_for_calibration_fit == 100
    assert manifest.record_plan.minimum_positive_count_for_calibration_fit == 30
    assert manifest.record_plan.minimum_negative_count_for_calibration_fit == 30


def test_precollection_manifest_summarizes_splits_and_workloads() -> None:
    manifest = _build_manifest_from_fixture()

    split_counts = {item.split: item.prompt_count for item in manifest.split_summary}
    split_records = {item.split: item.planned_runtime_records for item in manifest.split_summary}
    workload_counts = {item.workload_type: item.prompt_count for item in manifest.workload_summary}

    assert split_counts == {
        "adversarial_regression": 3,
        "calibration": 9,
        "development": 9,
        "final_evaluation": 9,
    }
    assert split_records == {
        "adversarial_regression": 12,
        "calibration": 36,
        "development": 36,
        "final_evaluation": 36,
    }
    assert workload_counts == {
        "code": 10,
        "open_ended_chat": 10,
        "structured_text": 10,
    }


def test_precollection_manifest_blocks_forbidden_downstream_actions() -> None:
    manifest = _build_manifest_from_fixture()

    assert "fit_kaggle_derived_calibrator_from_planned_corpus" in (
        manifest.forbidden_downstream_actions
    )
    assert "promote_threshold_policy_from_planned_corpus" in (manifest.forbidden_downstream_actions)
    assert "promote_scheduler_utility_from_planned_corpus" in (
        manifest.forbidden_downstream_actions
    )
    assert manifest.pre_collection_gates == {
        "no_calibration_fit": "passed",
        "no_outcome_labels": "passed",
        "no_threshold_promotion": "passed",
        "planned_record_count_minimum": "passed",
        "prompt_family_split_isolation": "passed",
        "public_safe_source_policy": "passed",
    }


def test_precollection_manifest_rejects_prompt_family_split_leakage() -> None:
    corpus = load_json(CORPUS_PATH)
    modified = copy.deepcopy(corpus)
    modified["prompts"][1]["family_id"] = modified["prompts"][0]["family_id"]
    modified["prompts"][1]["split"] = "final_evaluation"

    with pytest.raises(ValueError, match="prompt family leaks across splits"):
        build_precollection_manifest(
            modified,
            source_corpus_path=SOURCE_CORPUS_PATH,
            source_corpus_sha256="irrelevant",
        )


def test_precollection_manifest_rejects_outcome_label_fields() -> None:
    corpus = load_json(CORPUS_PATH)
    modified = copy.deepcopy(corpus)
    modified["prompts"][0]["target_probability"] = 0.9

    with pytest.raises(ValueError, match="forbidden outcome/execution fields"):
        build_precollection_manifest(
            modified,
            source_corpus_path=SOURCE_CORPUS_PATH,
            source_corpus_sha256="irrelevant",
        )


def test_retained_manifest_matches_deterministic_writer(tmp_path: Path) -> None:
    manifest = _build_manifest_from_fixture()
    output_path = tmp_path / "pre_collection_manifest.json"

    write_precollection_manifest(manifest, output_path)

    assert json.loads(RETAINED_MANIFEST_PATH.read_text(encoding="utf-8")) == json.loads(
        output_path.read_text(encoding="utf-8")
    )
    assert RETAINED_MANIFEST_PATH.read_text(encoding="utf-8").endswith("\n")
