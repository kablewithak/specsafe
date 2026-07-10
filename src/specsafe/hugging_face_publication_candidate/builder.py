from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from specsafe.bounded_negative_evidence.models import (
    BoundedNegativeEvidenceReleaseManifest,
    BoundedNegativeEvidenceReleaseSummary,
)
from specsafe.hugging_face_publication_candidate.models import (
    FinalSanitizationChecks,
    FinalSanitizationReport,
    PublicationCandidateArtifact,
    PublicationCandidateEntry,
    PublicationCandidateGateChecks,
    PublicationCandidateManifest,
)
from specsafe.publication_readiness.models import (
    BoundedNegativeEvidencePublicationReadinessDecision,
)

CANDIDATE_ID = "specsafe-bounded-negative-evidence-hf-candidate-v1"
SOURCE_RELEASE_DIRECTORY = "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1"
SOURCE_READINESS_DECISION = (
    "evidence/release-governance/specsafe-bounded-negative-evidence-v1/"
    "publication_readiness_decision.json"
)
CANDIDATE_RELATIVE_DIRECTORY = "release/hugging-face/specsafe-bounded-negative-evidence-v1"
EXPECTED_READINESS_DECISION_SHA256 = (
    "51cf44163f1656a62035475ad217271046bc0cf6c8f21d12bff22f65a5341790"
)
EXPECTED_READINESS_DECISION_BYTE_COUNT = 4563
EXPECTED_SOURCE_MANIFEST_SHA256 = "10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b"
EXPECTED_SOURCE_MANIFEST_BYTE_COUNT = 975
EXPECTED_SOURCE_FILES = (
    PublicationCandidateArtifact(
        relative_path=(
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/README.md"
        ),
        sha256="79906e66d11eb3d5c2c396167a441be669e6105b47edd335f0325a0815c8689f",
        byte_count=3008,
    ),
    PublicationCandidateArtifact(
        relative_path=(
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/"
            "evidence_boundary.md"
        ),
        sha256="8053d6c01a816280847b79d8bc036f14733dd7bc2d12f27bedf35934ef166967",
        byte_count=1577,
    ),
    PublicationCandidateArtifact(
        relative_path=(
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/"
            "release_summary.json"
        ),
        sha256="264886c6bb6d2490bb95b43a29506b04437972e5a42c6688db7dc7d124f8df90",
        byte_count=4470,
    ),
)
_EXPECTED_SOURCE_FILENAMES = {
    "README.md",
    "evidence_boundary.md",
    "release_summary.json",
    "release_manifest.json",
}
_EXPECTED_PRE_MANIFEST_FILENAMES = {
    "ATTRIBUTION.md",
    "LICENSE.md",
    "README.md",
    "ROLLBACK.md",
    "evidence_boundary.md",
    "release_summary.json",
    "sanitization_report.json",
    "source_release_manifest.json",
}
_EXPECTED_CANDIDATE_FILENAMES = _EXPECTED_PRE_MANIFEST_FILENAMES | {"publication_manifest.json"}
_BLOCKED_SUFFIXES = {
    ".env",
    ".jsonl",
    ".log",
    ".pt",
    ".safetensors",
    ".zip",
}
_FORBIDDEN_CONTENT_MARKERS = (
    b'"prompt_text"',
    b'"raw_prompt_text"',
    b'"raw_logits"',
    b'"environment_variables"',
    b"authorization: bearer",
    b"api_key=",
    b"access_token=",
    b"hf_token=",
    b"/home/",
    b"/users/",
)
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(rb"[A-Za-z]:\\")
_HUB_YAML = (
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


class HuggingFacePublicationCandidateErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_candidate_invalid_project_root"
    SOURCE_MISSING = "hf_candidate_source_missing"
    SOURCE_INTEGRITY_FAILED = "hf_candidate_source_integrity_failed"
    SOURCE_SCHEMA_INVALID = "hf_candidate_source_schema_invalid"
    SOURCE_STATE_INVALID = "hf_candidate_source_state_invalid"
    OUTPUT_OUTSIDE_REPOSITORY = "hf_candidate_output_outside_repository"
    OUTPUT_ALREADY_EXISTS = "hf_candidate_output_already_exists"
    SANITIZATION_FAILED = "hf_candidate_sanitization_failed"
    COMMITTED_CANDIDATE_MISMATCH = "hf_candidate_committed_candidate_mismatch"


class HuggingFacePublicationCandidateError(ValueError):
    def __init__(
        self,
        code: HuggingFacePublicationCandidateErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


def build_publication_candidate_payloads(
    project_root: Path | str,
) -> dict[str, bytes]:
    root = _require_project_root(Path(project_root))
    decision, source_manifest, source_summary = _load_verified_sources(root)
    _validate_source_state(decision, source_manifest, source_summary)

    source_root = root / SOURCE_RELEASE_DIRECTORY
    source_readme = (source_root / "README.md").read_bytes()
    payloads = {
        "ATTRIBUTION.md": _render_attribution(),
        "LICENSE.md": _render_license(),
        "README.md": _HUB_YAML + source_readme,
        "ROLLBACK.md": _render_rollback_runbook(),
        "evidence_boundary.md": (source_root / "evidence_boundary.md").read_bytes(),
        "release_summary.json": (source_root / "release_summary.json").read_bytes(),
        "source_release_manifest.json": (source_root / "release_manifest.json").read_bytes(),
    }
    report = _build_sanitization_report()
    payloads["sanitization_report.json"] = _canonical_json_bytes(report.model_dump(mode="json"))
    _validate_candidate_payloads(payloads)

    manifest = _build_publication_manifest(decision, payloads)
    payloads["publication_manifest.json"] = _canonical_json_bytes(manifest.model_dump(mode="json"))
    return payloads


def write_publication_candidate(
    project_root: Path | str,
    *,
    output_directory: Path | str | None = None,
) -> Path:
    root = _require_project_root(Path(project_root))
    output = _resolve_output_directory(root, output_directory)
    if output.exists():
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.OUTPUT_ALREADY_EXISTS,
            "publication candidate already exists; use check mode for committed artifacts",
        )

    payloads = build_publication_candidate_payloads(root)
    output.mkdir(parents=True)
    for filename in sorted(_EXPECTED_PRE_MANIFEST_FILENAMES):
        (output / filename).write_bytes(payloads[filename])
    (output / "publication_manifest.json").write_bytes(payloads["publication_manifest.json"])
    return output


def check_committed_publication_candidate(project_root: Path | str) -> None:
    root = _require_project_root(Path(project_root))
    output = _resolve_output_directory(root, None)
    expected = build_publication_candidate_payloads(root)
    if not output.is_dir():
        _raise_committed_mismatch("committed publication candidate directory is missing")

    entries = tuple(output.iterdir())
    actual_files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    if actual_files != _EXPECTED_CANDIDATE_FILENAMES:
        _raise_committed_mismatch("publication candidate file allowlist does not match")
    if any(path.is_dir() or path.is_symlink() for path in entries):
        _raise_committed_mismatch("publication candidate contains nested or linked content")

    for filename, expected_bytes in expected.items():
        path = output / filename
        if path.read_bytes() != expected_bytes:
            _raise_committed_mismatch(
                f"committed publication candidate file is not canonical: {filename}"
            )


def _load_verified_sources(
    root: Path,
) -> tuple[
    BoundedNegativeEvidencePublicationReadinessDecision,
    BoundedNegativeEvidenceReleaseManifest,
    BoundedNegativeEvidenceReleaseSummary,
]:
    decision_bytes = _require_exact_file(
        root / SOURCE_READINESS_DECISION,
        EXPECTED_READINESS_DECISION_SHA256,
        EXPECTED_READINESS_DECISION_BYTE_COUNT,
    )
    source_root = root / SOURCE_RELEASE_DIRECTORY
    _validate_source_release_directory(source_root)
    manifest_bytes = _require_exact_file(
        source_root / "release_manifest.json",
        EXPECTED_SOURCE_MANIFEST_SHA256,
        EXPECTED_SOURCE_MANIFEST_BYTE_COUNT,
    )
    summary_bytes = _require_exact_file(
        source_root / "release_summary.json",
        EXPECTED_SOURCE_FILES[2].sha256,
        EXPECTED_SOURCE_FILES[2].byte_count,
    )
    for artifact in EXPECTED_SOURCE_FILES[:2]:
        _require_exact_file(
            root / artifact.relative_path,
            artifact.sha256,
            artifact.byte_count,
        )

    try:
        decision = BoundedNegativeEvidencePublicationReadinessDecision.model_validate_json(
            decision_bytes
        )
        manifest = BoundedNegativeEvidenceReleaseManifest.model_validate_json(manifest_bytes)
        summary = BoundedNegativeEvidenceReleaseSummary.model_validate_json(summary_bytes)
    except ValidationError as error:
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_SCHEMA_INVALID,
            f"publication source failed strict schema validation: {error}",
        ) from error
    return decision, manifest, summary


