from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LocalV2ReleaseReadiness(StrictReadinessModel):
    schema_version: Literal["specsafe_space_v2_local_release_readiness_v1"]
    target_repository_id: Literal["KaboKableMolefe/specsafe-reliability-lab"]
    target_repository_url: Literal[
        "https://huggingface.co/spaces/KaboKableMolefe/specsafe-reliability-lab"
    ]
    v2_prebuilt_manifest_sha256: Literal[
        "73924515752cf10d8b05cde9f2e89313a3c1337ea2eb305a0166c453b9caf853"
    ]
    v2_prebuilt_tree_sha256: Literal[
        "20a9847f98d9b0d353a37a2f035c61524c20c3a92b0298ec2076e9d9278773d0"
    ]
    v2_source_manifest_sha256: Literal[
        "057b8f59dbcaa76ef9c51c2a72a26adb059510717b7af87966096dd0a1a510d0"
    ]
    v2_source_tree_sha256: Literal[
        "462988e7a1b30bdcdf66e87a25933356f67a0a83b86beaadc5fe810f4734d7bc"
    ]
    v2_prebuilt_file_count: Literal[5]
    evidence_index_sha256: Literal[
        "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
    ]
    retained_v1_published_revision: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    retained_v1_candidate_tree_sha256: Literal[
        "4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362"
    ]
    local_v2_candidate_verified: Literal[True]
    local_v1_receipt_verified: Literal[True]
    local_v1_reconciliation_verified: Literal[True]
    current_remote_head_observed: Literal[False] = False
    publication_authorized: Literal[False] = False
    remote_mutation: Literal[False] = False
    next_step: Literal["read_only_remote_preflight_existing_space"]


class RemoteV2PreflightReport(StrictReadinessModel):
    schema_version: Literal["specsafe_space_v2_remote_preflight_report_v1"]
    target_repository_id: Literal["KaboKableMolefe/specsafe-reliability-lab"]
    observed_current_revision: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    retained_v1_rollback_revision: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    v2_prebuilt_tree_sha256: Literal[
        "20a9847f98d9b0d353a37a2f035c61524c20c3a92b0298ec2076e9d9278773d0"
    ]
    existing_v1_remote_files_verified: Literal[True]
    current_remote_revision_verified: Literal[True]
    public_application_verified: Literal[True]
    publication_authorized: Literal[False] = False
    remote_mutation: Literal[False] = False
    next_step: Literal["design_and_approve_revision_guarded_v2_update"]
