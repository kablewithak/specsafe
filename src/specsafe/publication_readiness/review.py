from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from specsafe.bounded_negative_evidence.models import (
    BoundedNegativeEvidenceReleaseManifest,
    BoundedNegativeEvidenceReleaseSummary,
)
from specsafe.publication_readiness.models import (
    BoundedNegativeEvidencePublicationReadinessDecision,
    HuggingFaceMetadataDraft,
    PublicationLicenseDecision,
    PublicationReadinessGateChecks,
    ReviewedReleaseArtifact,
)

RELEASE_ID = "specsafe-bounded-negative-evidence-v1"
RELEASE_RELATIVE_DIRECTORY = (
    "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1"
)
MANIFEST_RELATIVE_PATH = f"{RELEASE_RELATIVE_DIRECTORY}/release_manifest.json"
DECISION_RELATIVE_PATH = (
    "evidence/release-governance/specsafe-bounded-negative-evidence-v1/"
    "publication_readiness_decision.json"
)
EXPECTED_MANIFEST_SHA256 = "10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b"
EXPECTED_MANIFEST_BYTE_COUNT = 975
EXPECTED_RELEASE_FILENAMES = {
    "README.md",
    "evidence_boundary.md",
    "release_summary.json",
    "release_manifest.json",
}
EXPECTED_ENTRY_PATHS = (
    "README.md",
    "evidence_boundary.md",
    "release_summary.json",
)
_REQUIRED_README_MARKERS = (
    "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
    "publication_status=local_pack_only",
    "candidate_not_promoted=true",
    "threshold_promotion_authorized=false",
    "scheduler_promotion_authorized=false",
    "production_claim_authorized=false",
    "decision_outcome=KEEP_DIAGNOSTIC_ONLY",
    "failure_label=ranking_safety_regression",
    "## Forbidden claims",
)
_REQUIRED_BOUNDARY_MARKERS = (
    "validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
    "ranking_safety_passed=false",
    "promotion_blocked=true",
    "conservative_fallback_required=true",
    "license_selection_pending=true",
    "explicit_publication_authorization_required=true",
)


class PublicationReadinessErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "publication_readiness_invalid_project_root"
    RELEASE_DIRECTORY_INVALID = "publication_readiness_release_directory_invalid"
    MANIFEST_INTEGRITY_FAILED = "publication_readiness_manifest_integrity_failed"
    MANIFEST_SCHEMA_INVALID = "publication_readiness_manifest_schema_invalid"
    RELEASE_FILE_INTEGRITY_FAILED = "publication_readiness_release_file_integrity_failed"
    SUMMARY_SCHEMA_INVALID = "publication_readiness_summary_schema_invalid"
    RELEASE_STATE_INVALID = "publication_readiness_release_state_invalid"
    CLAIM_BOUNDARY_FAILED = "publication_readiness_claim_boundary_failed"
    COMMITTED_DECISION_MISMATCH = "publication_readiness_committed_decision_mismatch"


