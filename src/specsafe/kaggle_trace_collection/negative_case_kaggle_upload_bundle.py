"""Build a private Kaggle input bundle for negative-case expansion.

This module is intentionally local-only. It prepares the files needed for a
private Kaggle dataset upload without running model inference, fitting
calibration, promoting thresholds, or creating public artifacts.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COLLECTION_ID = "v5-qwen-negative-case-expansion-v1"
ATTEMPT_ID = "attempt-001-t4"
BUNDLE_VERSION = "kaggle_private_input_bundle_v1"
ZIP_FILENAME = "specsafe_v5_qwen_negative_case_expansion_v1_private_input.zip"
EXTERNAL_MANIFEST_FILENAME = "kaggle_input_bundle_manifest.json"
INNER_MANIFEST_FILENAME = "UPLOAD_BUNDLE_INPUT_MANIFEST.json"
RUN_SOURCE_COMMIT_FILENAME = "RUN_SOURCE_COMMIT.txt"
PLANNED_PROMPT_COUNT = 16
CANDIDATE_POSITIONS_PER_PROMPT = 4
PLANNED_RUNTIME_RECORDS = 64
V2_OBSERVED_NEGATIVE_COUNT = 23
MINIMUM_NEGATIVES_FOR_CALIBRATION_FIT = 30
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

REQUIRED_INPUT_PATHS = (
    "data/fixtures/kaggle_negative_case_expansion_v1/prompt_corpus.json",
    "data/fixtures/kaggle_negative_case_expansion_v1/manifest.json",
    "data/fixtures/kaggle_negative_case_expansion_v1/authoring_ledger.md",
    (
        "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
        "pre-collection/pre_collection_manifest.json"
    ),
    (
        "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
        "readiness/collection_readiness_bundle.json"
    ),
    "docs/experiments/v5-kaggle-negative-case-expansion-precollection.md",
    "notebooks/kaggle/specsafe_v5_qwen_negative_case_expansion_v1_README.md",
)


@dataclass(frozen=True)
class FileEntry:
    """A locked file included in the private Kaggle input bundle."""

    path: str
    sha256: str
    byte_count: int


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_read_bytes(path))


def _json_bytes(payload: dict[str, Any]) -> bytes:
    text = json.dumps(payload, indent=2, sort_keys=True)
    return f"{text}\n".encode()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(payload))


def _resolve_source_commit(repo_root: Path, source_commit: str | None) -> str:
    if source_commit:
        return source_commit.strip()

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _build_file_entries(repo_root: Path) -> list[FileEntry]:
    entries: list[FileEntry] = []
    for relative_path in REQUIRED_INPUT_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"Required Kaggle input file is missing: {relative_path}")
        payload = _read_bytes(path)
        entries.append(
            FileEntry(
                path=relative_path,
                sha256=_sha256_bytes(payload),
                byte_count=len(payload),
            )
        )
    return entries


def _non_authorization_statuses() -> dict[str, str]:
    return {
        "model_execution_status": "not_started_by_upload_bundle",
        "third_archive_collection_status": "not_started",
        "calibration_fit_status": "not_authorized",
        "threshold_promotion_status": "not_authorized",
        "scheduler_promotion_status": "not_authorized",
        "public_release_status": "not_authorized",
        "production_claim_status": "not_authorized",
    }


def _inner_manifest(source_commit: str, file_entries: list[FileEntry]) -> dict[str, Any]:
    return {
        "artifact_role": "private_kaggle_input_bundle",
        "bundle_version": BUNDLE_VERSION,
        "collection_id": COLLECTION_ID,
        "attempt_id": ATTEMPT_ID,
        "source_commit": source_commit,
        "planned_prompt_count": PLANNED_PROMPT_COUNT,
        "candidate_positions_per_prompt": CANDIDATE_POSITIONS_PER_PROMPT,
        "planned_runtime_records": PLANNED_RUNTIME_RECORDS,
        "prior_diagnostic_boundary": {
            "v2_observed_negative_count": V2_OBSERVED_NEGATIVE_COUNT,
            "minimum_negatives_for_calibration_fit": MINIMUM_NEGATIVES_FOR_CALIBRATION_FIT,
            "minimum_additional_negatives_needed": (
                MINIMUM_NEGATIVES_FOR_CALIBRATION_FIT - V2_OBSERVED_NEGATIVE_COUNT
            ),
            "calibration_fit_authorized": False,
        },
        "included_files": [entry.__dict__ for entry in file_entries],
        "non_authorization_statuses": _non_authorization_statuses(),
        "privacy_boundary": {
            "public_safe_prompts_only": True,
            "contains_user_pii": False,
            "contains_client_data": False,
            "contains_secrets": False,
        },
    }


def _write_zip_entry(archive: zipfile.ZipFile, path: str, payload: bytes) -> None:
    if "\\" in path:
        raise ValueError(f"ZIP path must be POSIX-style, got: {path}")
    zip_info = zipfile.ZipInfo(filename=path, date_time=FIXED_ZIP_TIMESTAMP)
    zip_info.compress_type = zipfile.ZIP_DEFLATED
    zip_info.external_attr = 0o644 << 16
    archive.writestr(zip_info, payload)


def build_private_kaggle_input_bundle(
    repo_root: Path,
    output_dir: Path | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic private Kaggle input ZIP and manifest."""

    repo_root = repo_root.resolve()
    output_dir = (
        output_dir
        or repo_root / "evidence" / "kaggle-trace-collection" / COLLECTION_ID / "kaggle-input"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_commit = _resolve_source_commit(repo_root, source_commit)
    file_entries = _build_file_entries(repo_root)
    inner_manifest = _inner_manifest(resolved_commit, file_entries)
    inner_manifest_payload = _json_bytes(inner_manifest)

    zip_path = output_dir / ZIP_FILENAME
    with zipfile.ZipFile(zip_path, mode="w") as archive:
        _write_zip_entry(
            archive,
            RUN_SOURCE_COMMIT_FILENAME,
            f"{resolved_commit}\n".encode(),
        )
        _write_zip_entry(archive, INNER_MANIFEST_FILENAME, inner_manifest_payload)
        for entry in sorted(file_entries, key=lambda item: item.path):
            _write_zip_entry(archive, entry.path, _read_bytes(repo_root / entry.path))

    zip_payload = _read_bytes(zip_path)
    external_manifest = {
        **inner_manifest,
        "zip_filename": ZIP_FILENAME,
        "zip_sha256": _sha256_bytes(zip_payload),
        "zip_byte_count": len(zip_payload),
        "inner_manifest_filename": INNER_MANIFEST_FILENAME,
        "inner_manifest_sha256": _sha256_bytes(inner_manifest_payload),
        "run_source_commit_filename": RUN_SOURCE_COMMIT_FILENAME,
        "kaggle_dataset_visibility": "private_required",
        "kaggle_dataset_title_recommendation": "specsafe-qwen-negcase-v1-t4-input",
    }
    manifest_path = output_dir / EXTERNAL_MANIFEST_FILENAME
    _write_json(manifest_path, external_manifest)
    return external_manifest


def load_external_manifest(path: Path) -> dict[str, Any]:
    """Load the generated private Kaggle input manifest."""

    return json.loads(path.read_text(encoding="utf-8"))
