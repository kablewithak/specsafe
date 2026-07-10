from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.publication_readiness import (
    BoundedNegativeEvidencePublicationReadinessDecision,
    PublicationReadinessError,
    PublicationReadinessErrorCode,
    build_publication_readiness_decision,
)
from specsafe.publication_readiness.review import (
    DECISION_RELATIVE_PATH,
    EXPECTED_MANIFEST_SHA256,
    RELEASE_RELATIVE_DIRECTORY,
    canonical_publication_readiness_decision_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = PROJECT_ROOT / RELEASE_RELATIVE_DIRECTORY
RETAINED_DECISION_PATH = PROJECT_ROOT / DECISION_RELATIVE_PATH


@pytest.fixture
def short_project_root() -> Iterator[Path]:
    root = Path(tempfile.mkdtemp(prefix="ss-pub-"))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _copy_review_fixture(root: Path) -> Path:
    (root / "pyproject.toml").write_text("[project]\nname = 'specsafe-test'\n", encoding="utf-8")
    target = root / RELEASE_RELATIVE_DIRECTORY
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(RELEASE_ROOT, target)
    return target


def test_publication_readiness_decision_rebuild_is_byte_deterministic() -> None:
    decision = build_publication_readiness_decision(PROJECT_ROOT, write_output=False)
    assert canonical_publication_readiness_decision_json(decision) == (
        RETAINED_DECISION_PATH.read_bytes()
    )


def test_review_verifies_exact_pack_and_blocks_public_upload() -> None:
    decision = build_publication_readiness_decision(PROJECT_ROOT, write_output=False)
    assert decision.release_manifest.sha256 == EXPECTED_MANIFEST_SHA256
    assert decision.decision_outcome == "READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY"
    assert decision.publication_candidate_assembly_authorized is True
    assert decision.public_upload_authorized is False
    assert decision.gate_checks.public_upload_performed is False


def test_cc_by_license_is_scoped_to_sanitized_pack_only() -> None:
    decision = build_publication_readiness_decision(PROJECT_ROOT, write_output=False)
    license_decision = decision.license_decision
    assert license_decision.license_identifier == "cc-by-4.0"
    assert license_decision.license_scope == "sanitized_release_pack_original_materials_only"
    assert "specsafe_source_code_repository" in license_decision.excluded_scope
    assert "retained_kaggle_archives" in license_decision.excluded_scope
    assert "upstream_models_and_their_outputs" in license_decision.excluded_scope


def test_hugging_face_metadata_is_prepared_but_not_applied() -> None:
    decision = build_publication_readiness_decision(PROJECT_ROOT, write_output=False)
    metadata = decision.hugging_face_metadata_draft
    assert metadata.repository_type == "dataset"
    assert metadata.license == "cc-by-4.0"
    assert metadata.card_metadata_status == "prepared_not_applied"
    assert metadata.live_inference is False
    assert metadata.user_input_collection is False
    assert RELEASE_ROOT.joinpath("README.md").read_text(encoding="utf-8").startswith("# ")


def test_review_retains_non_promotion_and_next_control_boundary() -> None:
    decision = build_publication_readiness_decision(PROJECT_ROOT, write_output=False)
    assert decision.validity_marker == "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"
    assert "change_reviewed_metrics_or_claim_boundaries" in decision.blocked_actions
    assert "require_explicit_user_authorization_before_upload" in (decision.required_next_controls)
    assert decision.next_authorized_step == (
        "assemble_exact_hugging_face_publication_candidate_without_upload"
    )


def test_review_rejects_manifest_hash_drift(short_project_root: Path) -> None:
    release_root = _copy_review_fixture(short_project_root)
    manifest_path = release_root / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["publication_status"] = "public"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(PublicationReadinessError) as error:
        build_publication_readiness_decision(short_project_root, write_output=False)
    assert error.value.code is PublicationReadinessErrorCode.MANIFEST_INTEGRITY_FAILED


def test_review_rejects_release_file_hash_drift(short_project_root: Path) -> None:
    release_root = _copy_review_fixture(short_project_root)
    readme_path = release_root / "README.md"
    readme_path.write_text(
        readme_path.read_text(encoding="utf-8") + "\nchanged\n",
        encoding="utf-8",
    )

    with pytest.raises(PublicationReadinessError) as error:
        build_publication_readiness_decision(short_project_root, write_output=False)
    assert error.value.code is PublicationReadinessErrorCode.RELEASE_FILE_INTEGRITY_FAILED


def test_review_rejects_unexpected_release_file(short_project_root: Path) -> None:
    release_root = _copy_review_fixture(short_project_root)
    (release_root / "raw_traces.jsonl").write_text("{}\n", encoding="utf-8")

    with pytest.raises(PublicationReadinessError) as error:
        build_publication_readiness_decision(short_project_root, write_output=False)
    assert error.value.code is PublicationReadinessErrorCode.RELEASE_DIRECTORY_INVALID


def test_decision_contract_rejects_unknown_fields() -> None:
    decision = build_publication_readiness_decision(PROJECT_ROOT, write_output=False)
    payload = decision.model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        BoundedNegativeEvidencePublicationReadinessDecision.model_validate(payload)
