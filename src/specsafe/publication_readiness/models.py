from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictPublicationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewedReleaseArtifact(StrictPublicationModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)


class PublicationLicenseDecision(StrictPublicationModel):
    license_identifier: Literal["cc-by-4.0"]
    license_name: Literal["Creative Commons Attribution 4.0 International"]
    license_selection_status: Literal["selected_for_publication_candidate"]
    license_scope: Literal["sanitized_release_pack_original_materials_only"]
    licensor: Literal["Kabo Molefe"]
    copyright_year: Literal[2026]
    attribution_notice: Literal[
        "SpecSafe Bounded Negative-Evidence Release v1 © 2026 Kabo Molefe, "
        "licensed under CC BY 4.0."
    ]
    license_reference_url: Literal["https://creativecommons.org/licenses/by/4.0/"]
    excluded_scope: tuple[str, ...] = Field(min_length=5)
    legal_review_status: Literal["engineering_distribution_choice_not_legal_advice"]

    @model_validator(mode="after")
    def validate_scope(self) -> PublicationLicenseDecision:
        expected = {
            "specsafe_source_code_repository",
            "retained_kaggle_archives",
            "raw_trace_or_prompt_records",
            "candidate_calibrator_artifact",
            "upstream_models_and_their_outputs",
        }
        if set(self.excluded_scope) != expected:
            raise ValueError("license scope exclusions must match the bounded release decision")
        return self


class HuggingFaceMetadataDraft(StrictPublicationModel):
    repository_type: Literal["dataset"]
    repository_name: Literal["specsafe-bounded-negative-evidence-v1"]
    pretty_name: Literal["SpecSafe Bounded Negative-Evidence Release v1"]
    license: Literal["cc-by-4.0"]
    tags: tuple[str, ...] = Field(min_length=5, max_length=5)
    visibility: Literal["public"]
    gated: Literal[False]
    live_inference: Literal[False]
    user_input_collection: Literal[False]
    dataset_viewer_status: Literal["not_required_no_row_level_dataset"]
    card_metadata_status: Literal["prepared_not_applied"]

    @model_validator(mode="after")
    def validate_tags(self) -> HuggingFaceMetadataDraft:
        expected = (
            "ai-reliability",
            "calibration",
            "evaluation",
            "negative-results",
            "governance",
        )
        if self.tags != expected:
            raise ValueError("Hugging Face tags must match the reviewed deterministic order")
        return self


class PublicationReadinessGateChecks(StrictPublicationModel):
    release_manifest_hash_verified: Literal[True] = True
    release_manifest_schema_valid: Literal[True] = True
    release_entries_verified: Literal[True] = True
    release_summary_schema_valid: Literal[True] = True
    release_identity_alignment_passed: Literal[True] = True
    exact_file_allowlist_passed: Literal[True] = True
    sanitization_retained: Literal[True] = True
    claims_boundary_retained: Literal[True] = True
    validity_marker_prominent: Literal[True] = True
    non_promotion_prominent: Literal[True] = True
    license_selected: Literal[True] = True
    license_scope_bounded: Literal[True] = True
    hub_metadata_draft_prepared: Literal[True] = True
    rollback_plan_required: Literal[True] = True
    public_upload_performed: Literal[False] = False


class BoundedNegativeEvidencePublicationReadinessDecision(StrictPublicationModel):
    schema_version: Literal["specsafe_bounded_negative_evidence_publication_readiness_decision_v1"]
    decision_id: Literal["specsafe-bounded-negative-evidence-publication-readiness-v1"]
    created_at: Literal["2026-07-10T20:35:14Z"]
    source_commit: Literal["60755d1"]
    release_id: Literal["specsafe-bounded-negative-evidence-v1"]
    release_type: Literal["bounded_negative_evidence"]
    validity_marker: Literal["CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"]
    release_directory: Literal[
        "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1"
    ]
    release_manifest: ReviewedReleaseArtifact
    release_files: tuple[ReviewedReleaseArtifact, ...] = Field(min_length=3, max_length=3)
    license_decision: PublicationLicenseDecision
    hugging_face_metadata_draft: HuggingFaceMetadataDraft
    gate_checks: PublicationReadinessGateChecks
    decision_outcome: Literal["READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY"]
    publication_status: Literal["review_passed_upload_not_authorized"]
    publication_candidate_assembly_authorized: Literal[True]
    public_upload_authorized: Literal[False]
    required_next_controls: tuple[str, ...] = Field(min_length=6)
    blocked_actions: tuple[str, ...] = Field(min_length=4)
    next_authorized_step: Literal[
        "assemble_exact_hugging_face_publication_candidate_without_upload"
    ]

    @model_validator(mode="after")
    def validate_decision(self) -> BoundedNegativeEvidencePublicationReadinessDecision:
        expected_paths = (
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/README.md",
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/"
            "evidence_boundary.md",
            "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/"
            "release_summary.json",
        )
        paths = tuple(item.relative_path for item in self.release_files)
        if paths != expected_paths:
            raise ValueError("reviewed release files must match the deterministic order")
        if self.license_decision.license_identifier != self.hugging_face_metadata_draft.license:
            raise ValueError("license decision and Hub metadata draft must agree")
        if self.public_upload_authorized:
            raise ValueError("publication readiness review must not authorize upload")
        return self