class PublicationReadinessError(ValueError):
    def __init__(self, code: PublicationReadinessErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def build_publication_readiness_decision(
    project_root: Path | str,
    *,
    write_output: bool = True,
) -> BoundedNegativeEvidencePublicationReadinessDecision:
    root = _require_project_root(Path(project_root))
    release_root = root / RELEASE_RELATIVE_DIRECTORY
    _validate_release_directory(release_root)

    manifest_bytes = (release_root / "release_manifest.json").read_bytes()
    _validate_manifest_integrity(manifest_bytes)
    try:
        manifest = BoundedNegativeEvidenceReleaseManifest.model_validate_json(manifest_bytes)
    except ValidationError as error:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.MANIFEST_SCHEMA_INVALID,
            f"release manifest failed strict schema validation: {error}",
        ) from error

    reviewed_files = _verify_manifest_entries(release_root, manifest)
    summary_path = release_root / "release_summary.json"
    try:
        summary = BoundedNegativeEvidenceReleaseSummary.model_validate_json(
            summary_path.read_bytes()
        )
    except ValidationError as error:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.SUMMARY_SCHEMA_INVALID,
            f"release summary failed strict schema validation: {error}",
        ) from error

    _validate_release_state(manifest, summary)
    _validate_claim_boundaries(release_root)

    decision = BoundedNegativeEvidencePublicationReadinessDecision(
        schema_version=("specsafe_bounded_negative_evidence_publication_readiness_decision_v1"),
        decision_id="specsafe-bounded-negative-evidence-publication-readiness-v1",
        created_at="2026-07-10T20:35:14Z",
        source_commit="60755d1",
        release_id=RELEASE_ID,
        release_type="bounded_negative_evidence",
        validity_marker="CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        release_directory=RELEASE_RELATIVE_DIRECTORY,
        release_manifest=ReviewedReleaseArtifact(
            relative_path=MANIFEST_RELATIVE_PATH,
            sha256=EXPECTED_MANIFEST_SHA256,
            byte_count=EXPECTED_MANIFEST_BYTE_COUNT,
        ),
        release_files=reviewed_files,
        license_decision=PublicationLicenseDecision(
            license_identifier="cc-by-4.0",
            license_name="Creative Commons Attribution 4.0 International",
            license_selection_status="selected_for_publication_candidate",
            license_scope="sanitized_release_pack_original_materials_only",
            licensor="Kabo Molefe",
            copyright_year=2026,
            attribution_notice=(
                "SpecSafe Bounded Negative-Evidence Release v1 © 2026 Kabo Molefe, "
                "licensed under CC BY 4.0."
            ),
            license_reference_url="https://creativecommons.org/licenses/by/4.0/",
            excluded_scope=(
                "specsafe_source_code_repository",
                "retained_kaggle_archives",
                "raw_trace_or_prompt_records",
                "candidate_calibrator_artifact",
                "upstream_models_and_their_outputs",
            ),
            legal_review_status="engineering_distribution_choice_not_legal_advice",
        ),
        hugging_face_metadata_draft=HuggingFaceMetadataDraft(
            repository_type="dataset",
            repository_name="specsafe-bounded-negative-evidence-v1",
            pretty_name="SpecSafe Bounded Negative-Evidence Release v1",
            license="cc-by-4.0",
            tags=(
                "ai-reliability",
                "calibration",
                "evaluation",
                "negative-results",
                "governance",
            ),
            visibility="public",
            gated=False,
            live_inference=False,
            user_input_collection=False,
            dataset_viewer_status="not_required_no_row_level_dataset",
            card_metadata_status="prepared_not_applied",
        ),
        gate_checks=PublicationReadinessGateChecks(),
        decision_outcome="READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY",
        publication_status="review_passed_upload_not_authorized",
        publication_candidate_assembly_authorized=True,
        public_upload_authorized=False,
        required_next_controls=(
            "derive_publication_candidate_from_exact_reviewed_pack",
            "apply_reviewed_hugging_face_yaml_metadata",
            "add_cc_by_4_0_license_and_attribution_files",
            "retain_source_pack_hashes_in_publication_manifest",
            "add_rollback_and_unpublish_runbook",
            "run_final_secret_sanitization_and_claim_review",
            "require_explicit_user_authorization_before_upload",
        ),
        blocked_actions=(
            "upload_to_hugging_face_in_this_slice",
            "change_reviewed_metrics_or_claim_boundaries",
            "include_raw_archives_traces_prompts_or_model_payloads",
            "apply_cc_by_4_0_to_the_entire_specsafe_repository",
            "represent_the_candidate_as_promoted_or_production_ready",
        ),
        next_authorized_step=("assemble_exact_hugging_face_publication_candidate_without_upload"),
    )

    if write_output:
        output_path = root / DECISION_RELATIVE_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(canonical_publication_readiness_decision_json(decision))
    return decision


def canonical_publication_readiness_decision_json(
    decision: BoundedNegativeEvidencePublicationReadinessDecision,
) -> bytes:
    return (json.dumps(decision.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def check_committed_publication_readiness_decision(project_root: Path | str) -> None:
    root = _require_project_root(Path(project_root))
    expected = canonical_publication_readiness_decision_json(
        build_publication_readiness_decision(root, write_output=False)
    )
    output_path = root / DECISION_RELATIVE_PATH
    if not output_path.is_file() or output_path.read_bytes() != expected:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.COMMITTED_DECISION_MISMATCH,
            "committed publication-readiness decision is missing or not canonical",
        )


def _validate_release_directory(release_root: Path) -> None:
    if not release_root.is_dir():
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.RELEASE_DIRECTORY_INVALID,
            "reviewed release directory is missing",
        )
    entries = tuple(release_root.iterdir())
    actual_files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    if actual_files != EXPECTED_RELEASE_FILENAMES:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.RELEASE_DIRECTORY_INVALID,
            "release file allowlist does not match the reviewed pack",
        )
    if any(path.is_dir() or path.is_symlink() for path in entries):
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.RELEASE_DIRECTORY_INVALID,
            "release directory contains nested or linked content",
        )


