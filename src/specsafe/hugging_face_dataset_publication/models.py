from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictPublicationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FileDigest(StrictPublicationModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)


class PublicationPlan(StrictPublicationModel):
    schema_version: Literal["specsafe_hugging_face_dataset_publication_plan_v1"]
    authorization_decision_sha256: Literal[
        "bf96e015379f8ad955791c28b8ba75b123b3d748d2192943190b056eb5aadc46"
    ]
    authorization_decision_byte_count: Literal[4528]
    candidate_id: Literal["specsafe-bounded-negative-evidence-hf-candidate-v1"]
    release_id: Literal["specsafe-bounded-negative-evidence-v1"]
    repository_name: Literal["specsafe-bounded-negative-evidence-v1"]
    repository_type: Literal["dataset"]
    final_visibility: Literal["public"]
    gated: Literal[False]
    publication_manifest_sha256: Literal[
        "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
    ]
    files: tuple[FileDigest, ...] = Field(min_length=9, max_length=9)
    upload_mode: Literal["private_stage_exact_commit_public_release"]
    remote_existing_repository_policy: Literal["reject"]
    credential_policy: Literal["locally_managed_credential_never_logged"]
    receipt_relative_path: Literal[
        "evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/"
        "hugging_face_dataset_publication_receipt.json"
    ]

    @model_validator(mode="after")
    def validate_files(self) -> PublicationPlan:
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
        if tuple(item.relative_path for item in self.files) != expected:
            raise ValueError("publication plan must retain the exact authorized file order")
        return self


class PublicationReceipt(StrictPublicationModel):
    schema_version: Literal["specsafe_hugging_face_dataset_publication_receipt_v1"]
    publication_id: Literal["specsafe-bounded-negative-evidence-hf-publication-v1"]
    repository_id: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*/specsafe-bounded-negative-evidence-v1$"
    )
    repository_url: str = Field(pattern=r"^https://huggingface\.co/datasets/")
    namespace: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    repository_name: Literal["specsafe-bounded-negative-evidence-v1"]
    repository_type: Literal["dataset"]
    final_visibility: Literal["public"]
    gated: Literal[False]
    published_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    publication_manifest_sha256: Literal[
        "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
    ]
    published_file_hashes: tuple[FileDigest, ...] = Field(min_length=9, max_length=9)
    remote_files: tuple[str, ...] = Field(min_length=9, max_length=9)
    remote_file_count: Literal[9]
    authenticated_namespace_verified: Literal[True]
    private_stage_verified: Literal[True]
    anonymous_public_verification_passed: Literal[True]
    negative_evidence_marker_verified: Literal[True]
    candidate_non_promotion_verified: Literal[True]
    license_metadata_verified: Literal[True]
    rollback_triggered: Literal[False]
    published_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> PublicationReceipt:
        paths = tuple(item.relative_path for item in self.published_file_hashes)
        if paths != self.remote_files:
            raise ValueError("receipt file hashes must match the exact remote file list")
        if self.repository_id != f"{self.namespace}/{self.repository_name}":
            raise ValueError("receipt repository identity does not match namespace and name")
        return self
