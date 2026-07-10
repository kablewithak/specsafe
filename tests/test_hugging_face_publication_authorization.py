from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.publication_authorization import (
    PublicationAuthorizationError,
    build_publication_authorization_decision,
    check_committed_publication_authorization_decision,
)
from specsafe.publication_authorization.models import (
    ExactPublicationAuthorizationDecision,
)
from specsafe.publication_authorization.review import (
    CANDIDATE_RELATIVE_DIRECTORY,
    DECISION_RELATIVE_PATH,
    EXPECTED_FILES,
    EXPECTED_MANIFEST_SHA256,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY
DECISION_PATH = PROJECT_ROOT / DECISION_RELATIVE_PATH


def test_committed_authorization_decision_is_canonical() -> None:
    check_committed_publication_authorization_decision(PROJECT_ROOT)
    expected = build_publication_authorization_decision(
        PROJECT_ROOT,
        write_output=False,
    )
    actual = ExactPublicationAuthorizationDecision.model_validate_json(DECISION_PATH.read_bytes())
    assert actual == expected


def test_authorization_binds_exact_manifest_and_performs_no_upload() -> None:
    decision = ExactPublicationAuthorizationDecision.model_validate_json(DECISION_PATH.read_bytes())
    assert decision.decision_outcome == "AUTHORIZE_EXACT_PUBLICATION"
    assert decision.publication_authorized is True
    assert decision.publication_performed is False
    assert decision.publication_manifest.sha256 == EXPECTED_MANIFEST_SHA256
    assert decision.gate_checks.remote_repository_created is False
    assert decision.gate_checks.public_upload_performed is False


def test_authorized_files_match_exact_candidate_allowlist() -> None:
    decision = ExactPublicationAuthorizationDecision.model_validate_json(DECISION_PATH.read_bytes())
    paths = tuple(item.relative_path for item in decision.authorized_files)
    assert paths == EXPECTED_FILES
    assert decision.target.exact_candidate_files == EXPECTED_FILES
    assert decision.target.visibility == "public"
    assert decision.target.gated is False


def test_authorized_file_hashes_match_committed_candidate() -> None:
    decision = ExactPublicationAuthorizationDecision.model_validate_json(DECISION_PATH.read_bytes())
    for artifact in decision.authorized_files:
        payload = (CANDIDATE_ROOT / artifact.relative_path).read_bytes()
        assert len(payload) == artifact.byte_count
        import hashlib

        assert hashlib.sha256(payload).hexdigest() == artifact.sha256


def test_decision_contract_rejects_unknown_fields() -> None:
    value = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    value["unexpected"] = "field"
    with pytest.raises(ValidationError):
        ExactPublicationAuthorizationDecision.model_validate(value)


def test_decision_contract_rejects_publication_performed() -> None:
    value = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    value["publication_performed"] = True
    with pytest.raises(ValidationError):
        ExactPublicationAuthorizationDecision.model_validate(value)


def test_manifest_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    manifest = project / CANDIDATE_RELATIVE_DIRECTORY / "publication_manifest.json"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    with pytest.raises(PublicationAuthorizationError, match="reviewed bytes"):
        build_publication_authorization_decision(project, write_output=False)


def test_candidate_file_drift_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    readme = project / CANDIDATE_RELATIVE_DIRECTORY / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    with pytest.raises(PublicationAuthorizationError, match="README.md"):
        build_publication_authorization_decision(project, write_output=False)


def test_unexpected_candidate_file_is_rejected(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    candidate = project / CANDIDATE_RELATIVE_DIRECTORY
    (candidate / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(PublicationAuthorizationError, match="allowlist"):
        build_publication_authorization_decision(project, write_output=False)


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")
    target = project / CANDIDATE_RELATIVE_DIRECTORY
    target.parent.mkdir(parents=True)
    shutil.copytree(CANDIDATE_ROOT, target)
    return project
