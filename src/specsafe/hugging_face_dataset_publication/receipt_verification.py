from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from .models import FileDigest, PublicationReceipt

RECEIPT_RELATIVE_PATH = (
    "evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/"
    "hugging_face_dataset_publication_receipt.json"
)
CANDIDATE_RELATIVE_DIRECTORY = "release/hugging-face/specsafe-bounded-negative-evidence-v1"
EXPECTED_RECEIPT_SHA256 = "a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7"
EXPECTED_RECEIPT_BYTE_COUNT = 2834
EXPECTED_REPOSITORY_ID = "KaboKableMolefe/specsafe-bounded-negative-evidence-v1"
EXPECTED_REPOSITORY_URL = (
    "https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1"
)
EXPECTED_PUBLISHED_REVISION = "1ff151fc0646102f6e7b107d1bceb9a18e50098a"
EXPECTED_PUBLISHED_AT = "2026-07-10T22:46:44.611965Z"
EXPECTED_PUBLICATION_MANIFEST_SHA256 = (
    "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
)
EXPECTED_FILES = (
    FileDigest(
        relative_path="ATTRIBUTION.md",
        sha256="738543559f774c1f1375c9a5dda5d6b7a3f810ff00b2115c9590c7564997b97e",
        byte_count=844,
    ),
    FileDigest(
        relative_path="LICENSE.md",
        sha256="cdc0049740d46ff125ef50d5274dc64e807fa918e2eaa4c67371864294ed5d59",
        byte_count=872,
    ),
    FileDigest(
        relative_path="README.md",
        sha256="068764747dcb25a90190237f1230d5965a97c33ab13b0398104a5cd4aa6c74f4",
        byte_count=3187,
    ),
    FileDigest(
        relative_path="ROLLBACK.md",
        sha256="96d901ae36bc50e6d5265cbbad7b3ad45c880a85601395d70a9d9dbe839fc1a3",
        byte_count=1611,
    ),
    FileDigest(
        relative_path="evidence_boundary.md",
        sha256="8053d6c01a816280847b79d8bc036f14733dd7bc2d12f27bedf35934ef166967",
        byte_count=1577,
    ),
    FileDigest(
        relative_path="publication_manifest.json",
        sha256=EXPECTED_PUBLICATION_MANIFEST_SHA256,
        byte_count=4135,
    ),
    FileDigest(
        relative_path="release_summary.json",
        sha256="264886c6bb6d2490bb95b43a29506b04437972e5a42c6688db7dc7d124f8df90",
        byte_count=4470,
    ),
    FileDigest(
        relative_path="sanitization_report.json",
        sha256="863666570e1fcc4d6113bf5943812bb72b4d32862c727d7fd49cc73ad57c8c5c",
        byte_count=1278,
    ),
    FileDigest(
        relative_path="source_release_manifest.json",
        sha256="10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b",
        byte_count=975,
    ),
)
_FORBIDDEN_RECEIPT_MARKERS = (
    b"authorization: bearer",
    b"access_token",
    b"api_key",
    b"hf_token",
    b"secret",
)


class PublicationReceiptVerificationErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_receipt_invalid_project_root"
    RECEIPT_MISSING = "hf_receipt_missing"
    RECEIPT_INTEGRITY_FAILED = "hf_receipt_integrity_failed"
    RECEIPT_SCHEMA_INVALID = "hf_receipt_schema_invalid"
    RECEIPT_IDENTITY_INVALID = "hf_receipt_identity_invalid"
    RECEIPT_GATE_INVALID = "hf_receipt_gate_invalid"
    RECEIPT_FILE_SET_INVALID = "hf_receipt_file_set_invalid"
    CANDIDATE_INTEGRITY_FAILED = "hf_receipt_candidate_integrity_failed"
    RECEIPT_SECRET_MARKER_DETECTED = "hf_receipt_secret_marker_detected"


