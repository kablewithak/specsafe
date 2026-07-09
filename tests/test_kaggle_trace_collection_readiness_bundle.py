from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRE_COLLECTION_PATH = ROOT / (
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/"
    "pre-collection/pre_collection_manifest.json"
)
BUNDLE_PATH = ROOT / (
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/"
    "readiness/collection_readiness_bundle.json"
)
SCRIPT_PATH = ROOT / "scripts/prepare_kaggle_trace_collection_readiness_bundle.py"
NOTEBOOK_PATH = ROOT / ("notebooks/kaggle/specsafe_v5_qwen_trace_collection_v2_readiness.ipynb")
README_PATH = ROOT / "notebooks/kaggle/specsafe_v5_qwen_trace_collection_v2_README.md"


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_script_writes_deterministic_readiness_bundle() -> None:
    before = BUNDLE_PATH.read_bytes()

    subprocess.run([sys.executable, str(SCRIPT_PATH)], cwd=ROOT, check=True)

    after = BUNDLE_PATH.read_bytes()
    assert after == before
    assert after.endswith(b"\n")


def test_readiness_bundle_locks_pre_collection_manifest() -> None:
    bundle = _load_json(BUNDLE_PATH)
    pre_collection = _load_json(PRE_COLLECTION_PATH)

    assert bundle["schema_version"] == "specsafe.kaggle_trace_collection_readiness.v1"
    assert bundle["collection_id"] == "v5-qwen-governed-trace-collection-v2"
    assert bundle["source_pre_collection_manifest_sha256"] == _sha256(PRE_COLLECTION_PATH)
    assert bundle["source_pre_collection_manifest_id"] == pre_collection["manifest_id"]
    assert bundle["source_corpus_sha256"] == pre_collection["source_corpus_sha256"]


def test_readiness_bundle_is_not_model_execution_or_calibration_evidence() -> None:
    bundle = _load_json(BUNDLE_PATH)

    assert bundle["data_role"] == "trace_collection_readiness"
    assert bundle["evidence_class"] == "kaggle_environment_planned"
    assert bundle["model_execution_status"] == "not_started"
    assert bundle["notebook_execution_status"] == "not_started"
    assert bundle["calibration_fit_status"] == "not_authorized"
    assert bundle["threshold_promotion_status"] == "not_authorized"
    assert "not_model_execution_evidence" in bundle["non_claims"]
    assert "not_production_serving_evidence" in bundle["non_claims"]


def test_readiness_bundle_preserves_record_and_split_plan() -> None:
    bundle = _load_json(BUNDLE_PATH)

    assert bundle["planned_runtime_records"] == 120
    assert bundle["minimum_record_count_for_calibration_fit"] == 100
    assert bundle["minimum_positive_count_for_calibration_fit"] == 30
    assert bundle["minimum_negative_count_for_calibration_fit"] == 30
    assert bundle["prompt_family_assignment_count"] == 30

    split_names = {entry["split"] for entry in bundle["split_summary"]}
    workload_names = {entry["workload_type"] for entry in bundle["workload_summary"]}

    assert split_names == {
        "adversarial_regression",
        "calibration",
        "development",
        "final_evaluation",
    }
    assert workload_names == {"code", "open_ended_chat", "structured_text"}


def test_output_artifact_allowlist_excludes_downstream_promotion() -> None:
    bundle = _load_json(BUNDLE_PATH)

    assert "runtime_records.jsonl" in bundle["allowed_output_artifacts"]
    assert "expected_outcomes.jsonl" in bundle["allowed_output_artifacts"]
    assert "kaggle_derived_calibrator.json" in bundle["forbidden_output_artifacts"]
    assert "promoted_threshold_policy.json" in bundle["forbidden_output_artifacts"]
    assert "production_speedup_report.json" in bundle["forbidden_output_artifacts"]


def test_readiness_notebook_is_clean_and_non_executed() -> None:
    notebook = _load_json(NOTEBOOK_PATH)

    assert notebook["nbformat"] == 4
    assert notebook["cells"]
    serialized = json.dumps(notebook, sort_keys=True)
    assert "collection_readiness_bundle.json" in serialized
    assert "calibration_fit_status" in serialized
    assert "threshold_promotion_status" in serialized
    assert "AutoModel" not in serialized
    assert "from_pretrained" not in serialized

    for cell in notebook["cells"]:
        assert cell.get("outputs", []) == []
        assert cell.get("execution_count") is None


def test_readme_states_readiness_boundary() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "readiness bundle" in readme
    assert "does not run model inference" in readme
    assert "does not fit a Kaggle-derived calibrator" in readme
    assert "does not promote thresholds" in readme
    assert "production speedup" in readme
