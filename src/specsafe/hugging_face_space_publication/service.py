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

from specsafe.hugging_face_space_publication_candidate import (
    HuggingFaceSpacePublicationCandidateManifest,
)

from .models import SpacePublicationPlan, SpacePublicationReceipt

CANDIDATE_MANIFEST_RELATIVE_PATH = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/"
    "publication_candidate_manifest.json"
)
CANDIDATE_ROOT_RELATIVE_PATH = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space"
)
RECEIPT_RELATIVE_PATH = Path(
    "evidence/publication-receipts/specsafe-reliability-lab/"
    "hugging_face_space_publication_receipt.json"
)
EXPECTED_NAMESPACE = "KaboKableMolefe"
EXPECTED_REPOSITORY_NAME = "specsafe-reliability-lab"
EXPECTED_CANDIDATE_TREE_SHA256 = "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
EXPECTED_EVIDENCE_INDEX_SHA256 = "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
EXPECTED_CANDIDATE_FILE_COUNT = 35
_NAMESPACE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_RECEIPT_MARKERS = (
    b"authorization: bearer",
    b"access_token",
    b"api_key",
    b"hf_token",
    b"secret",
)


class SpacePublicationErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_space_publish_invalid_project_root"
    CANDIDATE_MANIFEST_INVALID = "hf_space_publish_candidate_manifest_invalid"
    CANDIDATE_DRIFT = "hf_space_publish_candidate_drift"
    NAMESPACE_INVALID = "hf_space_publish_namespace_invalid"
    NAMESPACE_NOT_AUTHORIZED = "hf_space_publish_namespace_not_authorized"
    REMOTE_REPOSITORY_EXISTS = "hf_space_publish_remote_repository_exists"
    REMOTE_INITIAL_STATE_INVALID = "hf_space_publish_remote_initial_state_invalid"
    PRIVATE_STAGE_VERIFICATION_FAILED = "hf_space_publish_private_stage_verification_failed"
    PUBLIC_REPOSITORY_VERIFICATION_FAILED = "hf_space_publish_public_repository_verification_failed"
    PUBLIC_APPLICATION_VERIFICATION_FAILED = (
        "hf_space_publish_public_application_verification_failed"
    )
    RECEIPT_ALREADY_EXISTS = "hf_space_publish_receipt_already_exists"
    RECEIPT_WRITE_FAILED = "hf_space_publish_receipt_write_failed"
    PUBLISHED_GIT_SHA_INVALID = "hf_space_publish_git_sha_invalid"


