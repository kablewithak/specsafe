from __future__ import annotations

from pathlib import Path

import pytest

from specsafe.hugging_face_dataset_publication import (
    WorkflowPublicationGateError,
    validate_workflow_environment,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/publish-hugging-face-dataset.yml"


def _valid_environment() -> dict[str, str]:
    return {
        "REQUESTED_NAMESPACE": "KaboKableMolefe",
        "PUBLICATION_CONFIRMATION": "PUBLISH_EXACT_DATASET",
        "GITHUB_REF": "refs/heads/main",
        "HF_TOKEN": "test-secret-value-never-retained",
    }


def test_workflow_gate_accepts_exact_manual_publication_context() -> None:
    gate = validate_workflow_environment(_valid_environment())
    assert gate.namespace == "KaboKableMolefe"
    assert gate.confirmation == "PUBLISH_EXACT_DATASET"
    assert gate.git_ref == "refs/heads/main"
    assert gate.credential_present is True
    assert "test-secret-value" not in gate.model_dump_json()
    assert "HF_TOKEN" not in gate.model_dump_json()


def test_workflow_gate_rejects_wrong_namespace() -> None:
    environment = _valid_environment()
    environment["REQUESTED_NAMESPACE"] = "other-owner"
    with pytest.raises(WorkflowPublicationGateError, match="KaboKableMolefe"):
        validate_workflow_environment(environment)


def test_workflow_gate_rejects_wrong_confirmation() -> None:
    environment = _valid_environment()
    environment["PUBLICATION_CONFIRMATION"] = "publish"
    with pytest.raises(WorkflowPublicationGateError, match="PUBLISH_EXACT_DATASET"):
        validate_workflow_environment(environment)


def test_workflow_gate_rejects_non_main_ref() -> None:
    environment = _valid_environment()
    environment["GITHUB_REF"] = "refs/heads/feature"
    with pytest.raises(WorkflowPublicationGateError, match="main branch"):
        validate_workflow_environment(environment)


def test_workflow_gate_rejects_missing_secret_without_retaining_a_value() -> None:
    environment = _valid_environment()
    environment["HF_TOKEN"] = ""
    with pytest.raises(WorkflowPublicationGateError, match="HF_TOKEN") as error:
        validate_workflow_environment(environment)
    assert "test-secret-value" not in str(error.value)


def test_workflow_is_manual_read_only_and_environment_protected() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "\n  push:" not in workflow
    assert "\n  pull_request:" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "environment: hugging-face-publication" in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "persist-credentials: false" in workflow


def test_workflow_uses_protected_secret_without_token_arguments_or_git_writes() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "HF_TOKEN: ${{ secrets.HF_TOKEN }}" in workflow
    assert "--token" not in workflow
    assert "hf auth login" not in workflow
    assert "git push" not in workflow
    assert "contents: write" not in workflow


def test_workflow_runs_preflight_before_publication_and_retains_receipt() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    preflight_command = "--preflight \\\n            --namespace"
    publication_command = "--publish \\\n            --namespace"
    assert preflight_command in workflow
    assert publication_command in workflow
    assert workflow.index(preflight_command) < workflow.index(publication_command)
    assert "actions/upload-artifact@v4" in workflow
    assert "if-no-files-found: error" in workflow
    assert "retention-days: 30" in workflow