def _validate_source_state(
    decision: BoundedNegativeEvidencePublicationReadinessDecision,
    manifest: BoundedNegativeEvidenceReleaseManifest,
    summary: BoundedNegativeEvidenceReleaseSummary,
) -> None:
    conditions = (
        decision.decision_outcome == "READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY",
        decision.publication_candidate_assembly_authorized is True,
        decision.public_upload_authorized is False,
        decision.next_authorized_step
        == "assemble_exact_hugging_face_publication_candidate_without_upload",
        decision.release_manifest.sha256 == EXPECTED_SOURCE_MANIFEST_SHA256,
        decision.release_manifest.byte_count == EXPECTED_SOURCE_MANIFEST_BYTE_COUNT,
        decision.license_decision.license_identifier == "cc-by-4.0",
        decision.license_decision.license_scope == "sanitized_release_pack_original_materials_only",
        decision.hugging_face_metadata_draft.repository_type == "dataset",
        decision.hugging_face_metadata_draft.card_metadata_status == "prepared_not_applied",
        tuple(item.model_dump() for item in decision.release_files)
        == tuple(item.model_dump() for item in EXPECTED_SOURCE_FILES),
        manifest.release_id == summary.release_id == decision.release_id,
        manifest.validity_marker == summary.validity_marker == decision.validity_marker,
        manifest.publication_status == summary.publication_status == "local_pack_only",
        summary.candidate_not_promoted is True,
        summary.threshold_promotion_authorized is False,
        summary.scheduler_promotion_authorized is False,
        summary.production_claim_authorized is False,
    )
    if not all(conditions):
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_STATE_INVALID,
            "reviewed release and readiness decision are not at the assembly boundary",
        )


