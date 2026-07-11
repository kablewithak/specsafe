from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specsafe.hugging_face_space_publication_candidate import CandidateFileDigest


class StrictReceiptReconciliationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpacePublicationReconciliationRecord(StrictReceiptReconciliationModel):
    schema_version: Literal["specsafe_hugging_face_space_publication_reconciliation_v1"]
    publication_id: Literal["specsafe-reliability-lab-hf-space-prebuilt-publication-v1"]
    receipt_relative_path: Literal[
        "evidence/publication-receipts/specsafe-reliability-lab/"
        "hugging_face_space_publication_receipt.json"
    ]
    receipt_byte_count: int = Field(gt=0)
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_id: Literal["KaboKableMolefe/specsafe-reliability-lab"]
    repository_url: Literal[
        "https://huggingface.co/spaces/KaboKableMolefe/specsafe-reliability-lab"
    ]
    application_url: Literal["https://kabokablemolefe-specsafe-reliability-lab.static.hf.space"]
    published_revision: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    published_from_git_sha: Literal["e456a7f1b8b8a1e3dddbbfc3a0f54ed3049f8b52"]
    candidate_manifest_sha256: Literal[
        "d377f18aa189cec1529b6385483059acecb675bdfc74eda767fc005e631f07e3"
    ]
    candidate_tree_sha256: Literal[
        "4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362"
    ]
    source_candidate_manifest_sha256: Literal[
        "63a28d28416f67b55f62019ff6c5905c923de791564f8de8fa6859a676356b8d"
    ]
    source_candidate_tree_sha256: Literal[
        "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
    ]
    evidence_index_sha256: Literal[
        "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
    ]
    remote_file_count: Literal[5]
    remote_files: tuple[str, ...] = Field(min_length=5, max_length=5)
    remote_file_hashes: tuple[CandidateFileDigest, ...] = Field(
        min_length=5,
        max_length=5,
    )
    remote_visibility: Literal["public"]
    remote_sdk: Literal["static"]
    remote_runtime_stage: str = Field(min_length=1)
    anonymous_repository_verified: Literal[True]
    anonymous_file_hashes_verified: Literal[True]
    anonymous_application_verified: Literal[True]
    served_html_verified: Literal[True]
    remote_public_and_ungated: Literal[True]
    remote_revision_matches_receipt: Literal[True]
    terminal_error_absent: Literal[True]
    credential_used: Literal[False]
    verified_at: datetime

    @model_validator(mode="after")
    def validate_files(self) -> SpacePublicationReconciliationRecord:
        paths = tuple(item.relative_path for item in self.remote_file_hashes)
        if paths != self.remote_files:
            raise ValueError("reconciliation file hashes must match the exact remote file order")
        if self.remote_files != tuple(sorted(self.remote_files)):
            raise ValueError("reconciliation remote files must retain sorted order")
        if len(set(self.remote_files)) != len(self.remote_files):
            raise ValueError("reconciliation remote files must not contain duplicates")
        return self
