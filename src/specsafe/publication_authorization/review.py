from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from specsafe.hugging_face_publication_candidate.models import (
    FinalSanitizationReport,
    PublicationCandidateManifest,
)
from specsafe.publication_authorization.models import (
    AuthorizedArtifact,
    ExactPublicationAuthorizationDecision,
    PublicationAuthorizationGateChecks,
    PublicationTarget,
)

CANDIDATE_RELATIVE_DIRECTORY = "release/hugging-face/specsafe-bounded-negative-evidence-v1"
DECISION_RELATIVE_PATH = (
    "evidence/release-governance/specsafe-bounded-negative-evidence-v1/"
    "publication_authorization_decision.json"
)
EXPECTED_MANIFEST_SHA256 = "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
EXPECTED_MANIFEST_BYTE_COUNT = 4135
EXPECTED_FILES = (
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
_FORBIDDEN_MARKERS = (
    b"authorization: bearer",
    b"api_key=",
    b"access_token=",
    b"hf_token=",
    b'"prompt_text"',
    b'"raw_prompt_text"',
    b'"raw_logits"',
    b'"environment_variables"',
    b"/home/",
    b"/users/",
)
_WINDOWS_ABSOLUTE_PATH = re.compile(rb"[A-Za-z]:\\")


class PublicationAuthorizationErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "publication_authorization_invalid_project_root"
    CANDIDATE_DIRECTORY_INVALID = "publication_authorization_candidate_directory_invalid"
    MANIFEST_INTEGRITY_FAILED = "publication_authorization_manifest_integrity_failed"
    MANIFEST_SCHEMA_INVALID = "publication_authorization_manifest_schema_invalid"
    CANDIDATE_FILE_INTEGRITY_FAILED = "publication_authorization_file_integrity_failed"
    SANITIZATION_INVALID = "publication_authorization_sanitization_invalid"
    CANDIDATE_STATE_INVALID = "publication_authorization_candidate_state_invalid"
    COMMITTED_DECISION_MISMATCH = "publication_authorization_decision_mismatch"


class PublicationAuthorizationError(ValueError):
    def __init__(
        self,
        code: PublicationAuthorizationErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


def build_publication_authorization_decision(
    project_root: Path | str,
    *,
    write_output: bool = True,
) -> ExactPublicationAuthorizationDecision:
    root = _require_project_root(Path(project_root))
    candidate_root = root / CANDIDATE_RELATIVE_DIRECTORY
    _validate_candidate_directory(candidate_root)

    manifest_path = candidate_root / "publication_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    _require_exact_bytes(
        manifest_bytes,
        expected_sha256=EXPECTED_MANIFEST_SHA256,
        expected_byte_count=EXPECTED_MANIFEST_BYTE_COUNT,
        label="publication candidate manifest",
    )

    try:
        manifest = PublicationCandidateManifest.model_validate_json(manifest_bytes)
    except ValidationError as error:
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.MANIFEST_SCHEMA_INVALID,
            f"publication candidate manifest failed strict validation: {error}",
        ) from error

    authorized_files = _verify_candidate_files(candidate_root, manifest, manifest_bytes)
    sanitization = _load_sanitization_report(candidate_root)
    _validate_candidate_state(candidate_root, manifest, sanitization)

    by_name = {artifact.relative_path: artifact for artifact in authorized_files}
    decision = ExactPublicationAuthorizationDecision(
        schema_version="specsafe_exact_hugging_face_publication_authorization_v1",
        decision_id="specsafe-bounded-negative-evidence-publication-authorization-v1",
        decision_date="2026-07-10",
        source_commit="489ebb5",
        candidate_id=manifest.candidate_id,
        release_id=manifest.release_id,
        validity_marker=manifest.validity_marker,
        authorization_scope="exact_candidate_bytes_only",
        publication_manifest=AuthorizedArtifact(
            relative_path=(f"{CANDIDATE_RELATIVE_DIRECTORY}/publication_manifest.json"),
            sha256=EXPECTED_MANIFEST_SHA256,
            byte_count=EXPECTED_MANIFEST_BYTE_COUNT,
        ),
        sanitization_report=AuthorizedArtifact(
            relative_path=(f"{CANDIDATE_RELATIVE_DIRECTORY}/sanitization_report.json"),
            sha256=by_name["sanitization_report.json"].sha256,
            byte_count=by_name["sanitization_report.json"].byte_count,
        ),
        authorized_files=authorized_files,
        target=PublicationTarget(
            repository_type="dataset",
            repository_name=manifest.repository_name,
            visibility="public",
            gated=False,
            default_branch="main",
            namespace_policy="authenticated_owner_or_explicit_organization",
            credential_policy="managed_credential_never_logged_or_committed",
            license_identifier=manifest.license_identifier,
            exact_candidate_file_count=9,
            exact_candidate_files=EXPECTED_FILES,
        ),
        gate_checks=PublicationAuthorizationGateChecks(),
        decision_outcome="AUTHORIZE_EXACT_PUBLICATION",
        publication_authorized=True,
        publication_performed=False,
        authorization_revoked_by_candidate_drift=True,
        required_receipt_fields=(
            "repository_id",
            "repository_url",
            "namespace",
            "published_revision",
            "publication_manifest_sha256",
            "published_file_hashes",
            "published_at",
        ),
        blocked_actions=(
            "upload_any_file_outside_the_exact_candidate_allowlist",
            "modify_candidate_bytes_during_upload",
            "publish_if_authenticated_namespace_is_not_confirmed",
            "log_or_commit_hugging_face_credentials",
            "claim_calibrator_scheduler_or_production_promotion",
            "skip_remote_hash_and_visibility_verification",
        ),
        next_authorized_step=("controlled_hugging_face_dataset_publication_and_receipt"),
    )

    if write_output:
        output = root / DECISION_RELATIVE_PATH
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_authorization_decision_json(decision))
    return decision