def _validate_manifest_integrity(manifest_bytes: bytes) -> None:
    if len(manifest_bytes) != EXPECTED_MANIFEST_BYTE_COUNT:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.MANIFEST_INTEGRITY_FAILED,
            "release manifest byte count does not match the reviewed artifact",
        )
    if _sha256_bytes(manifest_bytes) != EXPECTED_MANIFEST_SHA256:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.MANIFEST_INTEGRITY_FAILED,
            "release manifest SHA-256 does not match the reviewed artifact",
        )


def _verify_manifest_entries(
    release_root: Path,
    manifest: BoundedNegativeEvidenceReleaseManifest,
) -> tuple[ReviewedReleaseArtifact, ...]:
    if tuple(item.relative_path for item in manifest.entries) != EXPECTED_ENTRY_PATHS:
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.RELEASE_FILE_INTEGRITY_FAILED,
            "release manifest entry order does not match the reviewed pack",
        )

    reviewed: list[ReviewedReleaseArtifact] = []
    for entry in manifest.entries:
        path = release_root / entry.relative_path
        payload = path.read_bytes()
        if len(payload) != entry.byte_count or _sha256_bytes(payload) != entry.sha256:
            raise PublicationReadinessError(
                PublicationReadinessErrorCode.RELEASE_FILE_INTEGRITY_FAILED,
                f"release file does not match its manifest entry: {entry.relative_path}",
            )
        reviewed.append(
            ReviewedReleaseArtifact(
                relative_path=f"{RELEASE_RELATIVE_DIRECTORY}/{entry.relative_path}",
                sha256=entry.sha256,
                byte_count=entry.byte_count,
            )
        )
    return tuple(reviewed)


def _validate_release_state(
    manifest: BoundedNegativeEvidenceReleaseManifest,
    summary: BoundedNegativeEvidenceReleaseSummary,
) -> None:
    conditions = (
        manifest.release_id == summary.release_id == RELEASE_ID,
        manifest.validity_marker == summary.validity_marker,
        manifest.publication_status == summary.publication_status == "local_pack_only",
        manifest.source_integrity_passed is True,
        manifest.canonical_build_passed is True,
        manifest.sanitization_passed is True,
        manifest.claims_boundary_passed is True,
        summary.candidate_not_promoted is True,
        summary.threshold_promotion_authorized is False,
        summary.scheduler_promotion_authorized is False,
        summary.production_claim_authorized is False,
        summary.next_authorized_step == "publication_readiness_review_and_license_decision",
        "license_selection_pending" in summary.publication_controls,
        "explicit_publication_authorization_required" in summary.publication_controls,
    )
    if not all(conditions):
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.RELEASE_STATE_INVALID,
            "release pack is not at the required publication-readiness boundary",
        )


def _validate_claim_boundaries(release_root: Path) -> None:
    readme = (release_root / "README.md").read_text(encoding="utf-8")
    boundary = (release_root / "evidence_boundary.md").read_text(encoding="utf-8")
    if readme.startswith("---\n"):
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.CLAIM_BOUNDARY_FAILED,
            "Hub YAML metadata must be applied only in the publication-candidate assembly",
        )
    if any(marker not in readme for marker in _REQUIRED_README_MARKERS):
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.CLAIM_BOUNDARY_FAILED,
            "dataset card is missing a required negative-evidence marker",
        )
    if any(marker not in boundary for marker in _REQUIRED_BOUNDARY_MARKERS):
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.CLAIM_BOUNDARY_FAILED,
            "evidence boundary is missing a required publication control",
        )


def _require_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise PublicationReadinessError(
            PublicationReadinessErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return root


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
