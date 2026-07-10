from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.hugging_face_dataset_publication import (
    PublicationReceiptVerificationError,
    check_committed_publication_receipt,
)
from specsafe.hugging_face_dataset_publication.receipt_verification import (
    CANDIDATE_RELATIVE_DIRECTORY,
    EXPECTED_FILES,
    EXPECTED_PUBLISHED_REVISION,
    EXPECTED_RECEIPT_BYTE_COUNT,
    EXPECTED_RECEIPT_SHA256,
    RECEIPT_RELATIVE_PATH,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_committed_publication_receipt_is_canonical() -> None:
    receipt = check_committed_publication_receipt(PROJECT_ROOT)
    assert receipt.repository_id == ("KaboKableMolefe/specsafe-bounded-negative-evidence-v1")
    assert receipt.published_revision == EXPECTED_PUBLISHED_REVISION


def test_receipt_retains_public_anonymous_verification() -> None:
    receipt = check_committed_publication_receipt(PROJECT_ROOT)
    assert receipt.final_visibility == "public"
    assert receipt.gated is False
    assert receipt.private_stage_verified is True
    assert receipt.anonymous_public_verification_passed is True
    assert receipt.rollback_triggered is False


def test_receipt_hash_and_byte_count_match_uploaded_artifact() -> None:
    import hashlib

    payload = (PROJECT_ROOT / RECEIPT_RELATIVE_PATH).read_bytes()
    assert len(payload) == EXPECTED_RECEIPT_BYTE_COUNT
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_RECEIPT_SHA256


def test_receipt_file_hashes_match_exact_local_candidate() -> None:
    receipt = check_committed_publication_receipt(PROJECT_ROOT)
    assert receipt.published_file_hashes == EXPECTED_FILES
    assert receipt.remote_files == tuple(item.relative_path for item in EXPECTED_FILES)


def test_receipt_contains_no_credential_material() -> None:
    payload = (PROJECT_ROOT / RECEIPT_RELATIVE_PATH).read_bytes().lower()
    for marker in (b"authorization: bearer", b"access_token", b"api_key", b"hf_token"):
        assert marker not in payload


def test_receipt_byte_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    receipt_path.write_bytes(receipt_path.read_bytes() + b"\n")
    with pytest.raises(PublicationReceiptVerificationError, match="byte count"):
        check_committed_publication_receipt(project)


def test_receipt_identity_drift_is_rejected_by_integrity_gate(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    value = json.loads(receipt_path.read_text(encoding="utf-8"))
    value["namespace"] = "OtherNamespace"
    receipt_path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(PublicationReceiptVerificationError, match="SHA-256"):
        check_committed_publication_receipt(project)


def test_local_candidate_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    readme = project / CANDIDATE_RELATIVE_DIRECTORY / "README.md"
    readme.write_bytes(readme.read_bytes() + b"drift")
    with pytest.raises(PublicationReceiptVerificationError, match="README.md"):
        check_committed_publication_receipt(project)


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")

    receipt = project / RECEIPT_RELATIVE_PATH
    receipt.parent.mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / RECEIPT_RELATIVE_PATH, receipt)

    candidate = project / CANDIDATE_RELATIVE_DIRECTORY
    candidate.parent.mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY, candidate)
    return project