class SpacePublicationError(RuntimeError):
    def __init__(self, code: SpacePublicationErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class HubGateway(Protocol):
    def identity(self) -> Mapping[str, object]: ...

    def repository_exists(self, repo_id: str) -> bool: ...

    def create_private_space(self, repo_id: str) -> str: ...

    def list_files(
        self,
        repo_id: str,
        *,
        revision: str | None,
        anonymous: bool,
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

    def space_state(
        self,
        repo_id: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> Mapping[str, object]: ...

    def make_public(self, repo_id: str) -> None: ...

    def make_private(self, repo_id: str) -> None: ...

    def delete_space(self, repo_id: str) -> None: ...

    def wait_for_public_application(
        self,
        repo_id: str,
        *,
        timeout_seconds: int,
    ) -> Mapping[str, object]: ...


def build_publication_plan(project_root: Path | str) -> SpacePublicationPlan:
    root = _require_project_root(Path(project_root))
    manifest_bytes, manifest = _load_candidate_manifest(root)
    _verify_candidate(root, manifest)
    return SpacePublicationPlan(
        schema_version="specsafe_hugging_face_space_publication_plan_v1",
        candidate_manifest_sha256=_sha256_bytes(manifest_bytes),
        candidate_tree_sha256=EXPECTED_CANDIDATE_TREE_SHA256,
        evidence_index_sha256=EXPECTED_EVIDENCE_INDEX_SHA256,
        candidate_file_count=EXPECTED_CANDIDATE_FILE_COUNT,
        repository_name=EXPECTED_REPOSITORY_NAME,
        repository_type="space",
        sdk="static",
        final_visibility="public",
        files=manifest.files,
        upload_mode="private_stage_exact_commit_public_release",
        remote_existing_repository_policy="reject",
        credential_policy="environment_token_never_logged_or_persisted",
        receipt_relative_path=RECEIPT_RELATIVE_PATH.as_posix(),
    )


def preflight_remote_publication(
    project_root: Path | str,
    namespace: str,
    gateway: HubGateway,
) -> str:
    plan = build_publication_plan(project_root)
    normalized_namespace = _validate_namespace(namespace)
    if normalized_namespace != EXPECTED_NAMESPACE:
        raise SpacePublicationError(
            SpacePublicationErrorCode.NAMESPACE_NOT_AUTHORIZED,
            f"Space publication namespace must be exactly {EXPECTED_NAMESPACE}",
        )
    _require_authorized_namespace(normalized_namespace, gateway.identity())
    repo_id = f"{normalized_namespace}/{plan.repository_name}"
    if gateway.repository_exists(repo_id):
        raise SpacePublicationError(
            SpacePublicationErrorCode.REMOTE_REPOSITORY_EXISTS,
            f"refusing to publish over an existing Hugging Face Space: {repo_id}",
        )
    return repo_id


def publish_authorized_space(
    project_root: Path | str,
    namespace: str,
    gateway: HubGateway,
    *,
    published_from_git_sha: str,
    now: Callable[[], datetime] | None = None,
    receipt_path: Path | str | None = None,
    application_timeout_seconds: int = 900,
) -> SpacePublicationReceipt:
    root = _require_project_root(Path(project_root))
    if not _GIT_SHA_PATTERN.fullmatch(published_from_git_sha):
        raise SpacePublicationError(
            SpacePublicationErrorCode.PUBLISHED_GIT_SHA_INVALID,
            "published_from_git_sha must be a canonical 40-character Git SHA",
        )

    plan = build_publication_plan(root)
    repo_id = preflight_remote_publication(root, namespace, gateway)
    candidate_root = root / CANDIDATE_ROOT_RELATIVE_PATH
    local_files = {item.relative_path: candidate_root / item.relative_path for item in plan.files}
    target_receipt = _resolve_receipt_path(root, receipt_path)
    if target_receipt.exists():
        raise SpacePublicationError(
            SpacePublicationErrorCode.RECEIPT_ALREADY_EXISTS,
            "Space publication receipt already exists; refusing to overwrite retained evidence",
        )

    created = False
    made_public = False
    try:
        repository_url = gateway.create_private_space(repo_id)
        created = True
        initial_files = gateway.list_files(repo_id, revision=None, anonymous=False)
        unexpected_initial = set(initial_files) - {".gitattributes"}
        if unexpected_initial:
            raise SpacePublicationError(
                SpacePublicationErrorCode.REMOTE_INITIAL_STATE_INVALID,
                "new Space contains unexpected files before exact publication",
            )
        delete_paths = (".gitattributes",) if ".gitattributes" in initial_files else ()
        revision = gateway.commit_exact_files(
            repo_id,
            local_files,
            delete_paths=delete_paths,
        )
        _verify_remote_repository(
            gateway,
            repo_id,
            revision,
            plan,
            anonymous=False,
            error_code=SpacePublicationErrorCode.PRIVATE_STAGE_VERIFICATION_FAILED,
        )

        gateway.make_public(repo_id)
        made_public = True
        _verify_remote_repository(
            gateway,
            repo_id,
            revision,
            plan,
            anonymous=True,
            error_code=SpacePublicationErrorCode.PUBLIC_REPOSITORY_VERIFICATION_FAILED,
        )
        application = gateway.wait_for_public_application(
            repo_id,
            timeout_seconds=application_timeout_seconds,
        )
        application_url = _verify_public_application(application)
        receipt = SpacePublicationReceipt(
            schema_version="specsafe_hugging_face_space_publication_receipt_v1",
            publication_id="specsafe-reliability-lab-hf-space-publication-v1",
            repository_id=repo_id,
            repository_url=repository_url,
            application_url=application_url,
            namespace=EXPECTED_NAMESPACE,
            repository_name=plan.repository_name,
            repository_type="space",
            sdk="static",
            final_visibility="public",
            published_revision=revision,
            published_from_git_sha=published_from_git_sha,
            candidate_manifest_sha256=plan.candidate_manifest_sha256,
            candidate_tree_sha256=plan.candidate_tree_sha256,
            evidence_index_sha256=plan.evidence_index_sha256,
            published_file_hashes=plan.files,
            remote_files=tuple(item.relative_path for item in plan.files),
            remote_file_count=EXPECTED_CANDIDATE_FILE_COUNT,
            authenticated_namespace_verified=True,
            private_stage_verified=True,
            anonymous_repository_verification_passed=True,
            anonymous_application_verification_passed=True,
            served_html_verified=True,
            static_build_ready=True,
            rollback_triggered=False,
            published_at=(now or _utc_now)(),
        )
        _write_receipt(target_receipt, receipt)
    except Exception:
        if created and not made_public:
            gateway.delete_space(repo_id)
        elif made_public:
            gateway.make_private(repo_id)
        raise
    return receipt


def _load_candidate_manifest(
    root: Path,
) -> tuple[bytes, HuggingFaceSpacePublicationCandidateManifest]:
    path = root / CANDIDATE_MANIFEST_RELATIVE_PATH
    if not path.is_file():
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_MANIFEST_INVALID,
            "committed Space publication candidate manifest is missing",
        )
    payload = path.read_bytes()
    try:
        manifest = HuggingFaceSpacePublicationCandidateManifest.model_validate_json(payload)
    except ValidationError as error:
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_MANIFEST_INVALID,
            f"Space publication candidate manifest failed strict validation: {error}",
        ) from error

    conditions = (
        manifest.space_repository_name == EXPECTED_REPOSITORY_NAME,
        manifest.candidate_tree_sha256 == EXPECTED_CANDIDATE_TREE_SHA256,
        manifest.evidence_index_sha256 == EXPECTED_EVIDENCE_INDEX_SHA256,
        manifest.exact_candidate_file_count == EXPECTED_CANDIDATE_FILE_COUNT,
        len(manifest.files) == EXPECTED_CANDIDATE_FILE_COUNT,
        manifest.actual_space_publication is False,
        manifest.remote_mutation is False,
        manifest.live_inference is False,
        manifest.user_input_collection is False,
    )
    if not all(conditions):
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_MANIFEST_INVALID,
            "Space publication candidate manifest is outside the authorized boundary",
        )
    return payload, manifest


