from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from specsafe.hugging_face_space_prebuilt_candidate import (
    HuggingFaceSpacePrebuiltCandidateManifest,
)
from specsafe.hugging_face_space_publication import SpacePublicationReceipt

from .models import SpacePublicationReconciliationRecord

RECEIPT_RELATIVE_PATH = Path(
    "evidence/publication-receipts/specsafe-reliability-lab/"
    "hugging_face_space_publication_receipt.json"
)
RECONCILIATION_RELATIVE_PATH = Path(
    "evidence/publication-receipts/specsafe-reliability-lab/"
    "hugging_face_space_publication_reconciliation.json"
)
PREBUILT_MANIFEST_RELATIVE_PATH = Path(
    "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/"
    "prebuilt_candidate_manifest.json"
)
PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH = Path(
    "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/candidate/space"
)
SOURCE_MANIFEST_RELATIVE_PATH = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/"
    "publication_candidate_manifest.json"
)

EXPECTED_REPOSITORY_ID = "KaboKableMolefe/specsafe-reliability-lab"
EXPECTED_REPOSITORY_URL = "https://huggingface.co/spaces/KaboKableMolefe/specsafe-reliability-lab"
EXPECTED_APPLICATION_URL = "https://kabokablemolefe-specsafe-reliability-lab.static.hf.space"
EXPECTED_PUBLISHED_REVISION = "453481cc16518ba8d8b425813aca4cfc74c2d0e8"
EXPECTED_PUBLISHED_FROM_GIT_SHA = "e456a7f1b8b8a1e3dddbbfc3a0f54ed3049f8b52"
EXPECTED_PUBLISHED_AT = datetime(2026, 7, 11, 18, 11, 57, 890749, tzinfo=UTC)
EXPECTED_CANDIDATE_MANIFEST_SHA256 = (
    "d377f18aa189cec1529b6385483059acecb675bdfc74eda767fc005e631f07e3"
)
EXPECTED_CANDIDATE_TREE_SHA256 = "4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362"
EXPECTED_SOURCE_MANIFEST_SHA256 = "63a28d28416f67b55f62019ff6c5905c923de791564f8de8fa6859a676356b8d"
EXPECTED_SOURCE_TREE_SHA256 = "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
EXPECTED_EVIDENCE_SHA256 = "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
EXPECTED_REMOTE_FILES = (
    "README.md",
    "assets/index-ComhRJPm.css",
    "assets/index-DBdnOm5m.js",
    "evidence/evidence_index.json",
    "index.html",
)
TERMINAL_ERROR_STAGES = frozenset({"BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"})
FORBIDDEN_RECEIPT_MARKERS = (
    b"authorization: bearer",
    b"access_token",
    b"api_key",
    b"hf_token",
    b"secret",
)
_APPLICATION_URL_PATTERN = re.compile(r"^https://[A-Za-z0-9.-]+\.hf\.space/?$")


class ReceiptReconciliationErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_space_receipt_invalid_project_root"
    RECEIPT_MISSING = "hf_space_receipt_missing"
    RECEIPT_INVALID = "hf_space_receipt_invalid"
    RECEIPT_SECRET_MARKER = "hf_space_receipt_secret_marker"
    LOCAL_LINEAGE_MISMATCH = "hf_space_receipt_local_lineage_mismatch"
    LOCAL_CANDIDATE_DRIFT = "hf_space_receipt_local_candidate_drift"
    REMOTE_REPOSITORY_MISMATCH = "hf_space_receipt_remote_repository_mismatch"
    REMOTE_FILE_DRIFT = "hf_space_receipt_remote_file_drift"
    REMOTE_APPLICATION_MISMATCH = "hf_space_receipt_remote_application_mismatch"
    RECONCILIATION_ALREADY_EXISTS = "hf_space_receipt_reconciliation_already_exists"
    RECONCILIATION_WRITE_FAILED = "hf_space_receipt_reconciliation_write_failed"
    RECONCILIATION_INVALID = "hf_space_receipt_reconciliation_invalid"