def _build_sanitization_report() -> FinalSanitizationReport:
    return FinalSanitizationReport(
        schema_version=("specsafe_hugging_face_publication_candidate_sanitization_report_v1"),
        candidate_id=CANDIDATE_ID,
        review_date="2026-07-10",
        source_commit="38b2993",
        validity_marker="CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        publication_status="local_candidate_upload_not_authorized",
        public_upload_authorized=False,
        scanned_file_count=9,
        scanned_files=tuple(sorted(_EXPECTED_CANDIDATE_FILENAMES)),
        forbidden_marker_matches=0,
        checks=FinalSanitizationChecks(),
        final_result="PASS_LOCAL_CANDIDATE_ONLY",
        next_authorized_step="explicit_publication_authorization_decision",
    )


def _build_publication_manifest(
    decision: BoundedNegativeEvidencePublicationReadinessDecision,
    payloads: dict[str, bytes],
) -> PublicationCandidateManifest:
    derivations = {
        "README.md": "reviewed_source_with_hub_metadata",
        "evidence_boundary.md": "reviewed_source_copy",
        "release_summary.json": "reviewed_source_copy",
        "source_release_manifest.json": "reviewed_source_copy",
        "ATTRIBUTION.md": "governance_generated",
        "LICENSE.md": "governance_generated",
        "ROLLBACK.md": "governance_generated",
        "sanitization_report.json": "governance_generated",
    }
    entries = tuple(
        PublicationCandidateEntry(
            relative_path=filename,
            sha256=_sha256_bytes(payload),
            byte_count=len(payload),
            derivation=derivations[filename],
        )
        for filename, payload in sorted(payloads.items())
    )
    return PublicationCandidateManifest(
        schema_version="specsafe_hugging_face_publication_candidate_manifest_v1",
        candidate_id=CANDIDATE_ID,
        repository_type="dataset",
        repository_name=decision.hugging_face_metadata_draft.repository_name,
        release_id=decision.release_id,
        source_commit="38b2993",
        validity_marker=decision.validity_marker,
        license_identifier=decision.license_decision.license_identifier,
        license_scope=decision.license_decision.license_scope,
        publication_status="local_candidate_upload_not_authorized",
        public_upload_authorized=False,
        source_readiness_decision=PublicationCandidateArtifact(
            relative_path=SOURCE_READINESS_DECISION,
            sha256=EXPECTED_READINESS_DECISION_SHA256,
            byte_count=EXPECTED_READINESS_DECISION_BYTE_COUNT,
        ),
        source_release_manifest=PublicationCandidateArtifact(
            relative_path=f"{SOURCE_RELEASE_DIRECTORY}/release_manifest.json",
            sha256=EXPECTED_SOURCE_MANIFEST_SHA256,
            byte_count=EXPECTED_SOURCE_MANIFEST_BYTE_COUNT,
        ),
        reviewed_source_files=EXPECTED_SOURCE_FILES,
        manifest_scope="all_candidate_files_except_manifest_itself",
        file_count=8,
        entries=entries,
        gate_checks=PublicationCandidateGateChecks(),
        next_authorized_step="explicit_publication_authorization_decision",
    )


