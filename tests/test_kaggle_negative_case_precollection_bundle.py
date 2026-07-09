from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from specsafe.kaggle_trace_collection.negative_case_precollection_bundle import (
    PRE_COLLECTION_PATH,
    READINESS_BUNDLE_PATH,
    SOURCE_CORPUS_PATH,
    SOURCE_MANIFEST_PATH,
    build_negative_case_precollection_manifest,
    build_negative_case_readiness_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _generated_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        build_negative_case_precollection_manifest(REPO_ROOT),
        build_negative_case_readiness_bundle(REPO_ROOT),
    )


def test_retained_reports_match_deterministic_generation() -> None:
    generated_manifest, generated_readiness = _generated_reports()

    retained_manifest = _load_json(REPO_ROOT / PRE_COLLECTION_PATH)
    retained_readiness = _load_json(REPO_ROOT / READINESS_BUNDLE_PATH)

    assert retained_manifest == generated_manifest
    assert retained_readiness == generated_readiness


def test_precollection_manifest_locks_source_corpus_and_prior_gate() -> None:
    manifest = _load_json(REPO_ROOT / PRE_COLLECTION_PATH)
    source_manifest = _load_json(REPO_ROOT / SOURCE_MANIFEST_PATH)

    assert manifest["collection_id"] == "v5-qwen-negative-case-expansion-v1"
    assert manifest["attempt_id"] == "attempt-001-t4"
    assert manifest["source_corpus_id"] == "kaggle_negative_case_expansion_v1"
    assert manifest["source_corpus_sha256"] == _sha256(REPO_ROOT / SOURCE_CORPUS_PATH)
    assert manifest["source_manifest_sha256"] == _sha256(REPO_ROOT / SOURCE_MANIFEST_PATH)
    assert (
        manifest["source_manifest_declared_corpus_sha256"]
        == source_manifest["source_corpus_sha256"]
    )
    assert manifest["v2_observed_negative_count"] == 23
    assert manifest["target_minimum_negative_count_for_calibration_fit"] == 30
    assert manifest["v2_calibration_fit_authorized"] is False


def test_readiness_bundle_locks_precollection_manifest() -> None:
    readiness = _load_json(REPO_ROOT / READINESS_BUNDLE_PATH)

    assert readiness["readiness_status"] == "ready_for_private_kaggle_t4_collection"
    assert readiness["pre_collection_manifest_path"] == PRE_COLLECTION_PATH.as_posix()
    assert readiness["pre_collection_manifest_sha256"] == _sha256(REPO_ROOT / PRE_COLLECTION_PATH)
    assert readiness["source_corpus_sha256"] == _sha256(REPO_ROOT / SOURCE_CORPUS_PATH)
    assert readiness["source_manifest_sha256"] == _sha256(REPO_ROOT / SOURCE_MANIFEST_PATH)


def test_planned_counts_and_stratification_are_preserved() -> None:
    manifest = _load_json(REPO_ROOT / PRE_COLLECTION_PATH)

    assert manifest["planned_prompt_count"] == 16
    assert manifest["planned_candidate_positions_per_prompt"] == 4
    assert manifest["planned_runtime_records"] == 64
    assert manifest["minimum_additional_negative_records_needed"] == 7
    assert sum(manifest["split_counts"].values()) == 16
    assert sum(manifest["workload_counts"].values()) == 16
    assert len(manifest["family_counts"]) == 16


def test_no_runtime_or_promotion_claims_are_authorized() -> None:
    manifest = _load_json(REPO_ROOT / PRE_COLLECTION_PATH)
    readiness = _load_json(REPO_ROOT / READINESS_BUNDLE_PATH)

    for report in (manifest, readiness):
        assert report["model_execution_status"] == "not_started"
        assert report["notebook_execution_status"] == "not_started"
        assert report["calibration_fit_status"] == "not_authorized"
        assert report["threshold_promotion_status"] == "not_authorized"
        assert report["scheduler_promotion_status"] == "not_authorized"
        assert report["public_release_status"] == "not_authorized"
        assert report["production_claim_status"] == "not_authorized"
        assert (
            "fit_kaggle_derived_calibrator_from_planned_corpus"
            in report["forbidden_downstream_actions"]
        )


def test_readiness_controls_are_private_and_collection_only() -> None:
    readiness = _load_json(REPO_ROOT / READINESS_BUNDLE_PATH)

    assert readiness["kaggle_dataset_visibility_required"] == "private"
    assert readiness["internet_required_for_model_download"] is True
    assert readiness["planned_output_archive"] == (
        "specsafe_v5_qwen_negative_case_expansion_v1_attempt_001_t4.zip"
    )
    assert "private_input_dataset" in readiness["required_kaggle_controls"]
    assert "gpu_t4_accelerator" in readiness["required_kaggle_controls"]
    assert "no_calibration_fit" in readiness["required_kaggle_controls"]
    assert "no_threshold_promotion" in readiness["required_kaggle_controls"]
