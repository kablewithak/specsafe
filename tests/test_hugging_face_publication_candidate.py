from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.hugging_face_publication_candidate import (
    HuggingFacePublicationCandidateError,
    build_publication_candidate_payloads,
    check_committed_publication_candidate,
    write_publication_candidate,
)
from specsafe.hugging_face_publication_candidate.builder import (
    CANDIDATE_RELATIVE_DIRECTORY,
    SOURCE_READINESS_DECISION,
    SOURCE_RELEASE_DIRECTORY,
)
from specsafe.hugging_face_publication_candidate.models import (
    PublicationCandidateManifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY


def test_committed_publication_candidate_is_byte_canonical() -> None:
    check_committed_publication_candidate(PROJECT_ROOT)
    payloads = build_publication_candidate_payloads(PROJECT_ROOT)
    assert set(payloads) == {path.name for path in CANDIDATE_ROOT.iterdir()}
    for filename, expected in payloads.items():
        assert (CANDIDATE_ROOT / filename).read_bytes() == expected


def test_publication_manifest_retains_reviewed_sources_and_blocks_upload() -> None:
    manifest = PublicationCandidateManifest.model_validate_json(
        (CANDIDATE_ROOT / "publication_manifest.json").read_bytes()
    )
    assert manifest.validity_marker == "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"
    assert manifest.license_identifier == "cc-by-4.0"
    assert manifest.publication_status == "local_candidate_upload_not_authorized"
    assert manifest.public_upload_authorized is False
    assert manifest.source_readiness_decision.sha256 == (
        "51cf44163f1656a62035475ad217271046bc0cf6c8f21d12bff22f65a5341790"
    )
    assert manifest.source_release_manifest.sha256 == (
        "10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b"
    )
    assert manifest.gate_checks.public_upload_performed is False


def test_dataset_card_adds_only_reviewed_hub_metadata() -> None:
    source_readme = (PROJECT_ROOT / SOURCE_RELEASE_DIRECTORY / "README.md").read_bytes()
    candidate_readme = (CANDIDATE_ROOT / "README.md").read_bytes()
    metadata = (
        b"---\n"
        b"license: cc-by-4.0\n"
        b"pretty_name: SpecSafe Bounded Negative-Evidence Release v1\n"
        b"tags:\n"
        b"  - ai-reliability\n"
        b"  - calibration\n"
        b"  - evaluation\n"
        b"  - negative-results\n"
        b"  - governance\n"
        b"---\n\n"
    )
    assert candidate_readme.startswith(metadata)
    assert candidate_readme.removeprefix(metadata) == source_readme


def test_license_attribution_and_rollback_boundaries_are_prominent() -> None:
    license_text = (CANDIDATE_ROOT / "LICENSE.md").read_text(encoding="utf-8")
    attribution = (CANDIDATE_ROOT / "ATTRIBUTION.md").read_text(encoding="utf-8")
    rollback = (CANDIDATE_ROOT / "ROLLBACK.md").read_text(encoding="utf-8")

    assert "CC BY 4.0" in license_text
    assert "does not license" in license_text
    assert "SpecSafe source-code repository as a whole" in license_text
    assert "© 2026 Kabo Molefe" in attribution
    assert "reviewed metrics" in attribution
    assert "public_upload_authorized=false" in rollback
    assert "Unpublish procedure" in rollback
    assert "Revoke or rotate publishing credentials" in rollback


def test_final_sanitization_report_covers_exact_candidate_files() -> None:
    report = json.loads((CANDIDATE_ROOT / "sanitization_report.json").read_text(encoding="utf-8"))
    assert report["final_result"] == "PASS_LOCAL_CANDIDATE_ONLY"
    assert report["forbidden_marker_matches"] == 0
    assert report["public_upload_authorized"] is False
    assert report["scanned_file_count"] == 9
    assert all(report["checks"].values())


def test_manifest_contract_rejects_unknown_fields() -> None:
    value = json.loads((CANDIDATE_ROOT / "publication_manifest.json").read_text(encoding="utf-8"))
    value["unexpected"] = "field"
    with pytest.raises(ValidationError):
        PublicationCandidateManifest.model_validate(value)


def test_source_readiness_decision_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    decision_path = project / SOURCE_READINESS_DECISION
    value = json.loads(decision_path.read_text(encoding="utf-8"))
    value["public_upload_authorized"] = True
    decision_path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(HuggingFacePublicationCandidateError, match="reviewed bytes"):
        build_publication_candidate_payloads(project)


def test_reviewed_release_file_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    readme = project / SOURCE_RELEASE_DIRECTORY / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    with pytest.raises(HuggingFacePublicationCandidateError, match="reviewed bytes"):
        build_publication_candidate_payloads(project)


def test_write_rejects_output_outside_repository(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-publication-candidate"
    with pytest.raises(HuggingFacePublicationCandidateError, match="inside the repository"):
        write_publication_candidate(PROJECT_ROOT, output_directory=outside)


def test_write_rejects_existing_output(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    output = project / "candidate"
    output.mkdir()
    with pytest.raises(HuggingFacePublicationCandidateError, match="already exists"):
        write_publication_candidate(project, output_directory=output)


def test_check_rejects_unexpected_candidate_file(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path, include_candidate=True)
    candidate = project / CANDIDATE_RELATIVE_DIRECTORY
    (candidate / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(HuggingFacePublicationCandidateError, match="allowlist"):
        check_committed_publication_candidate(project)


def _copy_minimal_project(tmp_path: Path, *, include_candidate: bool = False) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")

    source_release = project / SOURCE_RELEASE_DIRECTORY
    source_release.parent.mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / SOURCE_RELEASE_DIRECTORY, source_release)

    decision = project / SOURCE_READINESS_DECISION
    decision.parent.mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / SOURCE_READINESS_DECISION, decision)

    if include_candidate:
        candidate = project / CANDIDATE_RELATIVE_DIRECTORY
        candidate.parent.mkdir(parents=True)
        shutil.copytree(CANDIDATE_ROOT, candidate)
    return project
