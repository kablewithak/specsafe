from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specsafe.hugging_face_space_publication_candidate import CandidateFileDigest


class StrictPrebuiltCandidateV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PrebuiltSpaceMetadataV2(StrictPrebuiltCandidateV2Model):
    title: Literal["SpecSafe - When Should AI Spend More Compute?"]
    emoji: Literal["🛡️"]
    color_from: Literal["yellow"]
    color_to: Literal["red"]
    sdk: Literal["static"]
    app_file: Literal["index.html"]
    full_width: Literal[True]
    header: Literal["mini"]
    short_description: Literal["AI reliability case study on adaptive verification."]
    datasets: tuple[Literal["KaboKableMolefe/specsafe-bounded-negative-evidence-v1"], ...]
    tags: tuple[str, ...]
    pinned: Literal[False]


class HuggingFaceSpacePrebuiltCandidateManifestV2(StrictPrebuiltCandidateV2Model):
    schema_version: Literal["specsafe_hugging_face_space_prebuilt_candidate_manifest_v2"]
    lineage_version: Literal["v2"]
    space_repository_name: Literal["specsafe-reliability-lab"]
    source_candidate_manifest_relative_path: Literal[
        "release/hugging-face-space-publication-v2/specsafe-reliability-lab/"
        "publication_candidate_manifest_v2.json"
    ]
    source_candidate_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_candidate_tree_sha256: Literal[
        "462988e7a1b30bdcdf66e87a25933356f67a0a83b86beaadc5fe810f4734d7bc"
    ]
    source_candidate_file_count: Literal[58]
    source_commit: Literal["19fac2747a4cd6b764f61a9d6f54fd2bfb5c71c9"]
    candidate_root_relative_path: Literal[
        "release/hugging-face-space-prebuilt-publication-v2/"
        "specsafe-reliability-lab/candidate/space"
    ]
    metadata: PrebuiltSpaceMetadataV2
    evidence_index_relative_path: Literal["evidence/evidence_index.json"]
    evidence_index_byte_count: int = Field(gt=0)
    evidence_index_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    build_strategy: Literal["local_validated_prebuilt_static_assets"]
    build_commands: tuple[str, ...]
    exact_candidate_file_count: int = Field(gt=2)
    candidate_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    files: tuple[CandidateFileDigest, ...]
    actual_space_publication: Literal[False]
    remote_mutation: Literal[False]
    provider_side_build_required: Literal[False]
    live_inference: Literal[False]
    user_input_collection: Literal[False]
    next_authorized_step: Literal["rebind_controlled_publication_executor_to_prebuilt_candidate_v2"]

    @model_validator(mode="after")
    def validate_files(self) -> HuggingFaceSpacePrebuiltCandidateManifestV2:
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)):
            raise ValueError("v2 prebuilt candidate files must retain sorted path order")
        if len(set(paths)) != len(paths):
            raise ValueError("v2 prebuilt candidate files must not contain duplicate paths")
        if len(paths) != self.exact_candidate_file_count:
            raise ValueError("v2 prebuilt candidate file count does not match file digests")
        if "README.md" not in paths or "index.html" not in paths:
            raise ValueError("v2 prebuilt candidate must contain README.md and index.html")
        if self.evidence_index_relative_path not in paths:
            raise ValueError("v2 prebuilt candidate must contain the frozen evidence index")
        return self
