"""Offline exact-operation plan for updating the existing Hugging Face Space.

This module intentionally contains no publishing gateway and performs no remote mutations.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specsafe.hugging_face_space_prebuilt_candidate_v2.models import (
    HuggingFaceSpacePrebuiltCandidateManifestV2,
)
from specsafe.hugging_face_space_publication_candidate.models import CandidateFileDigest
from specsafe.hugging_face_space_publication_receipt import verify_local_publication_receipt
from specsafe.hugging_face_space_publication_v2.readiness import (
    EXPECTED_EVIDENCE,
    EXPECTED_FILES,
    EXPECTED_REPO_ID,
    EXPECTED_V1_REVISION,
    EXPECTED_V1_TREE,
    EXPECTED_V2_MANIFEST_SHA,
    EXPECTED_V2_SOURCE_SHA,
    EXPECTED_V2_TREE,
    V2_MANIFEST_PATH,
    build_local_v2_release_readiness,
)

V1_STATIC_ASSETS = (
    "assets/index-ComhRJPm.css",
    "assets/index-DBdnOm5m.js",
)
V2_STATIC_ASSETS = (
    "assets/index-BeNBJrmc.css",
    "assets/index-CAsY5KRm.js",
)
V1_FILES = (
    "README.md",
    *V1_STATIC_ASSETS,
    "evidence/evidence_index.json",
    "index.html",
)
EXPECTED_V2_DELETIONS = V1_STATIC_ASSETS
EXPECTED_ROLLBACK_DELETIONS = V2_STATIC_ASSETS


class V2UpdatePlanErrorCode(StrEnum):
    INVALID_REPOSITORY = "v2_update_plan_invalid_repository"
    INVALID_CANDIDATE = "v2_update_plan_invalid_candidate"
    INVALID_ROLLBACK = "v2_update_plan_invalid_rollback"
    INVALID_OPERATIONS = "v2_update_plan_invalid_operations"


class V2UpdatePlanError(RuntimeError):
    def __init__(self, code: V2UpdatePlanErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class StrictUpdateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExistingSpaceV2UpdatePlan(StrictUpdateModel):
    """Immutable dry-run plan; does not confer permission to execute it."""

    schema_version: Literal["specsafe_existing_space_v2_update_plan_v1"]
    repository_id: Literal["KaboKableMolefe/specsafe-reliability-lab"]
    repository_type: Literal["space"]
    target_branch: Literal["main"]
    existing_repository_policy: Literal["require_exact_existing_public_v1"]
    expected_parent_commit: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    rollback_anchor_revision: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    rollback_candidate_tree_sha256: Literal[
        "4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362"
    ]
    v2_candidate_manifest_sha256: Literal[
        "73924515752cf10d8b05cde9f2e89313a3c1337ea2eb305a0166c453b9caf853"
    ]
    v2_source_manifest_sha256: Literal[
        "057b8f59dbcaa76ef9c51c2a72a26adb059510717b7af87966096dd0a1a510d0"
    ]
    v2_candidate_tree_sha256: Literal[
        "20a9847f98d9b0d353a37a2f035c61524c20c3a92b0298ec2076e9d9278773d0"
    ]
    evidence_index_sha256: Literal[
        "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
    ]
    upload_files: tuple[CandidateFileDigest, ...] = Field(min_length=5, max_length=5)
    delete_files: tuple[str, ...] = Field(min_length=2, max_length=2)
    rollback_upload_files: tuple[CandidateFileDigest, ...] = Field(min_length=5, max_length=5)
    rollback_delete_files: tuple[str, ...] = Field(min_length=2, max_length=2)
    commit_concurrency_policy: Literal["huggingface_create_commit_parent_commit_cas"]
    publication_authorized: Literal[False] = False
    remote_mutation: Literal[False] = False
    rollback_executed: Literal[False] = False
    next_step: Literal["qualify_revision_guarded_update_executor"]

    @model_validator(mode="after")
    def verify_exact_operations(self) -> ExistingSpaceV2UpdatePlan:
        if tuple(item.relative_path for item in self.upload_files) != EXPECTED_FILES:
            raise ValueError("V2 uploads must match exactly the five frozen V2 filenames")
        if tuple(item.relative_path for item in self.rollback_upload_files) != V1_FILES:
            raise ValueError("V1 rollback uploads must match exactly the retained files")
        if self.delete_files != EXPECTED_V2_DELETIONS:
            raise ValueError("V2 deletions may remove only superseded V1 hashed assets")
        if self.rollback_delete_files != EXPECTED_ROLLBACK_DELETIONS:
            raise ValueError("rollback deletions may remove only V2 hashed assets")
        if set(self.delete_files) & {item.relative_path for item in self.upload_files}:
            raise ValueError("V2 upload and delete paths may not overlap")
        if set(self.rollback_delete_files) & {
            item.relative_path for item in self.rollback_upload_files
        }:
            raise ValueError("V1 rollback upload and delete paths may not overlap")
        return self


def build_existing_space_v2_update_plan(project_root: Path | str) -> ExistingSpaceV2UpdatePlan:
    """Qualify exact local assets and V1 recovery; never query or mutate HF."""

    root = Path(project_root).expanduser().resolve()
    readiness = build_local_v2_release_readiness(root)
    v1 = verify_local_publication_receipt(root).receipt

    manifest_path = root / V2_MANIFEST_PATH
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != EXPECTED_V2_MANIFEST_SHA:
        raise V2UpdatePlanError(
            V2UpdatePlanErrorCode.INVALID_CANDIDATE,
            "V2 prebuilt manifest drifted from the frozen release",
        )
    manifest = HuggingFaceSpacePrebuiltCandidateManifestV2.model_validate_json(manifest_bytes)

    if readiness.target_repository_id != EXPECTED_REPO_ID or v1.repository_id != EXPECTED_REPO_ID:
        raise V2UpdatePlanError(
            V2UpdatePlanErrorCode.INVALID_REPOSITORY,
            "existing Space repository does not match the pinned owner and name",
        )
    if (
        v1.published_revision != EXPECTED_V1_REVISION
        or v1.candidate_tree_sha256 != EXPECTED_V1_TREE
        or v1.evidence_index_sha256 != EXPECTED_EVIDENCE
        or tuple(v1.remote_files) != V1_FILES
    ):
        raise V2UpdatePlanError(
            V2UpdatePlanErrorCode.INVALID_ROLLBACK,
            "retained V1 rollback provenance is not the frozen publication",
        )
    if (
        manifest.candidate_tree_sha256 != EXPECTED_V2_TREE
        or manifest.source_candidate_manifest_sha256 != EXPECTED_V2_SOURCE_SHA
        or manifest.evidence_index_sha256 != EXPECTED_EVIDENCE
        or tuple(item.relative_path for item in manifest.files) != EXPECTED_FILES
    ):
        raise V2UpdatePlanError(
            V2UpdatePlanErrorCode.INVALID_CANDIDATE,
            "V2 update assets are outside the exact preserved candidate",
        )

    # The only deletions are the two V1 fingerprinted assets no longer referenced
    # by the frozen V2 HTML. All other paths are overwritten with V2 bytes.
    prior_paths = set(v1.remote_files)
    next_paths = {item.relative_path for item in manifest.files}
    if (
        tuple(sorted(prior_paths - next_paths)) != EXPECTED_V2_DELETIONS
        or tuple(sorted(next_paths - prior_paths)) != EXPECTED_ROLLBACK_DELETIONS
    ):
        raise V2UpdatePlanError(
            V2UpdatePlanErrorCode.INVALID_OPERATIONS,
            "asset delta is outside the exact V1-to-V2 update boundary",
        )

    return ExistingSpaceV2UpdatePlan(
        schema_version="specsafe_existing_space_v2_update_plan_v1",
        repository_id=EXPECTED_REPO_ID,
        repository_type="space",
        target_branch="main",
        existing_repository_policy="require_exact_existing_public_v1",
        expected_parent_commit=EXPECTED_V1_REVISION,
        rollback_anchor_revision=EXPECTED_V1_REVISION,
        rollback_candidate_tree_sha256=EXPECTED_V1_TREE,
        v2_candidate_manifest_sha256=EXPECTED_V2_MANIFEST_SHA,
        v2_source_manifest_sha256=EXPECTED_V2_SOURCE_SHA,
        v2_candidate_tree_sha256=EXPECTED_V2_TREE,
        evidence_index_sha256=EXPECTED_EVIDENCE,
        upload_files=manifest.files,
        delete_files=EXPECTED_V2_DELETIONS,
        rollback_upload_files=v1.published_file_hashes,
        rollback_delete_files=EXPECTED_ROLLBACK_DELETIONS,
        commit_concurrency_policy="huggingface_create_commit_parent_commit_cas",
        next_step="qualify_revision_guarded_update_executor",
    )


def canonical_update_plan_json(plan: ExistingSpaceV2UpdatePlan) -> bytes:
    """Stable audit preview; contains no token, mutable state, or upload action."""
    return (json.dumps(plan.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
