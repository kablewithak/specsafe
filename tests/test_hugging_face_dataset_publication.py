from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from specsafe.hugging_face_dataset_publication import (
    DatasetPublicationError,
    build_publication_plan,
    preflight_remote_publication,
    publish_authorized_dataset,
)
from specsafe.hugging_face_dataset_publication.service import (
    AUTHORIZATION_RELATIVE_PATH,
    CANDIDATE_RELATIVE_DIRECTORY,
    EXPECTED_REMOTE_FILES,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXED_REVISION = "a" * 40
FIXED_TIME = datetime(2026, 7, 10, 22, 0, tzinfo=UTC)


class FakeHubGateway:
    def __init__(
        self,
        candidate_root: Path,
        *,
        identity: Mapping[str, object] | None = None,
        repository_exists: bool = False,
        public_hash_drift: str | None = None,
    ) -> None:
        self._candidate_root = candidate_root
        self._identity = identity or {"name": "kabo", "orgs": []}
        self._repository_exists = repository_exists
        self._public_hash_drift = public_hash_drift
        self._files: dict[str, bytes] = {".gitattributes": b"*.json filter=lfs\n"}
        self.private = True
        self.deleted = False
        self.created = False
        self.committed = False

    def identity(self) -> Mapping[str, object]:
        return self._identity

    def repository_exists(self, repo_id: str) -> bool:
        return self._repository_exists

    def create_private_dataset(self, repo_id: str) -> str:
        self.created = True
        return f"https://huggingface.co/datasets/{repo_id}"

    def list_files(self, repo_id: str, *, revision: str | None, anonymous: bool) -> tuple[str, ...]:
        if anonymous and self.private:
            raise RuntimeError("anonymous access denied")
        return tuple(sorted(self._files))

    def commit_exact_files(
        self,
        repo_id: str,
        files: Mapping[str, Path],
        *,
        delete_paths: tuple[str, ...],
    ) -> str:
        for path in delete_paths:
            self._files.pop(path, None)
        for name, path in files.items():
            self._files[name] = path.read_bytes()
        self.committed = True
        return FIXED_REVISION

    def read_file(
        self,
        repo_id: str,
        filename: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> bytes:
        if anonymous and self.private:
            raise RuntimeError("anonymous access denied")
        payload = self._files[filename]
        if anonymous and filename == self._public_hash_drift:
            return payload + b"drift"
        return payload

    def dataset_state(
        self,
        repo_id: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> Mapping[str, object]:
        return {
            "id": repo_id,
            "sha": revision,
            "private": self.private,
            "gated": False,
        }

    def make_public(self, repo_id: str) -> None:
        self.private = False

    def make_private(self, repo_id: str) -> None:
        self.private = True

    def delete_dataset(self, repo_id: str) -> None:
        self.deleted = True


def test_local_publication_plan_is_bound_to_exact_authorization_and_files() -> None:
    plan = build_publication_plan(PROJECT_ROOT)
    assert plan.authorization_decision_sha256 == (
        "bf96e015379f8ad955791c28b8ba75b123b3d748d2192943190b056eb5aadc46"
    )
    assert plan.publication_manifest_sha256 == (
        "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
    )
    assert tuple(item.relative_path for item in plan.files) == EXPECTED_REMOTE_FILES
    assert plan.upload_mode == "private_stage_exact_commit_public_release"


def test_remote_preflight_rejects_unknown_namespace() -> None:
    gateway = FakeHubGateway(
        PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY,
        identity={"name": "kabo", "orgs": [{"name": "specsafe-labs"}]},
    )
    with pytest.raises(DatasetPublicationError, match="not the authenticated account"):
        preflight_remote_publication(PROJECT_ROOT, "other-user", gateway)


def test_remote_preflight_accepts_authenticated_organization() -> None:
    gateway = FakeHubGateway(
        PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY,
        identity={"name": "kabo", "orgs": [{"name": "specsafe-labs"}]},
    )
    repo_id = preflight_remote_publication(PROJECT_ROOT, "specsafe-labs", gateway)
    assert repo_id == "specsafe-labs/specsafe-bounded-negative-evidence-v1"


def test_remote_preflight_rejects_existing_repository() -> None:
    gateway = FakeHubGateway(
        PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY,
        repository_exists=True,
    )
    with pytest.raises(DatasetPublicationError, match="existing Hugging Face Dataset"):
        preflight_remote_publication(PROJECT_ROOT, "kabo", gateway)


def test_publication_stages_privately_verifies_publicly_and_writes_receipt(
    tmp_path: Path,
) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_RELATIVE_DIRECTORY)
    receipt_path = project / "evidence" / "receipt.json"
    receipt = publish_authorized_dataset(
        project,
        "kabo",
        gateway,
        now=lambda: FIXED_TIME,
        receipt_path=receipt_path,
    )
    assert gateway.created is True
    assert gateway.committed is True
    assert gateway.private is False
    assert gateway.deleted is False
    assert tuple(sorted(gateway._files)) == EXPECTED_REMOTE_FILES
    assert receipt.repository_id == "kabo/specsafe-bounded-negative-evidence-v1"
    assert receipt.published_revision == FIXED_REVISION
    assert receipt.published_at == FIXED_TIME
    saved = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert saved["anonymous_public_verification_passed"] is True
    assert "token" not in receipt_path.read_text(encoding="utf-8").lower()


def test_private_stage_failure_deletes_new_repository(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_RELATIVE_DIRECTORY)
    gateway._files["unexpected.txt"] = b"unexpected"
    with pytest.raises(DatasetPublicationError, match="unexpected files"):
        publish_authorized_dataset(project, "kabo", gateway)
    assert gateway.deleted is True


def test_public_verification_failure_returns_repository_to_private(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(
        project / CANDIDATE_RELATIVE_DIRECTORY,
        public_hash_drift="README.md",
    )
    with pytest.raises(DatasetPublicationError, match="remote file hash mismatch"):
        publish_authorized_dataset(project, "kabo", gateway)
    assert gateway.private is True
    assert gateway.deleted is False


def test_candidate_drift_revokes_publication(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    readme = project / CANDIDATE_RELATIVE_DIRECTORY / "README.md"
    readme.write_bytes(readme.read_bytes() + b"drift")
    with pytest.raises(DatasetPublicationError, match="publication file drifted"):
        build_publication_plan(project)


def test_receipt_is_never_overwritten(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_RELATIVE_DIRECTORY)
    receipt_path = project / "evidence" / "receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text("retained\n", encoding="utf-8")
    with pytest.raises(DatasetPublicationError, match="already exists"):
        publish_authorized_dataset(
            project,
            "kabo",
            gateway,
            receipt_path=receipt_path,
        )
    assert gateway.created is False


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")

    authorization = project / AUTHORIZATION_RELATIVE_PATH
    authorization.parent.mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / AUTHORIZATION_RELATIVE_PATH, authorization)

    candidate = project / CANDIDATE_RELATIVE_DIRECTORY
    candidate.parent.mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / CANDIDATE_RELATIVE_DIRECTORY, candidate)
    return project