def _render_license() -> bytes:
    lines = [
        "# License",
        "",
        "SpecSafe Bounded Negative-Evidence Release v1 © 2026 Kabo Molefe.",
        "",
        (
            "The original sanitized materials assembled in this publication candidate are "
            "licensed under the Creative Commons Attribution 4.0 International license "
            "(CC BY 4.0)."
        ),
        "",
        "Canonical license reference:",
        "",
        "https://creativecommons.org/licenses/by/4.0/",
        "",
        "## Included scope",
        "",
        "- The dataset card and its Hugging Face metadata.",
        "- The sanitized aggregate evidence and evidence-boundary materials.",
        ("- The publication attribution, rollback, manifest, and sanitization materials."),
        "",
        "## Excluded scope",
        "",
        "This license notice does not license:",
        "",
        "- the SpecSafe source-code repository as a whole;",
        "- retained Kaggle archives;",
        "- raw trace or prompt records;",
        "- the candidate calibrator artifact; or",
        "- upstream models and their outputs.",
        "",
        (
            "No warranties are provided. This is an engineering distribution choice, "
            "not legal advice."
        ),
        "",
    ]
    return "\n".join(lines).encode()


def _render_attribution() -> bytes:
    lines = [
        "# Attribution",
        "",
        "## Licensed material",
        "",
        "SpecSafe Bounded Negative-Evidence Release v1",
        "",
        "## Creator",
        "",
        "Kabo Molefe",
        "",
        "## Copyright",
        "",
        "© 2026 Kabo Molefe",
        "",
        "## License",
        "",
        "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "",
        "https://creativecommons.org/licenses/by/4.0/",
        "",
        "## Attribution notice",
        "",
        (
            "SpecSafe Bounded Negative-Evidence Release v1 © 2026 Kabo Molefe, "
            "licensed under CC BY 4.0."
        ),
        "",
        "## Changes in this publication candidate",
        "",
        (
            "Hugging Face YAML metadata, bounded license material, attribution, a "
            "rollback runbook, a publication manifest, and a final sanitization report "
            "were added around the exact reviewed aggregate release materials. The "
            "reviewed metrics, failure label, non-promotion decision, and claim boundaries "
            "were not changed."
        ),
        "",
        (
            "The CC BY 4.0 scope is limited to the original sanitized "
            "publication-candidate materials listed in `LICENSE.md`."
        ),
        "",
    ]
    return "\n".join(lines).encode()


def _render_rollback_runbook() -> bytes:
    lines = [
        "# Rollback and Unpublish Runbook",
        "",
        "## Current state",
        "",
        "```text",
        "publication_status=local_candidate_upload_not_authorized",
        "public_upload_authorized=false",
        "```",
        "",
        "No remote repository is created or modified by this candidate builder.",
        "",
        "## Pre-publication stop",
        "",
        (
            "Before any upload, rerun the canonical candidate check and obtain an explicit "
            "publication-authorization decision tied to the exact "
            "`publication_manifest.json` SHA-256. Stop if any byte, claim, license scope, "
            "or sanitization result differs."
        ),
        "",
        "## Unpublish procedure after a future authorized release",
        "",
        (
            "1. Disable public access or remove the Hugging Face Dataset repository "
            "through the repository settings."
        ),
        (
            "2. Record the repository URL, last published revision, publication-manifest "
            "SHA-256, reason, actor, and timestamp in a local incident note."
        ),
        "3. Confirm that anonymous access no longer returns the publication candidate.",
        (
            "4. Preserve the canonical local candidate and governance evidence; do not "
            "rewrite the consumed holdout result."
        ),
        (
            "5. Revoke or rotate publishing credentials if exposure, compromise, or "
            "unauthorized use is suspected."
        ),
        (
            "6. Correct the local source or governance decision before considering a new "
            "publication candidate."
        ),
        "",
        "## Rollback triggers",
        "",
        "- source hash or publication-manifest drift;",
        "- missing negative-evidence or non-promotion labels;",
        "- license-scope error;",
        ("- secret, local-path, private-data, raw-trace, archive, or model-payload exposure;"),
        "- unsupported positive, scheduler, or production claim;",
        "- upload performed without explicit authorization.",
        "",
        (
            "Unpublishing limits future access but cannot revoke copies already obtained "
            "under CC BY 4.0."
        ),
        "",
    ]
    return "\n".join(lines).encode()


