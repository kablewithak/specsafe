from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictPublicationCandidateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicationCandidateArtifact(StrictPublicationCandidateModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)


class PublicationCandidateEntry(PublicationCandidateArtifact):
    derivation: Literal[
        "reviewed_source_copy",
        "reviewed_source_with_hub_metadata",
        "governance_generated",
    ]


class PublicationCandidateGateChecks(StrictPublicationCandidateModel):
    readiness_decision_verified: Literal[True] = True
    reviewed_pack_verified: Literal[True] = True
    source_hashes_retained: Literal[True] = True
    hub_metadata_applied: Literal[True] = True
    license_material_present: Literal[True] = True
    attribution_present: Literal[True] = True
    rollback_runbook_present: Literal[True] = True
    final_sanitization_passed: Literal[True] = True
    claim_boundary_passed: Literal[True] = True
    public_upload_performed: Literal[False] = False


class PublicationCandidateManifest(StrictPublicationCandidateModel):
    schema_version: Literal["specsafe_hugging_face_publication_candidate_manifest_v1"]
    candidate_id: Literal["specsafe-bounded-negative-evidence-hf-candidate-v1"]
    repository_type: Literal["dataset"]
    repository_name: Literal["specsafe-bounded-negative-evidence-v1"]
    release_id: Literal["specsafe-bounded-negative-evidence-v1"]
    source_commit: Literal["38b2993"]
    validity_marker: Literal["CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"]
    license_identifier: Literal["cc-by-4.0"]
    license_scope: Literal["sanitized_release_pack_original_materials_only"]
    publication_status: Literal["local_candidate_upload_not_authorized"]
    public_upload_authorized: Literal[False]
    source_readiness_decision: PublicationCandidateArtifact
    source_release_manifest: PublicationCandidateArtifact
    reviewed_source_files: tuple[PublicationCandidateArtifact, ...] = Field(
        min_length=3,
        max_length=3,
    )
    manifest_scope: Literal["all_candidate_files_except_manifest_itself"]
    file_count: Literal[8]
    entries: tuple[PublicationCandidateEntry, ...] = Field(min_length=8, max_length=8)
    gate_checks: PublicationCandidateGateChecks
    next_authorized_step: Literal["explicit_publication_authorization_decision"]

    @model_validator(mode="after")
    def validate_manifest(self) -> PublicationCandidateManifest:
        expected_source_paths = (
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/README.md",
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/"
            "evidence_boundary.md",
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/"
            "release_summary.json",
        )
        source_paths = tuple(item.relative_path for item in self.reviewed_source_files)
        if source_paths != expected_source_paths:
            raise ValueError("reviewed source files must retain the reviewed deterministic order")

        paths = tuple(item.relative_path for item in self.entries)
        if paths != tuple(sorted(paths)):
            raise ValueError("publication candidate entries must be sorted")
        expected_entries = {
            "ATTRIBUTION.md",
            "LICENSE.md",
            "README.md",
            "ROLLBACK.md",
            "evidence_boundary.md",
            "release_summary.json",
            "sanitization_report.json",
            "source_release_manifest.json",
        }
        if set(paths) != expected_entries:
            raise ValueError("publication candidate manifest file allowlist does not match")
        if self.public_upload_authorized:
            raise ValueError("local publication candidate must not authorize upload")
        return self


class FinalSanitizationChecks(StrictPublicationCandidateModel):
    exact_file_allowlist_passed: Literal[True] = True
    no_forbidden_extensions: Literal[True] = True
    no_secret_markers: Literal[True] = True
    no_local_absolute_paths: Literal[True] = True
    no_raw_prompt_or_trace_payloads: Literal[True] = True
    no_archives_or_model_payloads: Literal[True] = True
    validity_marker_prominent: Literal[True] = True
    non_promotion_prominent: Literal[True] = True
    license_scope_bounded: Literal[True] = True
    rollback_controls_present: Literal[True] = True
    public_upload_authorization_absent: Literal[True] = True


class FinalSanitizationReport(StrictPublicationCandidateModel):
    schema_version: Literal["specsafe_hugging_face_publication_candidate_sanitization_report_v1"]
    candidate_id: Literal["specsafe-bounded-negative-evidence-hf-candidate-v1"]
    review_date: Literal["2026-07-10"]
    source_commit: Literal["38b2993"]
    validity_marker: Literal["CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"]
    publication_status: Literal["local_candidate_upload_not_authorized"]
    public_upload_authorized: Literal[False]
    scanned_file_count: Literal[9]
    scanned_files: tuple[str, ...] = Field(min_length=9, max_length=9)
    forbidden_marker_matches: Literal[0]
    checks: FinalSanitizationChecks
    final_result: Literal["PASS_LOCAL_CANDIDATE_ONLY"]
    next_authorized_step: Literal["explicit_publication_authorization_decision"]

    @model_validator(mode="after")
    def validate_scanned_files(self) -> FinalSanitizationReport:
        expected = (
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
        if self.scanned_files != expected:
            raise ValueError("sanitization report must cover the exact candidate allowlist")
        if self.public_upload_authorized:
            raise ValueError("sanitization report must not authorize upload")
        return self