class PublicationReceiptVerificationError(ValueError):
    def __init__(
        self,
        code: PublicationReceiptVerificationErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


def check_committed_publication_receipt(project_root: Path | str) -> PublicationReceipt:
    root = _require_project_root(Path(project_root))
    receipt_path = root / RECEIPT_RELATIVE_PATH
    if not receipt_path.is_file():
        raise PublicationReceiptVerificationError(
            PublicationReceiptVerificationErrorCode.RECEIPT_MISSING,
            "committed Hugging Face Dataset publication receipt is missing",
        )

    payload = receipt_path.read_bytes()
    _verify_receipt_integrity(payload)
    _reject_secret_markers(payload)
    receipt = _parse_receipt(payload)
    _verify_receipt_identity(receipt, payload)
    _verify_receipt_gates(receipt)
    _verify_receipt_files(receipt)
    _verify_local_candidate(root, receipt)
    return receipt


def _verify_receipt_integrity(payload: bytes) -> None:
    if len(payload) != EXPECTED_RECEIPT_BYTE_COUNT:
        _raise_integrity("publication receipt byte count does not match the retained artifact")
    if _sha256_bytes(payload) != EXPECTED_RECEIPT_SHA256:
        _raise_integrity("publication receipt SHA-256 does not match the retained artifact")


def _parse_receipt(payload: bytes) -> PublicationReceipt:
    try:
        return PublicationReceipt.model_validate_json(payload)
    except ValidationError as error:
        raise PublicationReceiptVerificationError(
            PublicationReceiptVerificationErrorCode.RECEIPT_SCHEMA_INVALID,
            f"publication receipt failed strict schema validation: {error}",
        ) from error


def _verify_receipt_identity(receipt: PublicationReceipt, payload: bytes) -> None:
    raw = json.loads(payload)
    conditions = (
        receipt.repository_id == EXPECTED_REPOSITORY_ID,
        receipt.repository_url == EXPECTED_REPOSITORY_URL,
        receipt.namespace == "KaboKableMolefe",
        receipt.repository_name == "specsafe-bounded-negative-evidence-v1",
        receipt.repository_type == "dataset",
        receipt.published_revision == EXPECTED_PUBLISHED_REVISION,
        raw.get("published_at") == EXPECTED_PUBLISHED_AT,
        receipt.publication_manifest_sha256 == EXPECTED_PUBLICATION_MANIFEST_SHA256,
    )
    if not all(conditions):
        raise PublicationReceiptVerificationError(
            PublicationReceiptVerificationErrorCode.RECEIPT_IDENTITY_INVALID,
            "publication receipt does not match the authorized public Dataset identity",
        )


def _verify_receipt_gates(receipt: PublicationReceipt) -> None:
    conditions = (
        receipt.final_visibility == "public",
        receipt.gated is False,
        receipt.authenticated_namespace_verified is True,
        receipt.private_stage_verified is True,
        receipt.anonymous_public_verification_passed is True,
        receipt.negative_evidence_marker_verified is True,
        receipt.candidate_non_promotion_verified is True,
        receipt.license_metadata_verified is True,
        receipt.rollback_triggered is False,
    )
    if not all(conditions):
        raise PublicationReceiptVerificationError(
            PublicationReceiptVerificationErrorCode.RECEIPT_GATE_INVALID,
            "publication receipt does not retain every required publication gate",
        )


def _verify_receipt_files(receipt: PublicationReceipt) -> None:
    expected_names = tuple(item.relative_path for item in EXPECTED_FILES)
    if receipt.remote_file_count != len(EXPECTED_FILES):
        _raise_file_set("publication receipt remote file count does not match")
    if receipt.remote_files != expected_names:
        _raise_file_set("publication receipt remote file allowlist does not match")
    if receipt.published_file_hashes != EXPECTED_FILES:
        _raise_file_set("publication receipt file hashes do not match the authorized candidate")


def _verify_local_candidate(root: Path, receipt: PublicationReceipt) -> None:
    candidate_root = root / CANDIDATE_RELATIVE_DIRECTORY
    if not candidate_root.is_dir():
        _raise_candidate("authorized local publication candidate directory is missing")

    entries = tuple(candidate_root.iterdir())
    actual_files = tuple(
        sorted(path.name for path in entries if path.is_file() and not path.is_symlink())
    )
    if actual_files != receipt.remote_files:
        _raise_candidate("local candidate file allowlist does not match the public receipt")
    if any(path.is_dir() or path.is_symlink() for path in entries):
        _raise_candidate("local candidate contains nested or linked content")

    for artifact in receipt.published_file_hashes:
        path = candidate_root / artifact.relative_path
        payload = path.read_bytes()
        if len(payload) != artifact.byte_count or _sha256_bytes(payload) != artifact.sha256:
            _raise_candidate(
                f"local candidate does not match the published receipt: {artifact.relative_path}"
            )


def _reject_secret_markers(payload: bytes) -> None:
    lowered = payload.lower()
    if any(marker in lowered for marker in _FORBIDDEN_RECEIPT_MARKERS):
        raise PublicationReceiptVerificationError(
            PublicationReceiptVerificationErrorCode.RECEIPT_SECRET_MARKER_DETECTED,
            "publication receipt contains a forbidden credential marker",
        )


def _require_project_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir() or not (resolved / "pyproject.toml").is_file():
        raise PublicationReceiptVerificationError(
            PublicationReceiptVerificationErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return resolved


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _raise_integrity(message: str) -> None:
    raise PublicationReceiptVerificationError(
        PublicationReceiptVerificationErrorCode.RECEIPT_INTEGRITY_FAILED,
        message,
    )


def _raise_file_set(message: str) -> None:
    raise PublicationReceiptVerificationError(
        PublicationReceiptVerificationErrorCode.RECEIPT_FILE_SET_INVALID,
        message,
    )


def _raise_candidate(message: str) -> None:
    raise PublicationReceiptVerificationError(
        PublicationReceiptVerificationErrorCode.CANDIDATE_INTEGRITY_FAILED,
        message,
    )
