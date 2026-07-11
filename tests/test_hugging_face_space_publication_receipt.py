from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from specsafe.hugging_face_space_publication_receipt import (
    RECEIPT_RELATIVE_PATH,
    RECONCILIATION_RELATIVE_PATH,
    ReceiptReconciliationError,
    check_committed_reconciliation,
    reconcile_remote_publication,
    verify_local_publication_receipt,
    write_remote_reconciliation,
)
from specsafe.hugging_face_space_publication_receipt.service import (
    EXPECTED_APPLICATION_URL,
    EXPECTED_PUBLISHED_REVISION,
    EXPECTED_REPOSITORY_ID,
    PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
    PREBUILT_MANIFEST_RELATIVE_PATH,
    SOURCE_MANIFEST_RELATIVE_PATH,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = datetime(2026, 7, 11, 18, 30, tzinfo=UTC)


class FakeAnonymousGateway:
    def __init__(
        self,
        candidate_root: Path,
        *,
        private: bool = False,
        stage: str = "RUNNING",
        file_drift: str | None = None,
        invalid_application: bool = False,
    ) -> None:
        self._candidate_root = candidate_root
        self._private = private
        self._stage = stage
        self._file_drift = file_drift
        self._invalid_application = invalid_application

    def repository_state(
        self,
        repo_id: str,
        *,
        revision: str,
    ) -> Mapping[str, object]:
        return {
            "id": repo_id,
            "sha": revision,
            "private": self._private,
            "gated": False,
            "sdk": "static",
            "stage": self._stage,
        }

    def list_files(
        self,
        repo_id: str,
        *,
        revision: str,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                path.relative_to(self._candidate_root).as_posix()
                for path in self._candidate_root.rglob("*")
                if path.is_file()
            )
        )

    def read_file(
        self,
        repo_id: str,
        filename: str,
        *,
        revision: str,
    ) -> bytes:
        payload = (self._candidate_root / filename).read_bytes()
        if filename == self._file_drift:
            return payload + b"drift"
        return payload

    def fetch_application(self, application_url: str) -> Mapping[str, object]:
        body = b'<html><title>SpecSafe</title><div id="root"></div></html>'
        if self._invalid_application:
            body = b"<html>wrong application</html>"
        return {
            "application_url": application_url,
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
            "body": body,
        }


def test_local_receipt_binds_exact_publication_lineage() -> None:
    verified = verify_local_publication_receipt(PROJECT_ROOT)

    assert verified.receipt.schema_version == ("specsafe_hugging_face_space_publication_receipt_v2")
    assert verified.receipt.repository_id == EXPECTED_REPOSITORY_ID
    assert verified.receipt.application_url == EXPECTED_APPLICATION_URL
    assert verified.receipt.published_revision == EXPECTED_PUBLISHED_REVISION
    assert verified.receipt.remote_file_count == 5
    assert verified.receipt_byte_count > 0
    assert len(verified.receipt_sha256) == 64


def test_remote_reconciliation_verifies_exact_anonymous_publication(
    tmp_path: Path,
) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
    )

    record = reconcile_remote_publication(
        project,
        gateway,
        now=FIXED_TIME,
    )

    assert record.verified_at == FIXED_TIME
    assert record.credential_used is False
    assert record.remote_file_count == 5
    assert record.anonymous_repository_verified is True
    assert record.anonymous_file_hashes_verified is True
    assert record.anonymous_application_verified is True


def test_remote_file_hash_drift_revokes_reconciliation(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
        file_drift="README.md",
    )

    with pytest.raises(ReceiptReconciliationError, match="file drifted: README.md"):
        reconcile_remote_publication(project, gateway)


def test_private_remote_space_revokes_reconciliation(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
        private=True,
    )

    with pytest.raises(ReceiptReconciliationError, match="state does not match"):
        reconcile_remote_publication(project, gateway)


def test_terminal_remote_stage_revokes_reconciliation(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
        stage="CONFIG_ERROR",
    )

    with pytest.raises(ReceiptReconciliationError, match="state does not match"):
        reconcile_remote_publication(project, gateway)


def test_public_application_marker_drift_revokes_reconciliation(
    tmp_path: Path,
) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
        invalid_application=True,
    )

    with pytest.raises(ReceiptReconciliationError, match="required HTML markers"):
        reconcile_remote_publication(project, gateway)


def test_receipt_with_forbidden_credential_marker_is_rejected(
    tmp_path: Path,
) -> None:
    project = _copy_minimal_project(tmp_path)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    receipt_path.write_bytes(receipt_path.read_bytes() + b"\nhf_token\n")

    with pytest.raises(ReceiptReconciliationError, match="credential marker"):
        verify_local_publication_receipt(project)


def test_candidate_manifest_drift_revokes_local_verification(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    manifest_path = project / PREBUILT_MANIFEST_RELATIVE_PATH
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["candidate_tree_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ReceiptReconciliationError, match="authorized retained lineage"):
        verify_local_publication_receipt(project)


def test_reconciliation_write_and_committed_check_round_trip(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
    )

    written = write_remote_reconciliation(
        project,
        gateway,
        now=FIXED_TIME,
    )
    checked = check_committed_reconciliation(project)

    assert checked == written
    payload = (project / RECONCILIATION_RELATIVE_PATH).read_bytes()
    assert payload.endswith(b"\n")


def test_reconciliation_is_never_overwritten(tmp_path: Path) -> None:
    project = _copy_minimal_project(tmp_path)
    gateway = FakeAnonymousGateway(
        project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
    )
    target = project / RECONCILIATION_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("retained\n", encoding="utf-8")

    with pytest.raises(ReceiptReconciliationError, match="refusing to overwrite"):
        write_remote_reconciliation(project, gateway, now=FIXED_TIME)


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copyfile(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")

    for relative_path in (
        RECEIPT_RELATIVE_PATH,
        PREBUILT_MANIFEST_RELATIVE_PATH,
        SOURCE_MANIFEST_RELATIVE_PATH,
    ):
        target = project / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative_path, target)

    candidate = project / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH
    candidate.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        PROJECT_ROOT / PREBUILT_CANDIDATE_ROOT_RELATIVE_PATH,
        candidate,
    )
    return project
