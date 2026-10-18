from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from specsafe.hugging_face_space_prebuilt_candidate_v2 import (
    HuggingFaceSpacePrebuiltCandidateManifestV2,
)
from specsafe.hugging_face_space_publication_receipt import (
    check_committed_reconciliation,
    verify_local_publication_receipt,
)

from .models import LocalV2ReleaseReadiness, RemoteV2PreflightReport

V2_ROOT = Path("release/hugging-face-space-prebuilt-publication-v2/specsafe-reliability-lab")
V2_MANIFEST_PATH = V2_ROOT / "prebuilt_candidate_manifest_v2.json"
V2_CANDIDATE_PATH = V2_ROOT / "candidate/space"
V2_SOURCE_MANIFEST_PATH = Path(
    "release/hugging-face-space-publication-v2/specsafe-reliability-lab/"
    "publication_candidate_manifest_v2.json"
)
V1_RECEIPT_PATH = Path(
    "evidence/publication-receipts/specsafe-reliability-lab/"
    "hugging_face_space_publication_receipt.json"
)
EXPECTED_REPO_ID = "KaboKableMolefe/specsafe-reliability-lab"
EXPECTED_REPO_URL = "https://huggingface.co/spaces/KaboKableMolefe/specsafe-reliability-lab"
EXPECTED_V2_MANIFEST_SHA = "73924515752cf10d8b05cde9f2e89313a3c1337ea2eb305a0166c453b9caf853"
EXPECTED_V2_SOURCE_SHA = "057b8f59dbcaa76ef9c51c2a72a26adb059510717b7af87966096dd0a1a510d0"
EXPECTED_V2_TREE = "20a9847f98d9b0d353a37a2f035c61524c20c3a92b0298ec2076e9d9278773d0"
EXPECTED_SOURCE_TREE = "462988e7a1b30bdcdf66e87a25933356f67a0a83b86beaadc5fe810f4734d7bc"
EXPECTED_V1_TREE = "4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362"
EXPECTED_V1_REVISION = "453481cc16518ba8d8b425813aca4cfc74c2d0e8"
EXPECTED_EVIDENCE = "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
EXPECTED_FILES = (
    "README.md",
    "assets/index-BeNBJrmc.css",
    "assets/index-CAsY5KRm.js",
    "evidence/evidence_index.json",
    "index.html",
)
EXPECTED_BUILD_COMMANDS = (
    "npm ci",
    "npm run evidence:check",
    "npm run lint",
    "npm run test",
    "npm run build",
)
REQUIRED_README_MARKERS = (
    "sdk: static",
    "app_file: index.html",
    "decision=KEEP_DIAGNOSTIC_ONLY",
    "failure_label=ranking_safety_regression",
    "provider_side_build_required=false",
    "live_inference=false",
    "user_input_collection=false",
)
TERMINAL_STAGES = frozenset({"BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"})
REVISION_PATTERN = re.compile(r"[0-9a-f]{40}")


class V2ReleaseReadinessErrorCode(StrEnum):
    INVALID_REPO = "v2_readiness_invalid_repo"
    INVALID_MANIFEST = "v2_readiness_invalid_manifest"
    LOCAL_CANDIDATE_DRIFT = "v2_readiness_local_candidate_drift"
    RETAINED_V1_INVALID = "v2_readiness_retained_v1_invalid"
    REMOTE_REVISION_CHANGED = "v2_readiness_remote_revision_changed"
    REMOTE_STATE_INVALID = "v2_readiness_remote_state_invalid"
    REMOTE_FILE_DRIFT = "v2_readiness_remote_file_drift"
    REMOTE_APP_INVALID = "v2_readiness_remote_app_invalid"


class V2ReleaseReadinessError(RuntimeError):
    def __init__(self, code: V2ReleaseReadinessErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ReadOnlyExistingSpaceGateway(Protocol):
    def repository_state(self, repo_id: str, *, revision: str) -> Mapping[str, object]: ...

    def list_files(self, repo_id: str, *, revision: str) -> tuple[str, ...]: ...

    def read_file(self, repo_id: str, filename: str, *, revision: str) -> bytes: ...

    def fetch_application(self, application_url: str) -> Mapping[str, object]: ...


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _tree_sha256(files: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name, payload in sorted(files.items()):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(payload).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _root(project_root: Path | str) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_REPO,
            "project_root must be the SpecSafe repository root",
        )
    return root


def _source_manifest_checked(
    root: Path, manifest: HuggingFaceSpacePrebuiltCandidateManifestV2
) -> None:
    source_path = root / V2_SOURCE_MANIFEST_PATH
    if not source_path.is_file() or source_path.is_symlink():
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_MANIFEST,
            "V2 source candidate manifest is missing or linked",
        )
    source_payload = source_path.read_bytes()
    if _sha256(source_payload) != manifest.source_candidate_manifest_sha256:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_MANIFEST,
            "V2 source candidate manifest hash drifted",
        )


