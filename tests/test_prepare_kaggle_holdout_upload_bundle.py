from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


def load_module() -> Any:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / (
        "prepare_kaggle_holdout_upload_bundle.py"
    )
    spec = importlib.util.spec_from_file_location("prepare_holdout_upload_bundle", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def base_record(case_id: str, prompt_text: str, workload_type: str) -> dict[str, Any]:
    return {
        "allowed_use": [
            "kaggle_holdout_trace_collection",
            "candidate_calibrator_holdout_replay",
        ],
        "authoring_boundary": "authored_after_governance_before_holdout_outcomes",
        "case_id": case_id,
        "corpus_id": "v5-qwen-candidate-calibrator-independent-holdout-prompts-v1",
        "data_classification": "public_safe_self_authored_no_pii",
        "expected_trace_role": "holdout_evaluation_only",
        "forbidden_use": ["calibrator_refit", "threshold_tuning"],
        "prompt_text": prompt_text,
        "source_type": "self_authored",
        "split": "independent_holdout_candidate_calibrator_v1",
        "workload_type": workload_type,
    }


def write_manifest(module: Any, path: Path, corpus_path: Path, record_count: int) -> None:
    manifest = {
        "corpus_id": "v5-qwen-candidate-calibrator-independent-holdout-prompts-v1",
        "data_role": "independent_holdout_precollection",
        "prompt_corpus_sha256": module.sha256_file(corpus_path),
        "prompt_record_count": record_count,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_prepare_upload_bundle_writes_zip_and_manifest(tmp_path: Path) -> None:
    module = load_module()
    corpus_path = tmp_path / "holdout.jsonl"
    manifest_path = tmp_path / "manifest.json"
    output_dir = tmp_path / "bundle"
    rows = [
        base_record("KHOLD-001", "Summarize the onboarding checklist.", "structured_text"),
        base_record("KHOLD-002", "Write a Python function that doubles numbers.", "code"),
        base_record("KHOLD-003", "Explain why careful evidence matters.", "open_ended_chat"),
    ]
    write_jsonl(corpus_path, rows)
    write_manifest(module, manifest_path, corpus_path, len(rows))

    summary = module.prepare_upload_bundle(
        holdout_corpus_path=corpus_path,
        precollection_manifest_path=manifest_path,
        output_dir=output_dir,
        forbidden_corpus_paths=[],
    )

    zip_path = Path(summary.zip_path)
    assert zip_path.exists()
    assert summary.prompt_record_count == 3
    assert summary.duplicate_check_status == "passed_exact_normalized_prompt_checks"
    assert summary.allowed_next_step == "private_kaggle_holdout_trace_collection"
    assert (output_dir / "UPLOAD_BUNDLE_MANIFEST.json").exists()
    assert (output_dir / "KAGGLE_HOLDOUT_UPLOAD_README.md").exists()


def test_prepare_upload_bundle_rejects_duplicate_holdout_prompts(tmp_path: Path) -> None:
    module = load_module()
    corpus_path = tmp_path / "holdout.jsonl"
    manifest_path = tmp_path / "manifest.json"
    rows = [
        base_record("KHOLD-001", "Summarize the onboarding checklist.", "structured_text"),
        base_record("KHOLD-002", " summarize   THE onboarding checklist. ", "code"),
    ]
    write_jsonl(corpus_path, rows)
    write_manifest(module, manifest_path, corpus_path, len(rows))

    with pytest.raises(ValueError, match="duplicate normalized prompt_text"):
        module.prepare_upload_bundle(
            holdout_corpus_path=corpus_path,
            precollection_manifest_path=manifest_path,
            output_dir=tmp_path / "bundle",
            forbidden_corpus_paths=[],
        )


def test_prepare_upload_bundle_rejects_forbidden_reference_duplicates(tmp_path: Path) -> None:
    module = load_module()
    corpus_path = tmp_path / "holdout.jsonl"
    reference_path = tmp_path / "fit_pool.jsonl"
    manifest_path = tmp_path / "manifest.json"
    rows = [base_record("KHOLD-001", "Summarize the onboarding checklist.", "structured_text")]
    reference_rows = [
        {
            "case_id": "FIT-001",
            "prompt_text": " summarize   THE onboarding checklist. ",
        }
    ]
    write_jsonl(corpus_path, rows)
    write_jsonl(reference_path, reference_rows)
    write_manifest(module, manifest_path, corpus_path, len(rows))

    with pytest.raises(ValueError, match="duplicate forbidden/reference corpus"):
        module.prepare_upload_bundle(
            holdout_corpus_path=corpus_path,
            precollection_manifest_path=manifest_path,
            output_dir=tmp_path / "bundle",
            forbidden_corpus_paths=[reference_path],
        )


def test_holdout_prompt_record_rejects_outcome_fields() -> None:
    module = load_module()
    row = base_record("KHOLD-001", "Explain a safe holdout boundary.", "open_ended_chat")
    row["observed_acceptance"] = True

    with pytest.raises(ValueError, match="holdout prompt corpus must be label-free"):
        module.HoldoutPromptRecord.model_validate(row)
