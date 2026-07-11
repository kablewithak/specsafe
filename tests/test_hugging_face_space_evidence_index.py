from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.hugging_face_space_evidence import (
    HuggingFaceSpaceEvidenceError,
    HuggingFaceSpaceEvidenceIndex,
    build_space_evidence_index,
    build_space_evidence_payloads,
    check_committed_space_evidence_index,
)
from specsafe.hugging_face_space_evidence.builder import (
    COMPARISON_RELATIVE_PATH,
    DATASET_RECEIPT_RELATIVE_PATH,
    INDEX_FILENAME,
    OUTPUT_RELATIVE_DIRECTORY,
    RELEASE_SUMMARY_RELATIVE_PATH,
    _utility_matches,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / OUTPUT_RELATIVE_DIRECTORY


def test_committed_space_evidence_index_is_canonical() -> None:
    check_committed_space_evidence_index(PROJECT_ROOT)
    payloads = build_space_evidence_payloads(PROJECT_ROOT)
    assert set(payloads) == {"evidence_index.json", "evidence_manifest.json"}
    for filename, payload in payloads.items():
        assert (OUTPUT_ROOT / filename).read_bytes() == payload


def test_index_retains_plain_language_story_and_read_only_boundary() -> None:
    index = build_space_evidence_index(PROJECT_ROOT)
    assert index.space_repository_name == "specsafe-reliability-lab"
    assert "helped under some conditions" in index.quick_summary
    assert index.read_only is True
    assert index.live_inference is False
    assert index.user_input_collection is False
    assert tuple(section.section_id for section in index.sections) == (
        "overview",
        "what_was_tested",
        "policy_results",
        "capacity_conditions",
        "confidence_gate",
        "what_it_means",
        "evidence",
    )


def test_utility_comparison_accepts_serialization_noise_only() -> None:
    assert _utility_matches(-7.800000000000001, -7.8)
    assert _utility_matches(3.6000000000000005, 3.6)


def test_utility_comparison_rejects_material_drift() -> None:
    assert not _utility_matches(-7.800001, -7.8)
    assert not _utility_matches(3.61, 3.6)


def test_index_retains_mixed_policy_results() -> None:
    index = build_space_evidence_index(PROJECT_ROOT)
    assert index.adaptive_vs_fixed.model_dump() == {
        "adaptive_higher": 2,
        "neutral": 3,
        "adaptive_lower": 1,
    }
    assert index.adaptive_vs_threshold.model_dump() == {
        "adaptive_higher": 3,
        "neutral": 2,
        "adaptive_lower": 1,
    }
    by_id = {case.case_id: case for case in index.cases}
    assert by_id["MPC5-103"].adaptive_utility == 0.0
    assert by_id["MPC5-103"].fixed_utility == 1.0
    assert by_id["MPC5-104"].adaptive_utility == 0.0
    assert by_id["MPC5-104"].fixed_utility == -13.0
    assert by_id["MPC5-106"].adaptive_vs_threshold == "adaptive_higher_utility"


def test_index_retains_causal_safety_boundary() -> None:
    index = build_space_evidence_index(PROJECT_ROOT)
    assert index.valid_causal_comparisons == 6
    assert index.unsafe_retrospective_controls_excluded == 6
    assert index.unsafe_controls_failed_causal_safety is True
    assert "No global policy winner is established." in index.non_claims


def test_index_retains_failed_confidence_gate() -> None:
    gate = build_space_evidence_index(PROJECT_ROOT).calibration_gate
    assert gate.holdout_record_count == 192
    assert gate.decision_outcome == "KEEP_DIAGNOSTIC_ONLY"
    assert gate.failure_label == "ranking_safety_regression"
    assert gate.observed_auroc_delta == pytest.approx(-0.024356617647058765)
    assert gate.degradation_multiple_of_limit == pytest.approx(24.356617647058765)
    assert gate.metrics[0].gate_result == "improved"
    assert gate.metrics[1].gate_result == "improved"
    assert gate.metrics[2].gate_result == "failed_ranking_safety"


def test_index_retains_verified_public_dataset_identity() -> None:
    publication = build_space_evidence_index(PROJECT_ROOT).dataset_publication
    assert publication.repository_id == (
        "KaboKableMolefe/specsafe-bounded-negative-evidence-v1"
    )
    assert publication.published_revision == (
        "1ff151fc0646102f6e7b107d1bceb9a18e50098a"
    )
    assert publication.public is True
    assert publication.gated is False
    assert publication.anonymous_verification_passed is True


def test_index_contract_rejects_unknown_fields() -> None:
    value = json.loads((OUTPUT_ROOT / INDEX_FILENAME).read_text(encoding="utf-8"))
    value["unexpected"] = True
    with pytest.raises(ValidationError):
        HuggingFaceSpaceEvidenceIndex.model_validate(value)


def test_repository_readme_reconciles_publication_status() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Bounded public negative-evidence pack | Published and verified" in readme
    assert "Hugging Face Space evidence index | Complete locally" in readme
    assert (
        "Hugging Face Space interface | Implemented locally; publication pending"
    ) in readme
    assert (
        "Hugging Face Space publication candidate | Frozen locally; upload pending"
    ) in readme
    assert (
        "hugging_face_space_status=publication_candidate_frozen_remote_upload_pending"
    ) in readme


def test_source_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    summary = project / RELEASE_SUMMARY_RELATIVE_PATH
    summary.write_bytes(summary.read_bytes() + b"drift")
    with pytest.raises(HuggingFaceSpaceEvidenceError, match="SHA-256 mismatch"):
        build_space_evidence_index(project)


def test_committed_output_rejects_unexpected_file(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    output = project / OUTPUT_RELATIVE_DIRECTORY
    output.mkdir(parents=True)
    for filename, payload in build_space_evidence_payloads(project).items():
        (output / filename).write_bytes(payload)
    (output / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(HuggingFaceSpaceEvidenceError, match="allowlist"):
        check_committed_space_evidence_index(project)


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")
    for relative_path in (
        COMPARISON_RELATIVE_PATH,
        RELEASE_SUMMARY_RELATIVE_PATH,
        DATASET_RECEIPT_RELATIVE_PATH,
    ):
        target = project / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative_path, target)
    return project
