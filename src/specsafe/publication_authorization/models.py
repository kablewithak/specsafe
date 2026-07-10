from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictAuthorizationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthorizedArtifact(StrictAuthorizationModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)


class PublicationTarget(StrictAuthorizationModel):
    repository_type: Literal["dataset"]
    repository_name: Literal["specsafe-bounded-negative-evidence-v1"]
    visibility: Literal["public"]
    gated: Literal[False]
    default_branch: Literal["main"]
    namespace_policy: Literal["authenticated_owner_or_explicit_organization"]
    credential_policy: Literal["managed_credential_never_logged_or_committed"]
    license_identifier: Literal["cc-by-4.0"]
    exact_candidate_file_count: Literal[9]
    exact_candidate_files: tuple[str, ...] = Field(min_length=9, max_length=9)

    @model_validator(mode="after")
    def validate_files(self) -> PublicationTarget:
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
        if self.exact_candidate_files != expected:
            raise ValueError("publication target must retain the exact candidate file order")
        return self


class PublicationAuthorizationGateChecks(StrictAuthorizationModel):
    candidate_manifest_hash_verified: Literal[True] = True
    candidate_manifest_schema_valid: Literal[True] = True
    candidate_entries_verified: Literal[True] = True
    candidate_file_allowlist_passed: Literal[True] = True
    final_sanitization_schema_valid: Literal[True] = True
    final_sanitization_passed: Literal[True] = True
    negative_evidence_boundary_retained: Literal[True] = True
    license_scope_bounded: Literal[True] = True
    rollback_controls_present: Literal[True] = True
    no_credentials_present: Literal[True] = True
    remote_repository_created: Literal[False] = False
    public_upload_performed: Literal[False] = False


class ExactPublicationAuthorizationDecision(StrictAuthorizationModel):
    schema_version: Literal["specsafe_exact_hugging_face_publication_authorization_v1"]
    decision_id: Literal["specsafe-bounded-negative-evidence-publication-authorization-v1"]
    decision_date: Literal["2026-07-10"]
    source_commit: Literal["489ebb5"]
    candidate_id: Literal["specsafe-bounded-negative-evidence-hf-candidate-v1"]
    release_id: Literal["specsafe-bounded-negative-evidence-v1"]
    validity_marker: Literal["CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"]
    authorization_scope: Literal["exact_candidate_bytes_only"]
    publication_manifest: AuthorizedArtifact
    sanitization_report: AuthorizedArtifact
    authorized_files: tuple[AuthorizedArtifact, ...] = Field(min_length=9, max_length=9)
    target: PublicationTarget
    gate_checks: PublicationAuthorizationGateChecks
    decision_outcome: Literal["AUTHORIZE_EXACT_PUBLICATION"]
    publication_authorized: Literal[True]
    publication_performed: Literal[False]
    authorization_revoked_by_candidate_drift: Literal[True]
    required_receipt_fields: tuple[str, ...] = Field(min_length=6)
    blocked_actions: tuple[str, ...] = Field(min_length=5)
    next_authorized_step: Literal["controlled_hugging_face_dataset_publication_and_receipt"]

    @model_validator(mode="after")
    def validate_decision(self) -> ExactPublicationAuthorizationDecision:
        paths = tuple(item.relative_path for item in self.authorized_files)
        if paths != self.target.exact_candidate_files:
            raise ValueError("authorized files must match the exact publication target")
        if self.publication_manifest.relative_path != (
            "release/hugging-face/specsafe-bounded-negative-evidence-v1/publication_manifest.json"
        ):
            raise ValueError("authorization must bind the reviewed publication manifest")
        if self.publication_manifest.sha256 != (
            "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
        ):
            raise ValueError("authorization must bind the exact candidate manifest hash")
        if self.publication_performed:
            raise ValueError("authorization decision must not perform publication")
        return self
