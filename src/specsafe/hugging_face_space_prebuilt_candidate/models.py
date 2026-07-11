from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specsafe.hugging_face_space_publication_candidate import CandidateFileDigest


class StrictPrebuiltCandidateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PrebuiltSpaceMetadata(StrictPrebuiltCandidateModel):
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


class HuggingFaceSpacePrebuiltCandidateManifest(StrictPrebuiltCandidateModel):
    schema_version: Literal["specsafe_hugging_face_space_prebuilt_candidate_manifest_v1"]
    space_repository_name: Literal["specsafe-reliability-lab"]
    source_candidate_manifest_relative_path: Literal[
        "release/hugging-face-space-publication/specsafe-reliability-lab/"
        "publication_candidate_manifest.json"
    ]
    source_candidate_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_candidate_tree_sha256: Literal[
        "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
    ]
    source_candidate_file_count: Literal[35]
    candidate_root_relative_path: Literal[
        "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/candidate/space"
    ]
    metadata: PrebuiltSpaceMetadata
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
    next_authorized_step: Literal["rebind_controlled_publication_executor_to_prebuilt_candidate"]

    @model_validator(mode="after")
    def validate_files(self) -> HuggingFaceSpacePrebuiltCandidateManifest:
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)):
            raise ValueError("prebuilt candidate files must retain sorted path order")
        if len(set(paths)) != len(paths):
            raise ValueError("prebuilt candidate files must not contain duplicate paths")
        if len(paths) != self.exact_candidate_file_count:
            raise ValueError("prebuilt candidate file count does not match file digests")
        if "README.md" not in paths or "index.html" not in paths:
            raise ValueError("prebuilt candidate must contain README.md and index.html")
        if self.evidence_index_relative_path not in paths:
            raise ValueError("prebuilt candidate must contain the frozen evidence index")
        return self
