from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

import specsafe.hugging_face_space_publication.service as publication_service
from specsafe.hugging_face_space_publication import (
    SpacePublicationError,
    build_publication_plan,
    preflight_remote_publication,
    publish_authorized_space,
)
from specsafe.hugging_face_space_publication.service import (
    CANDIDATE_MANIFEST_RELATIVE_PATH,
    CANDIDATE_ROOT_RELATIVE_PATH,
    EXPECTED_CANDIDATE_PATHS,
    EXPECTED_CANDIDATE_TREE_SHA256,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXED_REVISION = "a" * 40
FIXED_GIT_SHA = "b" * 40
FIXED_TIME = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)


class FakeHubGateway:
    def __init__(
        self,
        candidate_root: Path,
        *,
        identity: Mapping[str, object] | None = None,
        repository_exists: bool = False,
        public_hash_drift: str | None = None,
        invalid_application: bool = False,
    ) -> None:
        self._candidate_root = candidate_root
        self._identity = identity or {"name": "KaboKableMolefe", "orgs": []}
        self._repository_exists = repository_exists
        self._public_hash_drift = public_hash_drift
        self._invalid_application = invalid_application
        self._files: dict[str, bytes] = {".gitattributes": b"*.json filter=lfs\n"}
        self.private = True
        self.deleted = False
        self.created = False
        self.committed = False

    def identity(self) -> Mapping[str, object]:
        return self._identity

    def repository_exists(self, repo_id: str) -> bool:
        return self._repository_exists

    def create_private_space(self, repo_id: str) -> str:
        self.created = True
        return f"https://huggingface.co/spaces/{repo_id}"

    def list_files(
        self,
        repo_id: str,
        *,
        revision: str | None,
        anonymous: bool,
    ) -> tuple[str, ...]:
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

    def space_state(
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
            "sdk": "static",
        }

    def make_public(self, repo_id: str) -> None:
        self.private = False

    def make_private(self, repo_id: str) -> None:
        self.private = True

    def delete_space(self, repo_id: str) -> None:
        self.deleted = True

    def wait_for_public_application(
        self,
        repo_id: str,
        *,
        timeout_seconds: int,
    ) -> Mapping[str, object]:
        body = b'<html><title>SpecSafe</title><div id="root"></div></html>'
        if self._invalid_application:
            body = b"<html>wrong application</html>"
        return {
            "application_url": ("https://kabokablemolefe-specsafe-reliability-lab.static.hf.space"),
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
            "body": body,
            "stage": "RUNNING",
        }


def test_local_plan_is_bound_to_exact_prebuilt_candidate() -> None:
    plan = build_publication_plan(PROJECT_ROOT)

    assert plan.schema_version == "specsafe_hugging_face_space_publication_plan_v2"
    assert plan.candidate_tree_sha256 == EXPECTED_CANDIDATE_TREE_SHA256
    assert plan.candidate_file_count == 5
    assert len(plan.files) == 5
    assert tuple(item.relative_path for item in plan.files) == EXPECTED_CANDIDATE_PATHS
    assert plan.source_candidate_file_count == 35
    assert plan.provider_side_build_required is False
    assert plan.build_strategy == "local_validated_prebuilt_static_assets"
    assert plan.sdk == "static"
    assert plan.upload_mode == "private_stage_exact_commit_public_release"


def test_prebuilt_readme_has_no_provider_side_build_command() -> None:
    readme = (PROJECT_ROOT / CANDIDATE_ROOT_RELATIVE_PATH / "README.md").read_text(encoding="utf-8")

    assert "sdk: static" in readme
    assert "app_file: index.html" in readme
    assert "provider_side_build_required=false" in readme
    assert "app_build_command:" not in readme


def test_remote_preflight_requires_exact_namespace() -> None:
    gateway = FakeHubGateway(PROJECT_ROOT / CANDIDATE_ROOT_RELATIVE_PATH)
    with pytest.raises(SpacePublicationError, match="must be exactly KaboKableMolefe"):
        preflight_remote_publication(PROJECT_ROOT, "other-user", gateway)


def test_remote_preflight_rejects_existing_space() -> None:
    gateway = FakeHubGateway(
        PROJECT_ROOT / CANDIDATE_ROOT_RELATIVE_PATH,
        repository_exists=True,
    )
    with pytest.raises(SpacePublicationError, match="existing Hugging Face Space"):
        preflight_remote_publication(PROJECT_ROOT, "KaboKableMolefe", gateway)


