from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.hugging_face_space_publication_v2.readiness import EXPECTED_FILES
from specsafe.hugging_face_space_publication_v2.update_plan import (
    EXPECTED_ROLLBACK_DELETIONS,
    EXPECTED_V2_DELETIONS,
    V1_FILES,
    V1_STATIC_ASSETS,
    V2_STATIC_ASSETS,
    ExistingSpaceV2UpdatePlan,
    build_existing_space_v2_update_plan,
    canonical_update_plan_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_update_plan_is_exact_and_not_authorization() -> None:
    plan = build_existing_space_v2_update_plan(PROJECT_ROOT)
    assert plan.repository_id == "KaboKableMolefe/specsafe-reliability-lab"
    assert plan.expected_parent_commit == plan.rollback_anchor_revision
    assert tuple(item.relative_path for item in plan.upload_files) == EXPECTED_FILES
    assert plan.delete_files == V1_STATIC_ASSETS
    assert tuple(item.relative_path for item in plan.rollback_upload_files) == V1_FILES
    assert plan.rollback_delete_files == V2_STATIC_ASSETS
    assert plan.commit_concurrency_policy == "huggingface_create_commit_parent_commit_cas"
    assert plan.publication_authorized is False
    assert plan.remote_mutation is False
    assert plan.rollback_executed is False


def test_v1_to_v2_asset_delta_is_exact_and_invertible() -> None:
    plan = build_existing_space_v2_update_plan(PROJECT_ROOT)
    current = {item.relative_path for item in plan.rollback_upload_files}
    updated = (current - set(plan.delete_files)) | {
        item.relative_path for item in plan.upload_files
    }
    assert updated == {item.relative_path for item in plan.upload_files}
    restored = (updated - set(plan.rollback_delete_files)) | {
        item.relative_path for item in plan.rollback_upload_files
    }
    assert restored == current
    assert plan.delete_files == EXPECTED_V2_DELETIONS
    assert plan.rollback_delete_files == EXPECTED_ROLLBACK_DELETIONS


def test_canonical_plan_is_repeatable_and_has_no_secrets() -> None:
    first = canonical_update_plan_json(build_existing_space_v2_update_plan(PROJECT_ROOT))
    second = canonical_update_plan_json(build_existing_space_v2_update_plan(PROJECT_ROOT))
    assert first == second
    assert first.endswith(b"\n")
    assert json.loads(first)["publication_authorized"] is False
    lowered = first.lower()
    for marker in (b"hf_token", b"access_token", b"authorization: bearer", b"api_key"):
        assert marker not in lowered


def test_plan_schema_rejects_deleting_readme() -> None:
    payload = build_existing_space_v2_update_plan(PROJECT_ROOT).model_dump()
    payload["delete_files"] = ("README.md", "assets/index-DBdnOm5m.js")
    with pytest.raises(ValidationError, match="V2 deletions"):
        ExistingSpaceV2UpdatePlan.model_validate(payload)


def test_plan_schema_rejects_non_frozen_parent_revision() -> None:
    payload = build_existing_space_v2_update_plan(PROJECT_ROOT).model_dump()
    payload["expected_parent_commit"] = "f" * 40
    with pytest.raises(ValidationError, match="expected_parent_commit"):
        ExistingSpaceV2UpdatePlan.model_validate(payload)


def test_plan_schema_rejects_publication_authorization_escalation() -> None:
    payload = build_existing_space_v2_update_plan(PROJECT_ROOT).model_dump()
    payload["publication_authorized"] = True
    with pytest.raises(ValidationError, match="publication_authorized"):
        ExistingSpaceV2UpdatePlan.model_validate(payload)


def test_plan_schema_rejects_unexpected_asset_upload() -> None:
    payload = build_existing_space_v2_update_plan(PROJECT_ROOT).model_dump()
    payload["upload_files"][1]["relative_path"] = "assets/unreviewed.css"
    with pytest.raises(ValidationError, match="V2 uploads"):
        ExistingSpaceV2UpdatePlan.model_validate(payload)


def test_operation_plan_has_no_network_or_mutation_dependency() -> None:
    # Importing the module and executing its local plan needs neither credentials
    # nor a remote repository. The CLI exposes only --check-local.
    import inspect

    import specsafe.hugging_face_space_publication_v2.update_plan as target

    source = inspect.getsource(target)
    assert "huggingface_hub" not in source
    assert "create_commit(" not in source
    assert "delete_repo(" not in source
    assert "update_repo_settings(" not in source