def _load_manifest(root: Path) -> HuggingFaceSpacePrebuiltCandidateManifestV2:
    path = root / V2_MANIFEST_PATH
    if not path.is_file() or path.is_symlink():
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_MANIFEST,
            "V2 prebuilt manifest is missing or linked",
        )
    payload = path.read_bytes()
    if _sha256(payload) != EXPECTED_V2_MANIFEST_SHA:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_MANIFEST,
            "V2 prebuilt manifest changed from the merged, frozen release",
        )
    try:
        manifest = HuggingFaceSpacePrebuiltCandidateManifestV2.model_validate_json(payload)
    except ValidationError as error:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_MANIFEST,
            "V2 prebuilt manifest failed strict schema validation",
        ) from error

    paths = tuple(item.relative_path for item in manifest.files)
    conditions = (
        manifest.candidate_tree_sha256 == EXPECTED_V2_TREE,
        manifest.source_candidate_tree_sha256 == EXPECTED_SOURCE_TREE,
        manifest.source_candidate_manifest_sha256 == EXPECTED_V2_SOURCE_SHA,
        manifest.evidence_index_sha256 == EXPECTED_EVIDENCE,
        manifest.evidence_index_byte_count == 9206,
        manifest.exact_candidate_file_count == 5,
        paths == EXPECTED_FILES,
        tuple(manifest.build_commands) == EXPECTED_BUILD_COMMANDS,
        manifest.provider_side_build_required is False,
        manifest.actual_space_publication is False,
        manifest.remote_mutation is False,
        manifest.live_inference is False,
        manifest.user_input_collection is False,
        manifest.metadata.sdk == "static",
        manifest.metadata.app_file == "index.html",
    )
    if not all(conditions):
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.INVALID_MANIFEST,
            "V2 prebuilt manifest is outside the frozen release boundary",
        )
    _source_manifest_checked(root, manifest)
    return manifest


def _verify_candidate(root: Path, manifest: HuggingFaceSpacePrebuiltCandidateManifestV2) -> None:
    directory = root / V2_CANDIDATE_PATH
    if not directory.is_dir() or directory.is_symlink():
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 static candidate directory is missing or linked",
        )

    actual: dict[str, bytes] = {}
    actual_dirs: set[str] = set()
    for path in directory.rglob("*"):
        name = path.relative_to(directory).as_posix()
        if path.is_symlink():
            raise V2ReleaseReadinessError(
                V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
                f"V2 static candidate contains linked content: {name}",
            )
        if path.is_dir():
            actual_dirs.add(name)
        elif path.is_file():
            actual[name] = path.read_bytes()
        else:
            raise V2ReleaseReadinessError(
                V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
                f"V2 static candidate contains unsupported content: {name}",
            )
    if tuple(sorted(actual)) != EXPECTED_FILES:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 candidate file allowlist differs from committed release",
        )
    expected_dirs = {"assets", "evidence"}
    if actual_dirs != expected_dirs:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 candidate directory allowlist differs from committed release",
        )

    by_path = {item.relative_path: item for item in manifest.files}
    for name, payload in actual.items():
        item = by_path[name]
        if len(payload) != item.byte_count or _sha256(payload) != item.sha256:
            raise V2ReleaseReadinessError(
                V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
                f"V2 candidate byte hash drifted: {name}",
            )
    if _tree_sha256(actual) != EXPECTED_V2_TREE:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 candidate aggregate tree SHA-256 drifted",
        )

    readme = actual["README.md"].decode("utf-8")
    if any(marker not in readme for marker in REQUIRED_README_MARKERS):
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 Space README lost the static reliability boundary",
        )
    if "app_build_command:" in readme:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 static candidate reintroduced provider-side build",
        )
    html = actual["index.html"].decode("utf-8")
    if "SpecSafe" not in html or 'id="root"' not in html:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
            "V2 static candidate HTML markers are missing",
        )
    for asset in ("assets/index-BeNBJrmc.css", "assets/index-CAsY5KRm.js"):
        if f"/{asset}" not in html:
            raise V2ReleaseReadinessError(
                V2ReleaseReadinessErrorCode.LOCAL_CANDIDATE_DRIFT,
                f"V2 static candidate HTML lost asset reference: {asset}",
            )


def _verify_retained_v1(root: Path) -> tuple[str, tuple[str, ...], tuple[object, ...], str]:
    try:
        local = verify_local_publication_receipt(root)
        check_committed_reconciliation(root)
    except (RuntimeError, ValueError, OSError) as error:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.RETAINED_V1_INVALID,
            "V1 retained receipt or reconciliation is not independently valid",
        ) from error

    receipt = local.receipt
    if (
        receipt.repository_id != EXPECTED_REPO_ID
        or receipt.repository_url != EXPECTED_REPO_URL
        or receipt.published_revision != EXPECTED_V1_REVISION
        or receipt.candidate_tree_sha256 != EXPECTED_V1_TREE
        or receipt.evidence_index_sha256 != EXPECTED_EVIDENCE
    ):
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.RETAINED_V1_INVALID,
            "V1 rollback lineage is outside the retained publication boundary",
        )
    return (
        receipt.published_revision,
        receipt.remote_files,
        receipt.published_file_hashes,
        (receipt.application_url),
    )