def test_publication_stages_prebuilt_assets_and_writes_v2_receipt(
    tmp_path: Path,
) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_ROOT_RELATIVE_PATH)
    receipt_path = project / "evidence" / "receipt.json"
    receipt = publish_authorized_space(
        project,
        "KaboKableMolefe",
        gateway,
        published_from_git_sha=FIXED_GIT_SHA,
        now=lambda: FIXED_TIME,
        receipt_path=receipt_path,
        application_timeout_seconds=30,
    )

    plan = build_publication_plan(project)
    expected_files = tuple(item.relative_path for item in plan.files)
    assert gateway.created is True
    assert gateway.committed is True
    assert gateway.private is False
    assert gateway.deleted is False
    assert tuple(sorted(gateway._files)) == expected_files
    assert receipt.schema_version == "specsafe_hugging_face_space_publication_receipt_v2"
    assert receipt.repository_id == "KaboKableMolefe/specsafe-reliability-lab"
    assert receipt.published_revision == FIXED_REVISION
    assert receipt.published_from_git_sha == FIXED_GIT_SHA
    assert receipt.published_at == FIXED_TIME
    assert receipt.remote_file_count == 5
    assert receipt.provider_side_build_required is False
    assert receipt.prebuilt_static_assets_verified is True
    saved = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert saved["anonymous_repository_verification_passed"] is True
    assert saved["anonymous_application_verification_passed"] is True
    assert saved["served_html_verified"] is True
    lowered = receipt_path.read_bytes().lower()
    for marker in (b"authorization: bearer", b"access_token", b"api_key", b"hf_token"):
        assert marker not in lowered


def test_private_stage_failure_deletes_new_space(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_ROOT_RELATIVE_PATH)
    gateway._files["unexpected.txt"] = b"unexpected"
    with pytest.raises(SpacePublicationError, match="unexpected files"):
        publish_authorized_space(
            project,
            "KaboKableMolefe",
            gateway,
            published_from_git_sha=FIXED_GIT_SHA,
        )
    assert gateway.deleted is True


def test_public_repository_failure_returns_space_to_private(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(
        project / CANDIDATE_ROOT_RELATIVE_PATH,
        public_hash_drift="README.md",
    )
    with pytest.raises(SpacePublicationError, match="remote Space file hash mismatch"):
        publish_authorized_space(
            project,
            "KaboKableMolefe",
            gateway,
            published_from_git_sha=FIXED_GIT_SHA,
        )
    assert gateway.private is True
    assert gateway.deleted is False


def test_public_application_failure_returns_space_to_private(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(
        project / CANDIDATE_ROOT_RELATIVE_PATH,
        invalid_application=True,
    )
    with pytest.raises(SpacePublicationError, match="required application markers"):
        publish_authorized_space(
            project,
            "KaboKableMolefe",
            gateway,
            published_from_git_sha=FIXED_GIT_SHA,
        )
    assert gateway.private is True
    assert gateway.deleted is False


def test_receipt_write_failure_returns_space_to_private(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_ROOT_RELATIVE_PATH)

    def fail_write(*args: object, **kwargs: object) -> None:
        raise SpacePublicationError(
            publication_service.SpacePublicationErrorCode.RECEIPT_WRITE_FAILED,
            "simulated receipt write failure",
        )

    monkeypatch.setattr(publication_service, "_write_receipt", fail_write)
    with pytest.raises(SpacePublicationError, match="simulated receipt write failure"):
        publish_authorized_space(
            project,
            "KaboKableMolefe",
            gateway,
            published_from_git_sha=FIXED_GIT_SHA,
        )
    assert gateway.private is True
    assert gateway.deleted is False


def test_receipt_is_never_overwritten(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeHubGateway(project / CANDIDATE_ROOT_RELATIVE_PATH)
    receipt_path = project / "evidence" / "receipt.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text("retained\n", encoding="utf-8")
    with pytest.raises(SpacePublicationError, match="already exists"):
        publish_authorized_space(
            project,
            "KaboKableMolefe",
            gateway,
            published_from_git_sha=FIXED_GIT_SHA,
            receipt_path=receipt_path,
        )
    assert gateway.created is False


def test_candidate_drift_revokes_publication(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    readme = project / CANDIDATE_ROOT_RELATIVE_PATH / "README.md"
    readme.write_bytes(readme.read_bytes() + b"drift")
    with pytest.raises(SpacePublicationError, match="candidate file drifted: README.md"):
        build_publication_plan(project)


def test_provider_side_build_flag_revokes_publication(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    manifest_path = project / CANDIDATE_MANIFEST_RELATIVE_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_side_build_required"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SpacePublicationError, match="failed strict validation"):
        build_publication_plan(project)


def test_asset_path_drift_revokes_publication(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    manifest_path = project / CANDIDATE_MANIFEST_RELATIVE_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][1]["relative_path"] = "assets/index-Corrupt.css"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SpacePublicationError, match="outside the authorized boundary"):
        build_publication_plan(project)


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")

    manifest = project / CANDIDATE_MANIFEST_RELATIVE_PATH
    manifest.parent.mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / CANDIDATE_MANIFEST_RELATIVE_PATH, manifest)

    candidate = project / CANDIDATE_ROOT_RELATIVE_PATH
    candidate.parent.mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / CANDIDATE_ROOT_RELATIVE_PATH, candidate)
    return project