def _verify_candidate(
    root: Path,
    manifest: HuggingFaceSpacePublicationCandidateManifest,
) -> Mapping[str, Path]:
    candidate_root = root / CANDIDATE_ROOT_RELATIVE_PATH
    if not candidate_root.is_dir():
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_DRIFT,
            "authorized Space publication candidate directory is missing",
        )

    expected_paths = tuple(item.relative_path for item in manifest.files)
    actual_paths: list[str] = []
    actual_directories: set[str] = set()
    for path in candidate_root.rglob("*"):
        relative = path.relative_to(candidate_root).as_posix()
        if path.is_symlink():
            raise SpacePublicationError(
                SpacePublicationErrorCode.CANDIDATE_DRIFT,
                f"authorized Space candidate contains linked content: {relative}",
            )
        if path.is_file():
            actual_paths.append(relative)
        elif path.is_dir():
            actual_directories.add(relative)

    if tuple(sorted(actual_paths)) != expected_paths:
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_DRIFT,
            "authorized Space candidate file allowlist drifted",
        )

    expected_directories = _expected_directories(expected_paths)
    if actual_directories != expected_directories:
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_DRIFT,
            "authorized Space candidate directory allowlist drifted",
        )

    payloads: dict[str, bytes] = {}
    for item in manifest.files:
        path = candidate_root / item.relative_path
        payload = path.read_bytes()
        if len(payload) != item.byte_count or _sha256_bytes(payload) != item.sha256:
            raise SpacePublicationError(
                SpacePublicationErrorCode.CANDIDATE_DRIFT,
                f"authorized Space candidate file drifted: {item.relative_path}",
            )
        payloads[item.relative_path] = payload

    tree_sha256 = _candidate_tree_sha256(payloads)
    if tree_sha256 != EXPECTED_CANDIDATE_TREE_SHA256:
        raise SpacePublicationError(
            SpacePublicationErrorCode.CANDIDATE_DRIFT,
            "authorized Space candidate aggregate tree hash drifted",
        )
    return {name: candidate_root / name for name in expected_paths}


def _verify_remote_repository(
    gateway: HubGateway,
    repo_id: str,
    revision: str,
    plan: SpacePublicationPlan,
    *,
    anonymous: bool,
    error_code: SpacePublicationErrorCode,
) -> None:
    expected_files = tuple(item.relative_path for item in plan.files)
    remote_files = gateway.list_files(
        repo_id,
        revision=revision,
        anonymous=anonymous,
    )
    if remote_files != expected_files:
        raise SpacePublicationError(error_code, "remote Space file allowlist does not match")

    remote_payloads: dict[str, bytes] = {}
    expected_by_name = {item.relative_path: item for item in plan.files}
    for filename in expected_files:
        payload = gateway.read_file(
            repo_id,
            filename,
            revision=revision,
            anonymous=anonymous,
        )
        expected = expected_by_name[filename]
        if len(payload) != expected.byte_count or _sha256_bytes(payload) != expected.sha256:
            raise SpacePublicationError(
                error_code,
                f"remote Space file hash mismatch: {filename}",
            )
        remote_payloads[filename] = payload

    state = gateway.space_state(
        repo_id,
        revision=revision,
        anonymous=anonymous,
    )
    if state.get("id") != repo_id or state.get("sha") != revision:
        raise SpacePublicationError(error_code, "remote Space identity or revision mismatch")
    if state.get("sdk") != "static":
        raise SpacePublicationError(error_code, "remote Space SDK is not static")
    if not anonymous and state.get("private") is not True:
        raise SpacePublicationError(error_code, "remote Space was not private during staging")
    if anonymous and (state.get("private") is not False or state.get("gated") not in (False, None)):
        raise SpacePublicationError(
            error_code,
            "remote Space is not anonymously public and ungated",
        )

    readme = remote_payloads["README.md"].decode("utf-8")
    required_markers = (
        "sdk: static",
        "app_build_command: npm run build",
        "app_file: dist/index.html",
        "decision=KEEP_DIAGNOSTIC_ONLY",
        "failure_label=ranking_safety_regression",
        "live_inference=false",
        "user_input_collection=false",
    )
    if any(marker not in readme for marker in required_markers):
        raise SpacePublicationError(error_code, "remote Space card lost a required boundary")