class ReceiptReconciliationError(RuntimeError):
    def __init__(
        self,
        code: ReceiptReconciliationErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class AnonymousPublicationGateway(Protocol):
    def repository_state(
        self,
        repo_id: str,
        *,
        revision: str,
    ) -> Mapping[str, object]: ...

    def list_files(
        self,
        repo_id: str,
        *,
        revision: str,
    ) -> tuple[str, ...]: ...

    def read_file(
        self,
        repo_id: str,
        filename: str,
        *,
        revision: str,
    ) -> bytes: ...

    def fetch_application(self, application_url: str) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class VerifiedLocalReceipt:
    receipt: SpacePublicationReceipt
    receipt_byte_count: int
    receipt_sha256: str
    manifest: HuggingFaceSpacePrebuiltCandidateManifest


def verify_local_publication_receipt(
    project_root: Path | str,
) -> VerifiedLocalReceipt:
    root = _require_project_root(Path(project_root))
    receipt_path = root / RECEIPT_RELATIVE_PATH
    if not receipt_path.is_file():
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECEIPT_MISSING,
            "retained Hugging Face Space publication receipt is missing",
        )

    receipt_bytes = receipt_path.read_bytes()
    lowered = receipt_bytes.lower()
    if any(marker in lowered for marker in FORBIDDEN_RECEIPT_MARKERS):
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECEIPT_SECRET_MARKER,
            "publication receipt contains a forbidden credential marker",
        )

    try:
        receipt = SpacePublicationReceipt.model_validate_json(receipt_bytes)
    except ValidationError as error:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECEIPT_INVALID,
            f"publication receipt failed strict v2 validation: {error}",
        ) from error

    manifest_bytes, manifest = _load_prebuilt_manifest(root)
    source_manifest_bytes = _read_required(root / SOURCE_MANIFEST_RELATIVE_PATH)
    _verify_local_candidate(root, manifest)

    conditions = (
        receipt.repository_id == EXPECTED_REPOSITORY_ID,
        receipt.repository_url == EXPECTED_REPOSITORY_URL,
        receipt.application_url == EXPECTED_APPLICATION_URL,
        receipt.published_revision == EXPECTED_PUBLISHED_REVISION,
        receipt.published_from_git_sha == EXPECTED_PUBLISHED_FROM_GIT_SHA,
        receipt.published_at == EXPECTED_PUBLISHED_AT,
        receipt.candidate_manifest_sha256 == EXPECTED_CANDIDATE_MANIFEST_SHA256,
        receipt.candidate_tree_sha256 == EXPECTED_CANDIDATE_TREE_SHA256,
        receipt.source_candidate_manifest_sha256 == EXPECTED_SOURCE_MANIFEST_SHA256,
        receipt.source_candidate_tree_sha256 == EXPECTED_SOURCE_TREE_SHA256,
        receipt.evidence_index_sha256 == EXPECTED_EVIDENCE_SHA256,
        receipt.remote_file_count == len(EXPECTED_REMOTE_FILES),
        receipt.remote_files == EXPECTED_REMOTE_FILES,
        receipt.provider_side_build_required is False,
        receipt.prebuilt_static_assets_verified is True,
        receipt.rollback_triggered is False,
        _sha256(manifest_bytes) == EXPECTED_CANDIDATE_MANIFEST_SHA256,
        _sha256(source_manifest_bytes) == EXPECTED_SOURCE_MANIFEST_SHA256,
        receipt.published_file_hashes == manifest.files,
    )
    if not all(conditions):
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.LOCAL_LINEAGE_MISMATCH,
            "publication receipt is outside the authorized retained lineage",
        )

    return VerifiedLocalReceipt(
        receipt=receipt,
        receipt_byte_count=len(receipt_bytes),
        receipt_sha256=_sha256(receipt_bytes),
        manifest=manifest,
    )


