from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path

import pytest

import specsafe.hugging_face_space_publication_v2.readiness as readiness
from specsafe.hugging_face_space_publication_receipt import verify_local_publication_receipt
from specsafe.hugging_face_space_publication_v2 import (
    V2ReleaseReadinessError,
    build_local_v2_release_readiness,
    preflight_existing_v2_space,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeReadOnlyGateway:
    def __init__(
        self,
        *,
        head: str = readiness.EXPECTED_V1_REVISION,
        file_drift: str | None = None,
        extra_file: bool = False,
        private: bool = False,
        invalid_application: bool = False,
    ) -> None:
        receipt = verify_local_publication_receipt(PROJECT_ROOT).receipt
        self.head = head
        self.file_drift = file_drift
        self.extra_file = extra_file
        self.private = private
        self.invalid_application = invalid_application
        self.calls: list[str] = []
        self.application_url = receipt.application_url
        source_dir = PROJECT_ROOT / (
            "release/hugging-face-space-prebuilt-publication/"
            "specsafe-reliability-lab/candidate/space"
        )
        self.payloads = {name: (source_dir / name).read_bytes() for name in receipt.remote_files}

    def repository_state(self, repo_id: str, *, revision: str) -> Mapping[str, object]:
        self.calls.append("repository_state")
        assert revision == "main"
        return {
            "id": repo_id,
            "sha": self.head,
            "private": self.private,
            "gated": False,
            "sdk": "static",
            "stage": "RUNNING",
        }

    def list_files(self, repo_id: str, *, revision: str) -> tuple[str, ...]:
        self.calls.append("list_files")
        assert revision == self.head
        paths = list(self.payloads)
        if self.extra_file:
            paths.append("unexpected.json")
        return tuple(sorted(paths))

    def read_file(self, repo_id: str, filename: str, *, revision: str) -> bytes:
        self.calls.append("read_file")
        assert revision == self.head
        payload = self.payloads[filename]
        return payload + b"drift" if filename == self.file_drift else payload

    def fetch_application(self, application_url: str) -> Mapping[str, object]:
        self.calls.append("fetch_application")
        assert application_url == self.application_url
        body = (
            b"wrong application"
            if self.invalid_application
            else b'<html><title>SpecSafe</title><div id="root"></div></html>'
        )
        return {
            "application_url": application_url,
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
            "body": body,
        }


def _copy_v2(root: Path) -> Path:
    target = root / "project"
    target.mkdir()
    (target / "pyproject.toml").write_text("[project]\nname = 'specsafe'\n", encoding="utf-8")
    for relative in (readiness.V2_MANIFEST_PATH, readiness.V2_SOURCE_MANIFEST_PATH):
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, dst)
    destination = target / readiness.V2_CANDIDATE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PROJECT_ROOT / readiness.V2_CANDIDATE_PATH, destination)
    return target


def test_local_readiness_preserves_v2_and_v1_lineage() -> None:
    plan = build_local_v2_release_readiness(PROJECT_ROOT)
    assert plan.v2_prebuilt_file_count == 5
    assert plan.local_v1_receipt_verified is True
    assert plan.local_v1_reconciliation_verified is True
    assert plan.current_remote_head_observed is False
    assert plan.publication_authorized is False
    assert plan.remote_mutation is False


def test_new_v2_manifest_drift_fails_closed(tmp_path: Path) -> None:
    root = _copy_v2(tmp_path)
    manifest = root / readiness.V2_MANIFEST_PATH
    manifest.write_bytes(manifest.read_bytes() + b" ")

    with pytest.raises(V2ReleaseReadinessError, match="manifest changed"):
        readiness._load_manifest(root)


def test_unknown_v2_file_fails_closed(tmp_path: Path) -> None:
    root = _copy_v2(tmp_path)
    manifest = readiness._load_manifest(root)
    unexpected = root / readiness.V2_CANDIDATE_PATH / "secret.txt"
    unexpected.write_bytes(b"unknown")
    with pytest.raises(V2ReleaseReadinessError, match="allowlist"):
        readiness._verify_candidate(root, manifest)


def test_v2_byte_drift_fails_closed(tmp_path: Path) -> None:
    root = _copy_v2(tmp_path)
    manifest = readiness._load_manifest(root)
    index = root / readiness.V2_CANDIDATE_PATH / "index.html"
    index.write_bytes(index.read_bytes() + b"drift")
    with pytest.raises(V2ReleaseReadinessError, match="byte hash drifted"):
        readiness._verify_candidate(root, manifest)


def test_v2_source_manifest_drift_fails_closed(tmp_path: Path) -> None:
    root = _copy_v2(tmp_path)
    manifest_source = root / readiness.V2_SOURCE_MANIFEST_PATH
    manifest_source.write_bytes(manifest_source.read_bytes() + b"drift")
    with pytest.raises(V2ReleaseReadinessError, match="source candidate manifest hash"):
        readiness._load_manifest(root)


def test_v1_rollback_anchor_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    def invalid_v1(_: Path) -> None:
        raise ValueError("simulated missing rollback evidence")

    monkeypatch.setattr(readiness, "check_committed_reconciliation", invalid_v1)
    with pytest.raises(V2ReleaseReadinessError, match="receipt or reconciliation"):
        build_local_v2_release_readiness(PROJECT_ROOT)


def test_remote_preflight_is_read_only_and_pinned_to_live_v1() -> None:
    gateway = FakeReadOnlyGateway()
    report = preflight_existing_v2_space(PROJECT_ROOT, gateway)
    assert report.observed_current_revision == readiness.EXPECTED_V1_REVISION
    assert report.existing_v1_remote_files_verified is True
    assert report.current_remote_revision_verified is True
    assert report.public_application_verified is True
    assert report.publication_authorized is False
    assert report.remote_mutation is False
    assert len(gateway.calls) == 8
    assert gateway.calls[-1] == "fetch_application"


def test_remote_head_change_fails_before_remote_file_access() -> None:
    gateway = FakeReadOnlyGateway(head="f" * 40)
    with pytest.raises(V2ReleaseReadinessError, match="main changed"):
        preflight_existing_v2_space(PROJECT_ROOT, gateway)
    assert gateway.calls == ["repository_state"]


def test_remote_extra_file_fails_closed() -> None:
    gateway = FakeReadOnlyGateway(extra_file=True)
    with pytest.raises(V2ReleaseReadinessError, match="allowlist"):
        preflight_existing_v2_space(PROJECT_ROOT, gateway)
    assert "read_file" not in gateway.calls


def test_remote_modified_file_fails_closed() -> None:
    gateway = FakeReadOnlyGateway(file_drift="README.md")
    with pytest.raises(V2ReleaseReadinessError, match="file drifted"):
        preflight_existing_v2_space(PROJECT_ROOT, gateway)


def test_remote_private_or_application_mismatch_fails_closed() -> None:
    gateway = FakeReadOnlyGateway(private=True)
    with pytest.raises(V2ReleaseReadinessError, match="expected public"):
        preflight_existing_v2_space(PROJECT_ROOT, gateway)

    gateway = FakeReadOnlyGateway(invalid_application=True)
    with pytest.raises(V2ReleaseReadinessError, match="lost required"):
        preflight_existing_v2_space(PROJECT_ROOT, gateway)
