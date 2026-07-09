from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from specsafe.kaggle_trace_collection.negative_case_kaggle_upload_bundle import (
    EXTERNAL_MANIFEST_FILENAME,
    INNER_MANIFEST_FILENAME,
    PLANNED_RUNTIME_RECORDS,
    REQUIRED_INPUT_PATHS,
    RUN_SOURCE_COMMIT_FILENAME,
    ZIP_FILENAME,
    build_private_kaggle_input_bundle,
)

SOURCE_COMMIT = "0123456789abcdef0123456789abcdef01234567"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _fake_json(name: str) -> str:
    return json.dumps({"fixture": name}, indent=2, sort_keys=True) + "\n"


def _build_fake_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    for relative_path in REQUIRED_INPUT_PATHS:
        path = repo_root / relative_path
        if path.suffix == ".json":
            _write(path, _fake_json(relative_path))
        else:
            _write(path, f"# {relative_path}\n\nSynthetic test fixture.\n")
    return repo_root


def test_builds_private_kaggle_input_zip_with_posix_paths(tmp_path: Path) -> None:
    repo_root = _build_fake_repo(tmp_path)
    manifest = build_private_kaggle_input_bundle(
        repo_root=repo_root,
        source_commit=SOURCE_COMMIT,
    )

    zip_path = (
        repo_root
        / "evidence"
        / "kaggle-trace-collection"
        / "v5-qwen-negative-case-expansion-v1"
        / "kaggle-input"
        / ZIP_FILENAME
    )
    assert zip_path.exists()
    assert manifest["zip_filename"] == ZIP_FILENAME
    assert manifest["planned_runtime_records"] == PLANNED_RUNTIME_RECORDS

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()

    assert RUN_SOURCE_COMMIT_FILENAME in names
    assert INNER_MANIFEST_FILENAME in names
    assert set(REQUIRED_INPUT_PATHS).issubset(names)
    assert all("\\" not in name for name in names)


def test_external_manifest_matches_generated_zip(tmp_path: Path) -> None:
    repo_root = _build_fake_repo(tmp_path)
    manifest = build_private_kaggle_input_bundle(
        repo_root=repo_root,
        source_commit=SOURCE_COMMIT,
    )

    manifest_path = (
        repo_root
        / "evidence"
        / "kaggle-trace-collection"
        / "v5-qwen-negative-case-expansion-v1"
        / "kaggle-input"
        / EXTERNAL_MANIFEST_FILENAME
    )
    retained_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert retained_manifest == manifest
    assert retained_manifest["source_commit"] == SOURCE_COMMIT
    assert retained_manifest["kaggle_dataset_visibility"] == "private_required"
    assert len(retained_manifest["zip_sha256"]) == 64
    assert retained_manifest["zip_byte_count"] > 0


def test_inner_manifest_preserves_non_authorization_boundary(tmp_path: Path) -> None:
    repo_root = _build_fake_repo(tmp_path)
    build_private_kaggle_input_bundle(repo_root=repo_root, source_commit=SOURCE_COMMIT)
    zip_path = (
        repo_root
        / "evidence"
        / "kaggle-trace-collection"
        / "v5-qwen-negative-case-expansion-v1"
        / "kaggle-input"
        / ZIP_FILENAME
    )

    with zipfile.ZipFile(zip_path) as archive:
        inner_manifest = json.loads(archive.read(INNER_MANIFEST_FILENAME))

    statuses = inner_manifest["non_authorization_statuses"]
    assert statuses["model_execution_status"] == "not_started_by_upload_bundle"
    assert statuses["third_archive_collection_status"] == "not_started"
    assert statuses["calibration_fit_status"] == "not_authorized"
    assert statuses["threshold_promotion_status"] == "not_authorized"
    assert statuses["scheduler_promotion_status"] == "not_authorized"
    assert statuses["public_release_status"] == "not_authorized"
    assert statuses["production_claim_status"] == "not_authorized"


def test_private_input_bundle_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    repo_root = _build_fake_repo(tmp_path)
    first = build_private_kaggle_input_bundle(repo_root=repo_root, source_commit=SOURCE_COMMIT)
    second = build_private_kaggle_input_bundle(repo_root=repo_root, source_commit=SOURCE_COMMIT)

    assert second["zip_sha256"] == first["zip_sha256"]
    assert second["inner_manifest_sha256"] == first["inner_manifest_sha256"]


def test_missing_required_input_file_fails_closed(tmp_path: Path) -> None:
    repo_root = _build_fake_repo(tmp_path)
    missing_path = repo_root / REQUIRED_INPUT_PATHS[0]
    missing_path.unlink()

    with pytest.raises(FileNotFoundError, match="Required Kaggle input file is missing"):
        build_private_kaggle_input_bundle(repo_root=repo_root, source_commit=SOURCE_COMMIT)
