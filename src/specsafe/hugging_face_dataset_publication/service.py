from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from specsafe.publication_authorization.models import ExactPublicationAuthorizationDecision

from .models import FileDigest, PublicationPlan, PublicationReceipt

AUTHORIZATION_RELATIVE_PATH = (
    "evidence/release-governance/specsafe-bounded-negative-evidence-v1/"
    "publication_authorization_decision.json"
)
CANDIDATE_RELATIVE_DIRECTORY = "release/hugging-face/specsafe-bounded-negative-evidence-v1"
RECEIPT_RELATIVE_PATH = (
    "evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/"
    "hugging_face_dataset_publication_receipt.json"
)
EXPECTED_AUTHORIZATION_SHA256 = "bf96e015379f8ad955791c28b8ba75b123b3d748d2192943190b056eb5aadc46"
EXPECTED_AUTHORIZATION_BYTE_COUNT = 4528
EXPECTED_PUBLICATION_MANIFEST_SHA256 = (
    "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
)
EXPECTED_REMOTE_FILES = (
    "ATTRIBUTION.md",
    "LICENSE.md",
    "README.md",
    "ROLLBACK.md",
    "evidence_boundary.md",
    "publication_manifest.json",
    "release_summary.json",
    "sanitization_report.json",
    "source_release_manifest.json",
)
_NAMESPACE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class DatasetPublicationErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_dataset_publish_invalid_project_root"
    AUTHORIZATION_INVALID = "hf_dataset_publish_authorization_invalid"
    CANDIDATE_DRIFT = "hf_dataset_publish_candidate_drift"
    NAMESPACE_INVALID = "hf_dataset_publish_namespace_invalid"
    NAMESPACE_NOT_AUTHORIZED = "hf_dataset_publish_namespace_not_authorized"
    REMOTE_REPOSITORY_EXISTS = "hf_dataset_publish_remote_repository_exists"
    REMOTE_INITIAL_STATE_INVALID = "hf_dataset_publish_remote_initial_state_invalid"
    PRIVATE_STAGE_VERIFICATION_FAILED = "hf_dataset_publish_private_stage_verification_failed"
    PUBLIC_VERIFICATION_FAILED = "hf_dataset_publish_public_verification_failed"
    RECEIPT_ALREADY_EXISTS = "hf_dataset_publish_receipt_already_exists"
    RECEIPT_WRITE_FAILED = "hf_dataset_publish_receipt_write_failed"