def _verify_public_application(application: Mapping[str, object]) -> str:
    app_url = application.get("application_url")
    status_code = application.get("status_code")
    content_type = application.get("content_type")
    body = application.get("body")
    stage = application.get("stage")

    if not isinstance(app_url, str) or not re.fullmatch(
        r"https://[A-Za-z0-9.-]+\.hf\.space/?",
        app_url,
    ):
        _raise_application_verification("public Space application URL is invalid")
    if status_code != 200:
        _raise_application_verification("public Space application did not return HTTP 200")
    if not isinstance(content_type, str) or "text/html" not in content_type.lower():
        _raise_application_verification("public Space application did not serve HTML")
    if not isinstance(body, bytes):
        _raise_application_verification("public Space application response body is invalid")
    if stage in {"BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"}:
        _raise_application_verification(f"public Space entered terminal error stage: {stage}")

    text = body.decode("utf-8", errors="replace")
    if "SpecSafe" not in text or 'id="root"' not in text:
        _raise_application_verification("public Space HTML lost required application markers")
    return app_url


def _write_receipt(path: Path, receipt: SpacePublicationReceipt) -> None:
    payload = (json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    lowered = payload.lower()
    if any(marker in lowered for marker in _FORBIDDEN_RECEIPT_MARKERS):
        raise SpacePublicationError(
            SpacePublicationErrorCode.RECEIPT_WRITE_FAILED,
            "publication receipt contains a forbidden credential marker",
        )

    temporary = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if temporary.exists():
            temporary.unlink()
        temporary.write_bytes(payload)
        temporary.replace(path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise SpacePublicationError(
            SpacePublicationErrorCode.RECEIPT_WRITE_FAILED,
            f"failed to write Space publication receipt: {error}",
        ) from error


def _resolve_receipt_path(root: Path, receipt_path: Path | str | None) -> Path:
    path = root / RECEIPT_RELATIVE_PATH if receipt_path is None else Path(receipt_path)
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SpacePublicationError(
            SpacePublicationErrorCode.RECEIPT_WRITE_FAILED,
            "Space publication receipt must remain inside the repository",
        )
    return resolved


def _require_authorized_namespace(namespace: str, identity: Mapping[str, object]) -> None:
    account_name = identity.get("name")
    organizations = identity.get("orgs", ())
    organization_names = {
        item.get("name")
        for item in organizations
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }
    if namespace != account_name and namespace not in organization_names:
        raise SpacePublicationError(
            SpacePublicationErrorCode.NAMESPACE_NOT_AUTHORIZED,
            "requested namespace is not the authenticated account or one of its organizations",
        )


def _validate_namespace(namespace: str) -> str:
    value = namespace.strip()
    if not _NAMESPACE_PATTERN.fullmatch(value):
        raise SpacePublicationError(
            SpacePublicationErrorCode.NAMESPACE_INVALID,
            "Hugging Face namespace contains unsupported characters",
        )
    return value


def _expected_directories(paths: tuple[str, ...]) -> set[str]:
    directories: set[str] = set()
    for relative_path in paths:
        parent = Path(relative_path).parent
        while parent != Path("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def _candidate_tree_sha256(files: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative_path, payload in sorted(files.items()):
        digest.update(relative_path.encode())
        digest.update(b"\0")
        digest.update(_sha256_bytes(payload).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _require_project_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir() or not (resolved / "pyproject.toml").is_file():
        raise SpacePublicationError(
            SpacePublicationErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return resolved


def _raise_application_verification(message: str) -> None:
    raise SpacePublicationError(
        SpacePublicationErrorCode.PUBLIC_APPLICATION_VERIFICATION_FAILED,
        message,
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
