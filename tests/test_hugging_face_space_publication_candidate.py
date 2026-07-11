from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import specsafe.hugging_face_space_publication_candidate.builder as publication_builder
from specsafe.hugging_face_space_evidence import (
    check_committed_space_evidence_index,
)
from specsafe.hugging_face_space_evidence.builder import (
    OUTPUT_RELATIVE_DIRECTORY,
)
from specsafe.hugging_face_space_publication_candidate import (
    HuggingFaceSpacePublicationCandidateError,
    build_candidate_files,
    build_candidate_manifest,
    check_committed_candidate,
    write_candidate,
)
from specsafe.hugging_face_space_publication_candidate.builder import (
    CANDIDATE_ROOT_RELATIVE_PATH,
    CANONICAL_EVIDENCE_RELATIVE_PATH,
    EXPECTED_EVIDENCE_SHA256,
    MANIFEST_RELATIVE_PATH,
    SOURCE_APP_RELATIVE_PATH,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_committed_publication_candidate_is_canonical() -> None:
    check_committed_candidate(PROJECT_ROOT)
    check_committed_space_evidence_index(PROJECT_ROOT)


def test_candidate_output_is_separate_from_frozen_evidence() -> None:
    evidence_root = Path(OUTPUT_RELATIVE_DIRECTORY)

    assert not CANDIDATE_ROOT_RELATIVE_PATH.is_relative_to(evidence_root)
    assert not MANIFEST_RELATIVE_PATH.is_relative_to(evidence_root)


def test_candidate_uses_static_space_metadata_and_frozen_evidence() -> None:
    files = build_candidate_files(PROJECT_ROOT)
    manifest = build_candidate_manifest(PROJECT_ROOT)

    readme = files["README.md"].decode()
    assert "sdk: static" in readme
    assert "app_build_command: npm run build" in readme
    assert "app_file: dist/index.html" in readme
    assert manifest.evidence_index_sha256 == EXPECTED_EVIDENCE_SHA256
    assert manifest.actual_space_publication is False
    assert manifest.remote_mutation is False
    assert manifest.live_inference is False
    assert manifest.user_input_collection is False


def test_candidate_package_is_standalone_and_fail_closed() -> None:
    files = build_candidate_files(PROJECT_ROOT)
    package = json.loads(files["package.json"])

    assert "evidence:sync" not in package["scripts"]
    assert package["scripts"]["evidence:check"] == ("node ./scripts/verify-evidence.mjs")
    assert package["scripts"]["build"].startswith("npm run evidence:check")
    assert b"applied-caas-gateway" not in files["package-lock.json"]
    assert not files["package-lock.json"].startswith(b"\xef\xbb\xbf")
    assert files[".npmrc"].startswith(b"registry=https://registry.npmjs.org/\n")


def test_candidate_normalizes_utf8_bom_in_source_lockfile(
    tmp_path: Path,
) -> None:
    project = _copy_candidate_inputs(tmp_path)
    lockfile = project / SOURCE_APP_RELATIVE_PATH / "package-lock.json"
    payload = lockfile.read_bytes().removeprefix(b"\xef\xbb\xbf")
    lockfile.write_bytes(b"\xef\xbb\xbf" + payload)

    files = build_candidate_files(project)

    assert not files["package-lock.json"].startswith(b"\xef\xbb\xbf")
    assert isinstance(json.loads(files["package-lock.json"]), dict)


def test_candidate_rejects_evidence_drift(tmp_path: Path) -> None:
    project = _copy_candidate_inputs(tmp_path)
    evidence_path = project / CANONICAL_EVIDENCE_RELATIVE_PATH
    evidence_path.write_bytes(evidence_path.read_bytes() + b"drift")

    with pytest.raises(
        HuggingFaceSpacePublicationCandidateError,
        match="byte-count mismatch",
    ):
        build_candidate_files(project)


def test_candidate_rejects_internal_registry_lockfile(tmp_path: Path) -> None:
    project = _copy_candidate_inputs(tmp_path)
    lockfile = project / SOURCE_APP_RELATIVE_PATH / "package-lock.json"
    lockfile.write_text(
        lockfile.read_text(encoding="utf-8") + "\n// applied-caas-gateway\n",
        encoding="utf-8",
    )

    with pytest.raises(
        HuggingFaceSpacePublicationCandidateError,
        match="forbidden registry marker",
    ):
        build_candidate_files(project)


def test_committed_candidate_rejects_unexpected_file(tmp_path: Path) -> None:
    project = _copy_candidate_inputs(tmp_path)
    write_candidate(project)
    unexpected = project / CANDIDATE_ROOT_RELATIVE_PATH / "unexpected.txt"
    unexpected.write_text("unexpected\n", encoding="utf-8")

    with pytest.raises(
        HuggingFaceSpacePublicationCandidateError,
        match="allowlist mismatch",
    ):
        check_committed_candidate(project)


def test_committed_candidate_rejects_runtime_artifacts(tmp_path: Path) -> None:
    project = _copy_candidate_inputs(tmp_path)
    write_candidate(project)
    candidate_root = project / CANDIDATE_ROOT_RELATIVE_PATH
    (candidate_root / "dist").mkdir()
    (candidate_root / "dist/index.html").write_text("generated\n", encoding="utf-8")
    (candidate_root / "node_modules/example").mkdir(parents=True)
    (candidate_root / "node_modules/example/package.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        HuggingFaceSpacePublicationCandidateError,
        match="disposable copy",
    ):
        check_committed_candidate(project)


def test_write_candidate_rotates_contaminated_tree_outside_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _copy_candidate_inputs(tmp_path)
    write_candidate(project)
    candidate_root = project / CANDIDATE_ROOT_RELATIVE_PATH
    runtime_file = candidate_root / "node_modules" / "example" / "nested" / "package.json"
    runtime_file.parent.mkdir(parents=True)
    runtime_file.write_text("{}\n", encoding="utf-8")

    original_rmtree = publication_builder.shutil.rmtree
    retained_trash_paths: list[Path] = []

    def retain_external_trash(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        resolved = Path(path)
        if publication_builder.TRASH_DIRECTORY_NAME in resolved.parts:
            retained_trash_paths.append(resolved)
            return
        original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(
        publication_builder.shutil,
        "rmtree",
        retain_external_trash,
    )

    write_candidate(project)
    check_committed_candidate(project)

    assert retained_trash_paths
    assert all(not path.is_relative_to(project) for path in retained_trash_paths)
    assert not (candidate_root / "node_modules").exists()
    assert not any(
        path.name.startswith(publication_builder.STAGING_PREFIX)
        for path in candidate_root.parent.iterdir()
    )


def test_manifest_is_strictly_retained(tmp_path: Path) -> None:
    project = _copy_candidate_inputs(tmp_path)
    manifest = write_candidate(project)
    committed = json.loads((project / MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8"))

    assert committed["candidate_tree_sha256"] == (manifest.candidate_tree_sha256)
    assert committed["exact_candidate_file_count"] == len(build_candidate_files(project))


def _copy_candidate_inputs(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()

    shutil.copytree(
        PROJECT_ROOT / SOURCE_APP_RELATIVE_PATH,
        project / SOURCE_APP_RELATIVE_PATH,
        ignore=shutil.ignore_patterns(
            "node_modules",
            "dist",
            "playwright-report",
            "test-results",
        ),
    )

    canonical_target = project / CANONICAL_EVIDENCE_RELATIVE_PATH
    canonical_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        PROJECT_ROOT / CANONICAL_EVIDENCE_RELATIVE_PATH,
        canonical_target,
    )
    return project