class DatasetPublicationError(RuntimeError):
    def __init__(self, code: DatasetPublicationErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class HubGateway(Protocol):
    def identity(self) -> Mapping[str, object]: ...

    def repository_exists(self, repo_id: str) -> bool: ...

    def create_private_dataset(self, repo_id: str) -> str: ...

    def list_files(
        self, repo_id: str, *, revision: str | None, anonymous: bool
    ) -> tuple[str, ...]: ...

    def commit_exact_files(
        self,
        repo_id: str,
        files: Mapping[str, Path],
        *,
        delete_paths: tuple[str, ...],
    ) -> str: ...

    def read_file(
        self,
        repo_id: str,
        filename: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> bytes: ...

    def dataset_state(
        self,
        repo_id: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> Mapping[str, object]: ...

    def make_public(self, repo_id: str) -> None: ...

    def make_private(self, repo_id: str) -> None: ...

    def delete_dataset(self, repo_id: str) -> None: ...


def build_publication_plan(project_root: Path | str) -> PublicationPlan:
    root = _require_project_root(Path(project_root))
    decision = _load_authorization(root)
    _verify_candidate(root, decision)
    return PublicationPlan(
        schema_version="specsafe_hugging_face_dataset_publication_plan_v1",
        authorization_decision_sha256=EXPECTED_AUTHORIZATION_SHA256,
        authorization_decision_byte_count=EXPECTED_AUTHORIZATION_BYTE_COUNT,
        candidate_id=decision.candidate_id,
        release_id=decision.release_id,
        repository_name=decision.target.repository_name,
        repository_type="dataset",
        final_visibility="public",
        gated=False,
        publication_manifest_sha256=EXPECTED_PUBLICATION_MANIFEST_SHA256,
        files=tuple(
            FileDigest(
                relative_path=item.relative_path,
                sha256=item.sha256,
                byte_count=item.byte_count,
            )
            for item in decision.authorized_files
        ),
        upload_mode="private_stage_exact_commit_public_release",
        remote_existing_repository_policy="reject",
        credential_policy="locally_managed_credential_never_logged",
        receipt_relative_path=RECEIPT_RELATIVE_PATH,
    )


def preflight_remote_publication(
    project_root: Path | str,
    namespace: str,
    gateway: HubGateway,
) -> str:
    plan = build_publication_plan(project_root)
    normalized_namespace = _validate_namespace(namespace)
    _require_authorized_namespace(normalized_namespace, gateway.identity())
    repo_id = f"{normalized_namespace}/{plan.repository_name}"
    if gateway.repository_exists(repo_id):
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.REMOTE_REPOSITORY_EXISTS,
            f"refusing to publish over an existing Hugging Face Dataset repository: {repo_id}",
        )
    return repo_id


def publish_authorized_dataset(
    project_root: Path | str,
    namespace: str,
    gateway: HubGateway,
    *,
    now: Callable[[], datetime] | None = None,
    receipt_path: Path | str | None = None,
) -> PublicationReceipt:
    root = _require_project_root(Path(project_root))
    plan = build_publication_plan(root)
    repo_id = preflight_remote_publication(root, namespace, gateway)
    normalized_namespace = repo_id.split("/", maxsplit=1)[0]
    candidate_root = root / CANDIDATE_RELATIVE_DIRECTORY
    local_files = {name: candidate_root / name for name in EXPECTED_REMOTE_FILES}
    target_receipt = _resolve_receipt_path(root, receipt_path)
    if target_receipt.exists():
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.RECEIPT_ALREADY_EXISTS,
            "publication receipt already exists; refusing to overwrite retained evidence",
        )

    created = False
    made_public = False
    try:
        repo_url = gateway.create_private_dataset(repo_id)
        created = True
        initial_files = gateway.list_files(repo_id, revision=None, anonymous=False)
        unexpected_initial = set(initial_files) - {".gitattributes"}
        if unexpected_initial:
            raise DatasetPublicationError(
                DatasetPublicationErrorCode.REMOTE_INITIAL_STATE_INVALID,
                "new remote repository contains unexpected files before publication",
            )
        delete_paths = (".gitattributes",) if ".gitattributes" in initial_files else ()
        revision = gateway.commit_exact_files(repo_id, local_files, delete_paths=delete_paths)
        _verify_remote(
            gateway,
            repo_id,
            revision,
            plan,
            anonymous=False,
            error_code=DatasetPublicationErrorCode.PRIVATE_STAGE_VERIFICATION_FAILED,
        )
        gateway.make_public(repo_id)
        made_public = True
        _verify_remote(
            gateway,
            repo_id,
            revision,
            plan,
            anonymous=True,
            error_code=DatasetPublicationErrorCode.PUBLIC_VERIFICATION_FAILED,
        )
    except Exception:
        if created and not made_public:
            gateway.delete_dataset(repo_id)
        elif made_public:
            gateway.make_private(repo_id)
        raise

    receipt = PublicationReceipt(
        schema_version="specsafe_hugging_face_dataset_publication_receipt_v1",
        publication_id="specsafe-bounded-negative-evidence-hf-publication-v1",
        repository_id=repo_id,
        repository_url=repo_url,
        namespace=normalized_namespace,
        repository_name=plan.repository_name,
        repository_type="dataset",
        final_visibility="public",
        gated=False,
        published_revision=revision,
        publication_manifest_sha256=EXPECTED_PUBLICATION_MANIFEST_SHA256,
        published_file_hashes=plan.files,
        remote_files=EXPECTED_REMOTE_FILES,
        remote_file_count=9,
        authenticated_namespace_verified=True,
        private_stage_verified=True,
        anonymous_public_verification_passed=True,
        negative_evidence_marker_verified=True,
        candidate_non_promotion_verified=True,
        license_metadata_verified=True,
        rollback_triggered=False,
        published_at=(now or _utc_now)(),
    )
    _write_receipt(target_receipt, receipt)
    return receipt


def _verify_remote(
    gateway: HubGateway,
    repo_id: str,
    revision: str,
    plan: PublicationPlan,
    *,
    anonymous: bool,
    error_code: DatasetPublicationErrorCode,
) -> None:
    remote_files = gateway.list_files(repo_id, revision=revision, anonymous=anonymous)
    if remote_files != EXPECTED_REMOTE_FILES:
        raise DatasetPublicationError(error_code, "remote file allowlist does not match")
    expected_by_name = {item.relative_path: item for item in plan.files}
    remote_payloads: dict[str, bytes] = {}
    for filename in EXPECTED_REMOTE_FILES:
        payload = gateway.read_file(
            repo_id,
            filename,
            revision=revision,
            anonymous=anonymous,
        )
        expected = expected_by_name[filename]
        if len(payload) != expected.byte_count or _sha256_bytes(payload) != expected.sha256:
            raise DatasetPublicationError(error_code, f"remote file hash mismatch: {filename}")
        remote_payloads[filename] = payload

    state = gateway.dataset_state(repo_id, revision=revision, anonymous=anonymous)
    if state.get("id") != repo_id or state.get("sha") != revision:
        raise DatasetPublicationError(error_code, "remote Dataset identity or revision mismatch")
    if not anonymous and state.get("private") is not True:
        raise DatasetPublicationError(error_code, "remote Dataset was not private during staging")
    if anonymous and (state.get("private") is not False or state.get("gated") is not False):
        raise DatasetPublicationError(
            error_code, "remote Dataset is not anonymously public and ungated"
        )

    readme = remote_payloads["README.md"].decode("utf-8")
    required_markers = (
        "license: cc-by-4.0",
        "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        "candidate_not_promoted=true",
        "scheduler_promotion_authorized=false",
        "failure_label=ranking_safety_regression",
    )
    if any(marker not in readme for marker in required_markers):
        raise DatasetPublicationError(error_code, "remote Dataset card lost a required boundary")


def _load_authorization(root: Path) -> ExactPublicationAuthorizationDecision:
    path = root / AUTHORIZATION_RELATIVE_PATH
    payload = _require_exact_file(
        path,
        EXPECTED_AUTHORIZATION_SHA256,
        EXPECTED_AUTHORIZATION_BYTE_COUNT,
        DatasetPublicationErrorCode.AUTHORIZATION_INVALID,
    )
    try:
        decision = ExactPublicationAuthorizationDecision.model_validate_json(payload)
    except ValidationError as error:
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.AUTHORIZATION_INVALID,
            f"publication authorization failed strict schema validation: {error}",
        ) from error
    if not decision.publication_authorized or decision.publication_performed:
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.AUTHORIZATION_INVALID,
            "publication authorization is not at the controlled publication boundary",
        )
    return decision


