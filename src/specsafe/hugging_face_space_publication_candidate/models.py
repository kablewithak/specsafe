from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CandidateFileDigest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    relative_path: str = Field(min_length=1)
    byte_count: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SpaceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    emoji: str
    color_from: Literal["yellow"]
    color_to: Literal["red"]
    sdk: Literal["static"]
    app_build_command: Literal["npm run build"]
    app_file: Literal["dist/index.html"]
    full_width: Literal[True]
    header: Literal["mini"]
    short_description: str
    datasets: tuple[str, ...]
    tags: tuple[str, ...]
    pinned: Literal[False]


class HuggingFaceSpacePublicationCandidateManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[
        "specsafe_hugging_face_space_publication_candidate_manifest_v1"
    ]
    space_repository_name: Literal["specsafe-reliability-lab"]
    source_app_relative_path: Literal["apps/specsafe-reliability-lab"]
    candidate_root_relative_path: Literal[
        "release/hugging-face-space-publication/specsafe-reliability-lab/"
        "candidate/space"
    ]
    source_commit: Literal["2848e80"]
    metadata: SpaceMetadata
    evidence_index_relative_path: Literal["public/evidence/evidence_index.json"]
    evidence_index_byte_count: int = Field(gt=0)
    evidence_index_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    exact_candidate_file_count: int = Field(gt=0)
    candidate_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    files: tuple[CandidateFileDigest, ...]
    actual_space_publication: Literal[False]
    remote_mutation: Literal[False]
    live_inference: Literal[False]
    user_input_collection: Literal[False]
    next_authorized_step: Literal["controlled_remote_space_creation_and_upload"]