def build_local_v2_release_readiness(project_root: Path | str) -> LocalV2ReleaseReadiness:
    root = _root(project_root)
    manifest = _load_manifest(root)
    _verify_candidate(root, manifest)
    _verify_retained_v1(root)
    return LocalV2ReleaseReadiness(
        schema_version="specsafe_space_v2_local_release_readiness_v1",
        target_repository_id=EXPECTED_REPO_ID,
        target_repository_url=EXPECTED_REPO_URL,
        v2_prebuilt_manifest_sha256=EXPECTED_V2_MANIFEST_SHA,
        v2_prebuilt_tree_sha256=EXPECTED_V2_TREE,
        v2_source_manifest_sha256=manifest.source_candidate_manifest_sha256,
        v2_source_tree_sha256=EXPECTED_SOURCE_TREE,
        v2_prebuilt_file_count=5,
        evidence_index_sha256=EXPECTED_EVIDENCE,
        retained_v1_published_revision=EXPECTED_V1_REVISION,
        retained_v1_candidate_tree_sha256=EXPECTED_V1_TREE,
        local_v2_candidate_verified=True,
        local_v1_receipt_verified=True,
        local_v1_reconciliation_verified=True,
        next_step="read_only_remote_preflight_existing_space",
    )


def _verify_remote_application(
    response: Mapping[str, object],
    application_url: str,
) -> None:
    if (
        response.get("application_url") != application_url
        or response.get("status_code") != 200
        or not isinstance(response.get("content_type"), str)
        or "text/html" not in str(response["content_type"]).lower()
        or not isinstance(response.get("body"), bytes)
    ):
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.REMOTE_APP_INVALID,
            "existing Space public application did not satisfy the retained response contract",
        )
    html = response["body"].decode("utf-8", errors="replace")
    if "SpecSafe" not in html or 'id="root"' not in html:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.REMOTE_APP_INVALID,
            "existing Space public application lost required HTML markers",
        )


def preflight_existing_v2_space(
    project_root: Path | str,
    gateway: ReadOnlyExistingSpaceGateway,
) -> RemoteV2PreflightReport:
    root = _root(project_root)
    local = build_local_v2_release_readiness(root)
    revision, files, hashes, application_url = _verify_retained_v1(root)
    state = gateway.repository_state(EXPECTED_REPO_ID, revision="main")
    observed = state.get("sha")
    if not isinstance(observed, str) or not REVISION_PATTERN.fullmatch(observed):
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.REMOTE_STATE_INVALID,
            "existing Space main revision is missing or malformed",
        )
    if observed != revision:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.REMOTE_REVISION_CHANGED,
            "existing Space main changed since the retained V1 receipt; stop for investigation",
        )
    if (
        state.get("id") != EXPECTED_REPO_ID
        or state.get("private") is not False
        or state.get("gated") not in (False, None)
        or state.get("sdk") != "static"
        or state.get("stage") in TERMINAL_STAGES
    ):
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.REMOTE_STATE_INVALID,
            "existing Space main is not the expected public, ungated, static baseline",
        )

    remote_files = gateway.list_files(EXPECTED_REPO_ID, revision=observed)
    if remote_files != files:
        raise V2ReleaseReadinessError(
            V2ReleaseReadinessErrorCode.REMOTE_FILE_DRIFT,
            "existing Space main file allowlist differs from retained V1 publication",
        )

    expected_by_path = {item.relative_path: item for item in hashes}
    for filename in remote_files:
        payload = gateway.read_file(EXPECTED_REPO_ID, filename, revision=observed)
        item = expected_by_path[filename]
        if len(payload) != item.byte_count or _sha256(payload) != item.sha256:
            raise V2ReleaseReadinessError(
                V2ReleaseReadinessErrorCode.REMOTE_FILE_DRIFT,
                f"existing Space file drifted: {filename}",
            )

    application = gateway.fetch_application(application_url)
    _verify_remote_application(application, application_url)
    return RemoteV2PreflightReport(
        schema_version="specsafe_space_v2_remote_preflight_report_v1",
        target_repository_id=EXPECTED_REPO_ID,
        observed_current_revision=observed,
        retained_v1_rollback_revision=revision,
        v2_prebuilt_tree_sha256=local.v2_prebuilt_tree_sha256,
        existing_v1_remote_files_verified=True,
        current_remote_revision_verified=True,
        public_application_verified=True,
        next_step="design_and_approve_revision_guarded_v2_update",
    )