def _verify_candidate(
    root: Path,
    decision: ExactPublicationAuthorizationDecision,
) -> Mapping[str, Path]:
    candidate_root = root / CANDIDATE_RELATIVE_DIRECTORY
    if not candidate_root.is_dir():
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.CANDIDATE_DRIFT,
            "authorized publication candidate directory is missing",
        )
    entries = tuple(candidate_root.iterdir())
    actual_files = tuple(
        sorted(path.name for path in entries if path.is_file() and not path.is_symlink())
    )
    if actual_files != EXPECTED_REMOTE_FILES:
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.CANDIDATE_DRIFT,
            "authorized publication candidate file allowlist drifted",
        )
    if any(path.is_dir() or path.is_symlink() for path in entries):
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.CANDIDATE_DRIFT,
            "authorized publication candidate contains nested or linked content",
        )
    for artifact in decision.authorized_files:
        _require_exact_file(
            candidate_root / artifact.relative_path,
            artifact.sha256,
            artifact.byte_count,
            DatasetPublicationErrorCode.CANDIDATE_DRIFT,
        )
    return {name: candidate_root / name for name in EXPECTED_REMOTE_FILES}


def _require_authorized_namespace(namespace: str, identity: Mapping[str, object]) -> None:
    account_name = identity.get("name")
    organizations = identity.get("orgs", ())
    organization_names = {
        item.get("name")
        for item in organizations
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }
    if namespace != account_name and namespace not in organization_names:
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.NAMESPACE_NOT_AUTHORIZED,
            "requested namespace is not the authenticated account or one of its organizations",
        )


def _validate_namespace(namespace: str) -> str:
    value = namespace.strip()
    if not _NAMESPACE_PATTERN.fullmatch(value):
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.NAMESPACE_INVALID,
            "Hugging Face namespace contains unsupported characters",
        )
    return value


def _resolve_receipt_path(root: Path, receipt_path: Path | str | None) -> Path:
    path = root / RECEIPT_RELATIVE_PATH if receipt_path is None else Path(receipt_path)
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.RECEIPT_WRITE_FAILED,
            "publication receipt must remain inside the repository",
        )
    return resolved


def _write_receipt(path: Path, receipt: PublicationReceipt) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError as error:
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.RECEIPT_WRITE_FAILED,
            f"failed to write publication receipt: {error}",
        ) from error


def _require_exact_file(
    path: Path,
    expected_sha256: str,
    expected_byte_count: int,
    error_code: DatasetPublicationErrorCode,
) -> bytes:
    if not path.is_file():
        raise DatasetPublicationError(error_code, f"required publication file is missing: {path}")
    payload = path.read_bytes()
    if len(payload) != expected_byte_count or _sha256_bytes(payload) != expected_sha256:
        raise DatasetPublicationError(error_code, f"publication file drifted: {path}")
    return payload


def _require_project_root(root: Path) -> Path:
    resolved = root.resolve()
    if not (resolved / "pyproject.toml").is_file():
        raise DatasetPublicationError(
            DatasetPublicationErrorCode.INVALID_PROJECT_ROOT,
            "project root must contain pyproject.toml",
        )
    return resolved


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