def reconcile_remote_publication(
    project_root: Path | str,
    gateway: AnonymousPublicationGateway,
    *,
    now: datetime | None = None,
) -> SpacePublicationReconciliationRecord:
    local = verify_local_publication_receipt(project_root)
    receipt = local.receipt

    state = gateway.repository_state(
        receipt.repository_id,
        revision=receipt.published_revision,
    )
    runtime_stage = state.get("stage")
    terminal_error_absent = runtime_stage not in TERMINAL_ERROR_STAGES
    state_conditions = (
        state.get("id") == receipt.repository_id,
        state.get("sha") == receipt.published_revision,
        state.get("private") is False,
        state.get("gated") in (False, None),
        state.get("sdk") == "static",
        isinstance(runtime_stage, str),
        terminal_error_absent,
    )
    if not all(state_conditions):
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.REMOTE_REPOSITORY_MISMATCH,
            "anonymous remote Space state does not match the retained receipt",
        )

    remote_files = gateway.list_files(
        receipt.repository_id,
        revision=receipt.published_revision,
    )
    if remote_files != receipt.remote_files:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.REMOTE_FILE_DRIFT,
            "anonymous remote Space file allowlist drifted",
        )

    expected_by_name = {item.relative_path: item for item in receipt.published_file_hashes}
    for filename in remote_files:
        payload = gateway.read_file(
            receipt.repository_id,
            filename,
            revision=receipt.published_revision,
        )
        expected = expected_by_name[filename]
        if len(payload) != expected.byte_count or _sha256(payload) != expected.sha256:
            raise ReceiptReconciliationError(
                ReceiptReconciliationErrorCode.REMOTE_FILE_DRIFT,
                f"anonymous remote Space file drifted: {filename}",
            )

    application = gateway.fetch_application(receipt.application_url)
    _verify_application(application, receipt.application_url)

    return SpacePublicationReconciliationRecord(
        schema_version="specsafe_hugging_face_space_publication_reconciliation_v1",
        publication_id=receipt.publication_id,
        receipt_relative_path=RECEIPT_RELATIVE_PATH.as_posix(),
        receipt_byte_count=local.receipt_byte_count,
        receipt_sha256=local.receipt_sha256,
        repository_id=receipt.repository_id,
        repository_url=receipt.repository_url,
        application_url=receipt.application_url,
        published_revision=receipt.published_revision,
        published_from_git_sha=receipt.published_from_git_sha,
        candidate_manifest_sha256=receipt.candidate_manifest_sha256,
        candidate_tree_sha256=receipt.candidate_tree_sha256,
        source_candidate_manifest_sha256=receipt.source_candidate_manifest_sha256,
        source_candidate_tree_sha256=receipt.source_candidate_tree_sha256,
        evidence_index_sha256=receipt.evidence_index_sha256,
        remote_file_count=receipt.remote_file_count,
        remote_files=receipt.remote_files,
        remote_file_hashes=receipt.published_file_hashes,
        remote_visibility="public",
        remote_sdk="static",
        remote_runtime_stage=runtime_stage,
        anonymous_repository_verified=True,
        anonymous_file_hashes_verified=True,
        anonymous_application_verified=True,
        served_html_verified=True,
        remote_public_and_ungated=True,
        remote_revision_matches_receipt=True,
        terminal_error_absent=True,
        credential_used=False,
        verified_at=now or datetime.now(tz=UTC),
    )


def write_remote_reconciliation(
    project_root: Path | str,
    gateway: AnonymousPublicationGateway,
    *,
    now: datetime | None = None,
) -> SpacePublicationReconciliationRecord:
    root = _require_project_root(Path(project_root))
    target = root / RECONCILIATION_RELATIVE_PATH
    if target.exists():
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECONCILIATION_ALREADY_EXISTS,
            "retained publication reconciliation already exists; refusing to overwrite",
        )

    record = reconcile_remote_publication(root, gateway, now=now)
    payload = _canonical_json_bytes(record.model_dump(mode="json"))
    _write_atomic(target, payload)
    return record


def check_committed_reconciliation(
    project_root: Path | str,
) -> SpacePublicationReconciliationRecord:
    root = _require_project_root(Path(project_root))
    local = verify_local_publication_receipt(root)
    path = root / RECONCILIATION_RELATIVE_PATH
    if not path.is_file():
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECONCILIATION_INVALID,
            "committed publication reconciliation is missing",
        )

    payload = path.read_bytes()
    try:
        record = SpacePublicationReconciliationRecord.model_validate_json(payload)
    except ValidationError as error:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECONCILIATION_INVALID,
            f"publication reconciliation failed strict validation: {error}",
        ) from error

    expected_conditions = (
        record.receipt_byte_count == local.receipt_byte_count,
        record.receipt_sha256 == local.receipt_sha256,
        record.remote_files == local.receipt.remote_files,
        record.remote_file_hashes == local.receipt.published_file_hashes,
        record.published_revision == local.receipt.published_revision,
        record.published_from_git_sha == local.receipt.published_from_git_sha,
        record.candidate_manifest_sha256 == local.receipt.candidate_manifest_sha256,
        record.candidate_tree_sha256 == local.receipt.candidate_tree_sha256,
        record.source_candidate_manifest_sha256 == local.receipt.source_candidate_manifest_sha256,
        record.source_candidate_tree_sha256 == local.receipt.source_candidate_tree_sha256,
        record.evidence_index_sha256 == local.receipt.evidence_index_sha256,
        payload == _canonical_json_bytes(record.model_dump(mode="json")),
    )
    if not all(expected_conditions):
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECONCILIATION_INVALID,
            "committed publication reconciliation drifted from the retained receipt",
        )
    return record