def _validate_candidate_payloads(payloads: dict[str, bytes]) -> None:
    if set(payloads) != _EXPECTED_PRE_MANIFEST_FILENAMES:
        _raise_sanitization("publication candidate pre-manifest allowlist does not match")
    for filename, payload in payloads.items():
        if Path(filename).suffix.lower() in _BLOCKED_SUFFIXES:
            _raise_sanitization(f"blocked publication candidate suffix: {filename}")
        lowered = payload.lower()
        for marker in _FORBIDDEN_CONTENT_MARKERS:
            if marker in lowered:
                _raise_sanitization(f"forbidden content marker in {filename}: {marker!r}")
        if _WINDOWS_ABSOLUTE_PATH_PATTERN.search(payload):
            _raise_sanitization(f"local absolute path detected in {filename}")

    readme = payloads["README.md"].decode()
    required_readme_markers = (
        _HUB_YAML.decode(),
        "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        "candidate_not_promoted=true",
        "decision_outcome=KEEP_DIAGNOSTIC_ONLY",
        "failure_label=ranking_safety_regression",
        "## Forbidden claims",
    )
    if any(marker not in readme for marker in required_readme_markers):
        _raise_sanitization("publication candidate dataset card lost a required boundary")

    license_text = payloads["LICENSE.md"].decode()
    if (
        "sanitized materials" not in license_text
        or "does not license" not in license_text
        or "upstream models and their outputs" not in license_text
    ):
        _raise_sanitization("license scope is not sufficiently bounded")

    rollback = payloads["ROLLBACK.md"].decode()
    required_rollback_markers = (
        "public_upload_authorized=false",
        "explicit publication-authorization decision",
        "Unpublish procedure",
        "Revoke or rotate publishing credentials",
        "cannot revoke copies already obtained",
    )
    if any(marker not in rollback for marker in required_rollback_markers):
        _raise_sanitization("rollback runbook is incomplete")


def _validate_final_candidate_payloads(payloads: dict[str, bytes]) -> None:
    if set(payloads) != _EXPECTED_CANDIDATE_FILENAMES:
        _raise_sanitization("final publication candidate allowlist does not match")
    _scan_payloads(payloads)


def _scan_payloads(payloads: dict[str, bytes]) -> None:
    for filename, payload in payloads.items():
        if Path(filename).suffix.lower() in _BLOCKED_SUFFIXES:
            _raise_sanitization(f"blocked publication candidate suffix: {filename}")
        lowered = payload.lower()
        for marker in _FORBIDDEN_CONTENT_MARKERS:
            if marker in lowered:
                _raise_sanitization(f"forbidden content marker in {filename}: {marker!r}")
        if _WINDOWS_ABSOLUTE_PATH_PATTERN.search(payload):
            _raise_sanitization(f"local absolute path detected in {filename}")


def _validate_source_release_directory(source_root: Path) -> None:
    if not source_root.is_dir():
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_MISSING,
            "reviewed source release directory is missing",
        )
    entries = tuple(source_root.iterdir())
    actual_files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    if actual_files != _EXPECTED_SOURCE_FILENAMES:
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_STATE_INVALID,
            "reviewed source release file allowlist does not match",
        )
    if any(path.is_dir() or path.is_symlink() for path in entries):
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_STATE_INVALID,
            "reviewed source release contains nested or linked content",
        )


def _require_exact_file(path: Path, expected_sha256: str, expected_size: int) -> bytes:
    if not path.is_file():
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_MISSING,
            f"required publication source is missing: {path}",
        )
    payload = path.read_bytes()
    if len(payload) != expected_size or _sha256_bytes(payload) != expected_sha256:
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.SOURCE_INTEGRITY_FAILED,
            f"publication source does not match reviewed bytes: {path}",
        )
    return payload


def _require_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return root


def _resolve_output_directory(
    root: Path,
    output_directory: Path | str | None,
) -> Path:
    if output_directory is None:
        output = root / CANDIDATE_RELATIVE_DIRECTORY
    else:
        candidate = Path(output_directory).expanduser()
        output = candidate if candidate.is_absolute() else root / candidate
    output = output.resolve()
    if not output.is_relative_to(root):
        raise HuggingFacePublicationCandidateError(
            HuggingFacePublicationCandidateErrorCode.OUTPUT_OUTSIDE_REPOSITORY,
            "publication candidate output must remain inside the repository root",
        )
    return output


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _raise_sanitization(message: str) -> None:
    raise HuggingFacePublicationCandidateError(
        HuggingFacePublicationCandidateErrorCode.SANITIZATION_FAILED,
        message,
    )


def _raise_committed_mismatch(message: str) -> None:
    raise HuggingFacePublicationCandidateError(
        HuggingFacePublicationCandidateErrorCode.COMMITTED_CANDIDATE_MISMATCH,
        message,
    )