def canonical_authorization_decision_json(
    decision: ExactPublicationAuthorizationDecision,
) -> bytes:
    return (json.dumps(decision.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def check_committed_publication_authorization_decision(
    project_root: Path | str,
) -> None:
    root = _require_project_root(Path(project_root))
    expected = canonical_authorization_decision_json(
        build_publication_authorization_decision(root, write_output=False)
    )
    output = root / DECISION_RELATIVE_PATH
    if not output.is_file() or output.read_bytes() != expected:
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.COMMITTED_DECISION_MISMATCH,
            "committed publication-authorization decision is missing or not canonical",
        )


def _validate_candidate_directory(candidate_root: Path) -> None:
    if not candidate_root.is_dir():
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.CANDIDATE_DIRECTORY_INVALID,
            "publication candidate directory is missing",
        )
    entries = tuple(candidate_root.iterdir())
    actual = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    if actual != set(EXPECTED_FILES):
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.CANDIDATE_DIRECTORY_INVALID,
            "publication candidate file allowlist does not match",
        )
    if any(path.is_dir() or path.is_symlink() for path in entries):
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.CANDIDATE_DIRECTORY_INVALID,
            "publication candidate contains nested or linked content",
        )


def _verify_candidate_files(
    candidate_root: Path,
    manifest: PublicationCandidateManifest,
    manifest_bytes: bytes,
) -> tuple[AuthorizedArtifact, ...]:
    expected_entries = {entry.relative_path: entry for entry in manifest.entries}
    artifacts: list[AuthorizedArtifact] = []
    for filename in EXPECTED_FILES:
        path = candidate_root / filename
        payload = path.read_bytes()
        if filename == "publication_manifest.json":
            expected_sha256 = EXPECTED_MANIFEST_SHA256
            expected_byte_count = EXPECTED_MANIFEST_BYTE_COUNT
            if payload != manifest_bytes:
                _raise_file_integrity(filename)
        else:
            entry = expected_entries.get(filename)
            if entry is None:
                _raise_file_integrity(filename)
            expected_sha256 = entry.sha256
            expected_byte_count = entry.byte_count
        if len(payload) != expected_byte_count or _sha256_bytes(payload) != expected_sha256:
            _raise_file_integrity(filename)
        artifacts.append(
            AuthorizedArtifact(
                relative_path=filename,
                sha256=expected_sha256,
                byte_count=expected_byte_count,
            )
        )
    return tuple(artifacts)