def _load_prebuilt_manifest(
    root: Path,
) -> tuple[bytes, HuggingFaceSpacePrebuiltCandidateManifest]:
    payload = _read_required(root / PREBUILT_MANIFEST_RELATIVE_PATH)
    try:
        manifest = HuggingFaceSpacePrebuiltCandidateManifest.model_validate_json(payload)
    except ValidationError as error:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.LOCAL_LINEAGE_MISMATCH,
            f"prebuilt candidate manifest failed strict validation: {error}",
        ) from error
    return payload, manifest


def _verify_local_candidate(
    root: Path,
    manifest: HuggingFaceSpacePrebuiltCandidateManifest,
) -> None:
    candidate_root = root / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH
    if not candidate_root.is_dir():
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.LOCAL_CANDIDATE_DRIFT,
            "committed prebuilt publication candidate directory is missing",
        )

    actual_paths: list[str] = []
    for path in candidate_root.rglob("*"):
        relative = path.relative_to(candidate_root).as_posix()
        if path.is_symlink():
            raise ReceiptReconciliationError(
                ReceiptReconciliationErrorCode.LOCAL_CANDIDATE_DRIFT,
                f"committed prebuilt candidate contains linked content: {relative}",
            )
        if path.is_file():
            actual_paths.append(relative)

    expected_paths = tuple(item.relative_path for item in manifest.files)
    if tuple(sorted(actual_paths)) != expected_paths:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.LOCAL_CANDIDATE_DRIFT,
            "committed prebuilt candidate file allowlist drifted",
        )

    payloads: dict[str, bytes] = {}
    for item in manifest.files:
        payload = (candidate_root / item.relative_path).read_bytes()
        if len(payload) != item.byte_count or _sha256(payload) != item.sha256:
            raise ReceiptReconciliationError(
                ReceiptReconciliationErrorCode.LOCAL_CANDIDATE_DRIFT,
                f"committed prebuilt candidate file drifted: {item.relative_path}",
            )
        payloads[item.relative_path] = payload

    if _candidate_tree_sha256(payloads) != EXPECTED_CANDIDATE_TREE_SHA256:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.LOCAL_CANDIDATE_DRIFT,
            "committed prebuilt candidate aggregate tree hash drifted",
        )


def _verify_application(
    application: Mapping[str, object],
    expected_url: str,
) -> None:
    url = application.get("application_url")
    status_code = application.get("status_code")
    content_type = application.get("content_type")
    body = application.get("body")

    valid_url = (
        isinstance(url, str)
        and url == expected_url
        and bool(_APPLICATION_URL_PATTERN.fullmatch(url))
    )
    valid_content_type = isinstance(content_type, str) and "text/html" in content_type.lower()
    conditions = (
        valid_url,
        status_code == 200,
        valid_content_type,
        isinstance(body, bytes),
    )
    if not all(conditions):
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.REMOTE_APPLICATION_MISMATCH,
            "anonymous public application response does not match the retained receipt",
        )

    text = body.decode("utf-8", errors="replace")
    if "SpecSafe" not in text or 'id="root"' not in text:
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.REMOTE_APPLICATION_MISMATCH,
            "anonymous public application lost required HTML markers",
        )


def _write_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.unlink(missing_ok=True)
        temporary.write_bytes(payload)
        temporary.replace(path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.RECONCILIATION_WRITE_FAILED,
            f"failed to write retained publication reconciliation: {error}",
        ) from error


def _read_required(path: Path) -> bytes:
    if not path.is_file():
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.LOCAL_LINEAGE_MISMATCH,
            f"required retained publication evidence is missing: {path}",
        )
    return path.read_bytes()


def _require_project_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir() or not (resolved / "pyproject.toml").is_file():
        raise ReceiptReconciliationError(
            ReceiptReconciliationErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return resolved


def _candidate_tree_sha256(files: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative_path, payload in sorted(files.items()):
        digest.update(relative_path.encode())
        digest.update(b"\0")
        digest.update(_sha256(payload).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
