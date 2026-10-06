from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specsafe.hugging_face_space_publication_candidate import CandidateFileDigest

REDESIGN_SOURCE_COMMIT = "19fac2747a4cd6b764f61a9d6f54fd2bfb5c71c9"


class StrictV2CandidateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpaceMetadataV2(StrictV2CandidateModel):
    title: Literal["SpecSafe - When Should AI Spend More Compute?"]
    emoji: Literal["🛡️"]
    color_from: Literal["yellow"]
    color_to: Literal["red"]
    sdk: Literal["static"]
    app_build_command: Literal["npm run build"]
    app_file: Literal["dist/index.html"]
    full_width: Literal[True]
    header: Literal["mini"]
    short_description: Literal["AI reliability case study on adaptive verification."]
    datasets: tuple[Literal["KaboKableMolefe/specsafe-bounded-negative-evidence-v1"], ...]
    tags: tuple[str, ...]
    pinned: Literal[False]


class HuggingFaceSpacePublicationCandidateManifestV2(StrictV2CandidateModel):
    schema_version: Literal["specsafe_hugging_face_space_publication_candidate_manifest_v2"]
    lineage_version: Literal["v2"]
    space_repository_name: Literal["specsafe-reliability-lab"]
    source_app_relative_path: Literal["apps/specsafe-reliability-lab"]
    source_commit: Literal["19fac2747a4cd6b764f61a9d6f54fd2bfb5c71c9"]
    candidate_root_relative_path: Literal[
        "release/hugging-face-space-publication-v2/specsafe-reliability-lab/candidate/space"
    ]
    metadata: SpaceMetadataV2
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
    next_authorized_step: Literal["build_and_qualify_prebuilt_candidate_v2"]

    @model_validator(mode="after")
    def validate_files(self) -> HuggingFaceSpacePublicationCandidateManifestV2:
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)):
            raise ValueError("v2 candidate files must retain sorted path order")
        if len(set(paths)) != len(paths):
            raise ValueError("v2 candidate files must not contain duplicate paths")
        if len(paths) != self.exact_candidate_file_count:
            raise ValueError("v2 candidate file count does not match file digests")
        if self.evidence_index_relative_path not in paths:
            raise ValueError("v2 candidate must contain the frozen evidence index")
        return self