def _load_sanitization_report(candidate_root: Path) -> FinalSanitizationReport:
    try:
        return FinalSanitizationReport.model_validate_json(
            (candidate_root / "sanitization_report.json").read_bytes()
        )
    except ValidationError as error:
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.SANITIZATION_INVALID,
            f"final sanitization report failed strict validation: {error}",
        ) from error


def _validate_candidate_state(
    candidate_root: Path,
    manifest: PublicationCandidateManifest,
    sanitization: FinalSanitizationReport,
) -> None:
    conditions = (
        manifest.candidate_id == sanitization.candidate_id,
        manifest.validity_marker == sanitization.validity_marker,
        manifest.publication_status == "local_candidate_upload_not_authorized",
        manifest.public_upload_authorized is False,
        manifest.next_authorized_step == "explicit_publication_authorization_decision",
        sanitization.final_result == "PASS_LOCAL_CANDIDATE_ONLY",
        sanitization.forbidden_marker_matches == 0,
        sanitization.public_upload_authorized is False,
        sanitization.scanned_files == EXPECTED_FILES,
        all(sanitization.checks.model_dump().values()),
        manifest.gate_checks.public_upload_performed is False,
        manifest.license_identifier == "cc-by-4.0",
        manifest.license_scope == "sanitized_release_pack_original_materials_only",
    )
    if not all(conditions):
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.CANDIDATE_STATE_INVALID,
            "publication candidate is not at the exact authorization boundary",
        )

    readme = (candidate_root / "README.md").read_text(encoding="utf-8")
    required_readme = (
        "license: cc-by-4.0",
        "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        "candidate_not_promoted=true",
        "decision_outcome=KEEP_DIAGNOSTIC_ONLY",
        "failure_label=ranking_safety_regression",
        "## Forbidden claims",
    )
    if any(marker not in readme for marker in required_readme):
        _raise_state("dataset card lost a required negative-evidence boundary")

    license_text = (candidate_root / "LICENSE.md").read_text(encoding="utf-8")
    if "does not license" not in license_text or "CC BY 4.0" not in license_text:
        _raise_state("candidate license scope is not sufficiently bounded")

    rollback = (candidate_root / "ROLLBACK.md").read_text(encoding="utf-8")
    rollback_markers = (
        "public_upload_authorized=false",
        "Unpublish procedure",
        "Revoke or rotate publishing credentials",
    )
    if any(marker not in rollback for marker in rollback_markers):
        _raise_state("candidate rollback controls are incomplete")

    for filename in EXPECTED_FILES:
        payload = (candidate_root / filename).read_bytes()
        lowered = payload.lower()
        if any(marker in lowered for marker in _FORBIDDEN_MARKERS):
            _raise_state(f"forbidden content marker detected in {filename}")
        if _WINDOWS_ABSOLUTE_PATH.search(payload):
            _raise_state(f"local absolute path detected in {filename}")


def _require_exact_bytes(
    payload: bytes,
    *,
    expected_sha256: str,
    expected_byte_count: int,
    label: str,
) -> None:
    if len(payload) != expected_byte_count or _sha256_bytes(payload) != expected_sha256:
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.MANIFEST_INTEGRITY_FAILED,
            f"{label} does not match the reviewed bytes",
        )


def _require_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise PublicationAuthorizationError(
            PublicationAuthorizationErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return root


def _raise_file_integrity(filename: str) -> None:
    raise PublicationAuthorizationError(
        PublicationAuthorizationErrorCode.CANDIDATE_FILE_INTEGRITY_FAILED,
        f"publication candidate file does not match reviewed bytes: {filename}",
    )


def _raise_state(message: str) -> None:
    raise PublicationAuthorizationError(
        PublicationAuthorizationErrorCode.CANDIDATE_STATE_INVALID,
        message,
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
