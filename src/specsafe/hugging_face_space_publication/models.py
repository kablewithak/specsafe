from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specsafe.hugging_face_space_publication_candidate import CandidateFileDigest


class StrictSpacePublicationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpacePublicationPlan(StrictSpacePublicationModel):
    schema_version: Literal["specsafe_hugging_face_space_publication_plan_v1"]
    candidate_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_tree_sha256: Literal[
        "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
    ]
    evidence_index_sha256: Literal[
        "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
    ]
    candidate_file_count: Literal[35]
    repository_name: Literal["specsafe-reliability-lab"]
    repository_type: Literal["space"]
    sdk: Literal["static"]
    final_visibility: Literal["public"]
    files: tuple[CandidateFileDigest, ...] = Field(min_length=35, max_length=35)
    upload_mode: Literal["private_stage_exact_commit_public_release"]
    remote_existing_repository_policy: Literal["reject"]
    credential_policy: Literal["environment_token_never_logged_or_persisted"]
    receipt_relative_path: Literal[
        "evidence/publication-receipts/specsafe-reliability-lab/"
        "hugging_face_space_publication_receipt.json"
    ]

    @model_validator(mode="after")
    def validate_files(self) -> SpacePublicationPlan:
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)):
            raise ValueError("publication plan files must retain sorted candidate order")
        if len(set(paths)) != len(paths):
            raise ValueError("publication plan files must not contain duplicate paths")
        return self


class SpacePublicationReceipt(StrictSpacePublicationModel):
    schema_version: Literal["specsafe_hugging_face_space_publication_receipt_v1"]
    publication_id: Literal["specsafe-reliability-lab-hf-space-publication-v1"]
    repository_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*/specsafe-reliability-lab$")
    repository_url: str = Field(pattern=r"^https://huggingface\.co/spaces/")
    application_url: str = Field(pattern=r"^https://[A-Za-z0-9.-]+\.hf\.space/?$")
    namespace: Literal["KaboKableMolefe"]
    repository_name: Literal["specsafe-reliability-lab"]
    repository_type: Literal["space"]
    sdk: Literal["static"]
    final_visibility: Literal["public"]
    published_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    published_from_git_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    candidate_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_tree_sha256: Literal[
        "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
    ]
    evidence_index_sha256: Literal[
        "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
    ]
    published_file_hashes: tuple[CandidateFileDigest, ...] = Field(
        min_length=35,
        max_length=35,
    )
    remote_files: tuple[str, ...] = Field(min_length=35, max_length=35)
    remote_file_count: Literal[35]
    authenticated_namespace_verified: Literal[True]
    private_stage_verified: Literal[True]
    anonymous_repository_verification_passed: Literal[True]
    anonymous_application_verification_passed: Literal[True]
    served_html_verified: Literal[True]
    static_build_ready: Literal[True]
    rollback_triggered: Literal[False]
    published_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> SpacePublicationReceipt:
        paths = tuple(item.relative_path for item in self.published_file_hashes)
        if paths != self.remote_files:
            raise ValueError("receipt file hashes must match the exact remote file order")
        if self.repository_id != f"{self.namespace}/{self.repository_name}":
            raise ValueError("receipt repository identity does not match namespace and name")
        return self
