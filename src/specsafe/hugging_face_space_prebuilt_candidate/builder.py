from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from specsafe.hugging_face_space_publication_candidate import (
    HuggingFaceSpacePublicationCandidateManifest,
)
from specsafe.hugging_face_space_publication_candidate import (
    check_committed_candidate as check_source_candidate,
)
from specsafe.hugging_face_space_publication_candidate.models import CandidateFileDigest

from .models import (
    HuggingFaceSpacePrebuiltCandidateManifest,
    PrebuiltSpaceMetadata,
)

SOURCE_CANDIDATE_ROOT_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space"
)
SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/"
    "publication_candidate_manifest.json"
)
CANDIDATE_ROOT_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/candidate/space"
)
MANIFEST_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/"
    "prebuilt_candidate_manifest.json"
)

EXPECTED_SOURCE_TREE_SHA256: Final = (
    "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"
)
EXPECTED_SOURCE_FILE_COUNT: Final = 35
EXPECTED_EVIDENCE_SHA256: Final = "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
EXPECTED_EVIDENCE_BYTE_COUNT: Final = 9206

BUILD_COMMANDS: Final = (
    ("npm", "ci"),
    ("npm", "run", "evidence:check"),
    ("npm", "run", "lint"),
    ("npm", "run", "test"),
    ("npm", "run", "build"),
)
COMMAND_TIMEOUT_SECONDS: Final = {
    ("npm", "ci"): 900,
    ("npm", "run", "evidence:check"): 180,
    ("npm", "run", "lint"): 300,
    ("npm", "run", "test"): 300,
    ("npm", "run", "build"): 300,
}
FORBIDDEN_CANDIDATE_PARTS: Final = frozenset(
    {
        "node_modules",
        "src",
        "scripts",
        "tests",
        "test-results",
        "playwright-report",
    }
)
FORBIDDEN_CANDIDATE_FILENAMES: Final = frozenset(
    {
        ".npmrc",
        "package.json",
        "package-lock.json",
        "vite.config.ts",
        "tsconfig.json",
        "tsconfig.app.json",
        "tsconfig.node.json",
    }
)
FORBIDDEN_SUFFIXES: Final = frozenset({".map"})
STAGING_PREFIX: Final = ".space-prebuilt-candidate-staging-"
TRASH_DIRECTORY_NAME: Final = ".specsafe-prebuilt-candidate-trash"
TRASH_PREFIX: Final = "specsafe-reliability-lab-"

CommandRunner = Callable[[Path, tuple[str, ...], int, Mapping[str, str]], None]
SourceValidator = Callable[[Path], None]


class HuggingFaceSpacePrebuiltCandidateError(ValueError):
    """Raised when the prebuilt Space candidate cannot be created safely."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_required(path: Path) -> bytes:
    if not path.is_file():
        raise HuggingFaceSpacePrebuiltCandidateError(f"Required file is missing: {path}")
    return path.read_bytes()


def _validate_output_namespace() -> None:
    source_root = SOURCE_CANDIDATE_ROOT_RELATIVE_PATH
    output_paths = (CANDIDATE_ROOT_RELATIVE_PATH, MANIFEST_RELATIVE_PATH)
    if any(path.is_relative_to(source_root) for path in output_paths):
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt candidate output must remain outside the frozen source candidate."
        )


def _load_source_manifest(
    project_root: Path,
) -> tuple[bytes, HuggingFaceSpacePublicationCandidateManifest]:
    path = project_root / SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH
    payload = _read_required(path)
    try:
        manifest = HuggingFaceSpacePublicationCandidateManifest.model_validate_json(payload)
    except ValidationError as error:
        raise HuggingFaceSpacePrebuiltCandidateError(
            f"Source candidate manifest failed strict validation: {error}"
        ) from error

    conditions = (
        manifest.candidate_tree_sha256 == EXPECTED_SOURCE_TREE_SHA256,
        manifest.exact_candidate_file_count == EXPECTED_SOURCE_FILE_COUNT,
        len(manifest.files) == EXPECTED_SOURCE_FILE_COUNT,
        manifest.evidence_index_sha256 == EXPECTED_EVIDENCE_SHA256,
        manifest.evidence_index_byte_count == EXPECTED_EVIDENCE_BYTE_COUNT,
        manifest.actual_space_publication is False,
        manifest.remote_mutation is False,
        manifest.live_inference is False,
        manifest.user_input_collection is False,
    )
    if not all(conditions):
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Source publication candidate is outside the frozen prebuilt-build boundary."
        )
    return payload, manifest


def _build_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in (
        "HF_TOKEN",
        "HUGGING_FACE_HUB_TOKEN",
        "HUGGINGFACE_TOKEN",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "CI": "true",
            "NPM_CONFIG_UPDATE_NOTIFIER": "false",
        }
    )
    return environment


def _resolve_command(
    command: tuple[str, ...],
    *,
    which: Callable[[str], str | None] = shutil.which,
    platform_name: str = os.name,
) -> tuple[str, ...]:
    if not command:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt candidate command must not be empty."
        )

    executable, *arguments = command
    candidates = (f"{executable}.cmd", executable) if platform_name == "nt" else (executable,)
    for candidate in candidates:
        resolved = which(candidate)
        if resolved is not None:
            return (resolved, *arguments)

    raise HuggingFaceSpacePrebuiltCandidateError(
        "Required prebuilt-candidate executable is unavailable: "
        f"{executable}. Install Node.js/npm and ensure it is on PATH."
    )


def _run_command(
    working_directory: Path,
    command: tuple[str, ...],
    timeout_seconds: int,
    environment: Mapping[str, str],
) -> None:
    resolved_command = _resolve_command(command)
    try:
        result = subprocess.run(
            resolved_command,
            cwd=working_directory,
            env=dict(environment),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise HuggingFaceSpacePrebuiltCandidateError(
            f"Prebuilt candidate command could not run: {' '.join(command)}"
        ) from error

    if result.returncode == 0:
        return

    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    output_tail = output[-4000:] if output else "<no command output>"
    raise HuggingFaceSpacePrebuiltCandidateError(
        "Prebuilt candidate command failed: "
        f"command={' '.join(command)!r}, exit_code={result.returncode}, "
        f"output_tail={output_tail!r}"
    )


def _space_readme() -> bytes:
    return b"""---
title: SpecSafe - When Should AI Spend More Compute?
emoji: \xf0\x9f\x9b\xa1\xef\xb8\x8f
colorFrom: yellow
colorTo: red
sdk: static
app_file: index.html
fullWidth: true
header: mini
short_description: AI reliability case study on adaptive verification.
datasets:
  - KaboKableMolefe/specsafe-bounded-negative-evidence-v1
tags:
  - ai-evaluation
  - reliability
  - verification
  - calibration
pinned: false
---

# SpecSafe: When Should AI Spend More Compute?

SpecSafe is a read-only AI reliability case study.

It tests whether a confidence-calibrated, capacity-aware verification policy can
spend limited compute more intelligently than fixed rules without using
forbidden future information.

## Result

The adaptive policy helped in some governed conditions, was neutral in others,
and lost once. The independent confidence candidate improved probability
calibration but breached the ranking-safety limit, so SpecSafe blocked
automated activation.

```text
decision=KEEP_DIAGNOSTIC_ONLY
failure_label=ranking_safety_regression
live_inference=false
user_input_collection=false
provider_side_build_required=false
```

## Evidence boundary

This Space serves locally built, hash-bound static assets. It reads one frozen
evidence index and does not run a model, accept user input, tune thresholds,
mutate evidence, or establish production throughput, latency, cost, or serving
performance.
"""


def _copy_source_candidate(source_root: Path, build_root: Path) -> None:
    if not source_root.is_dir():
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Frozen source publication candidate directory is missing."
        )
    shutil.copytree(source_root, build_root, dirs_exist_ok=False)


def _run_build(
    build_root: Path,
    *,
    command_runner: CommandRunner,
) -> None:
    environment = _build_environment()
    for command in BUILD_COMMANDS:
        timeout_seconds = COMMAND_TIMEOUT_SECONDS[command]
        command_runner(build_root, command, timeout_seconds, environment)


def _collect_dist_files(dist_root: Path) -> dict[str, bytes]:
    if not dist_root.is_dir():
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Validated frontend build did not create a dist directory."
        )

    files: dict[str, bytes] = {}
    for path in sorted(dist_root.rglob("*")):
        relative_path = path.relative_to(dist_root).as_posix()
        if path.is_symlink():
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Prebuilt output contains linked content: {relative_path}"
            )
        if path.is_dir():
            continue
        if not path.is_file():
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Prebuilt output contains unsupported content: {relative_path}"
            )
        files[relative_path] = path.read_bytes()

    if not files:
        raise HuggingFaceSpacePrebuiltCandidateError("Prebuilt output is empty.")
    return files


def _validate_candidate_paths(files: Mapping[str, bytes]) -> None:
    for relative_path in files:
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Prebuilt output path is unsafe: {relative_path}"
            )
        if any(part in FORBIDDEN_CANDIDATE_PARTS for part in path.parts):
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Prebuilt output contains a forbidden runtime path: {relative_path}"
            )
        if path.name in FORBIDDEN_CANDIDATE_FILENAMES:
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Prebuilt output contains a source-only file: {relative_path}"
            )
        if path.suffix in FORBIDDEN_SUFFIXES:
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Prebuilt output contains a forbidden source map: {relative_path}"
            )


def _validate_evidence(files: Mapping[str, bytes]) -> None:
    evidence_path = "evidence/evidence_index.json"
    payload = files.get(evidence_path)
    if payload is None:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt output lost the frozen evidence index."
        )
    if len(payload) != EXPECTED_EVIDENCE_BYTE_COUNT:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt evidence index byte count does not match the frozen evidence."
        )
    if _sha256(payload) != EXPECTED_EVIDENCE_SHA256:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt evidence index SHA-256 does not match the frozen evidence."
        )


def _validate_html(files: Mapping[str, bytes]) -> None:
    payload = files.get("index.html")
    if payload is None:
        raise HuggingFaceSpacePrebuiltCandidateError("Prebuilt output does not contain index.html.")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt index.html is not valid UTF-8."
        ) from error

    required_markers = ("SpecSafe", 'id="root"')
    if any(marker not in text for marker in required_markers):
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt index.html lost required application markers."
        )

    referenced_assets = tuple(
        sorted(
            {
                match.group(1).lstrip("./")
                for match in re.finditer(
                    r"""(?:src|href)=["']([^"']+)["']""",
                    text,
                )
                if not match.group(1).startswith(("http://", "https://", "data:", "#"))
            }
        )
    )
    missing_assets = tuple(
        path
        for path in referenced_assets
        if path not in {"", "/"} and path.lstrip("/") not in files
    )
    if missing_assets:
        raise HuggingFaceSpacePrebuiltCandidateError(
            f"Prebuilt index.html references missing assets: {missing_assets}"
        )


def _validate_readme(payload: bytes) -> None:
    text = payload.decode("utf-8")
    required_markers = (
        "sdk: static",
        "app_file: index.html",
        "provider_side_build_required=false",
        "decision=KEEP_DIAGNOSTIC_ONLY",
        "failure_label=ranking_safety_regression",
    )
    if any(marker not in text for marker in required_markers):
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt Space README lost a required publication boundary."
        )
    if "app_build_command:" in text:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt Space README must not request a provider-side build."
        )


def build_prebuilt_candidate_files(
    project_root: Path,
    *,
    command_runner: CommandRunner = _run_command,
    source_validator: SourceValidator = check_source_candidate,
) -> tuple[dict[str, bytes], bytes, HuggingFaceSpacePublicationCandidateManifest]:
    _validate_output_namespace()
    source_validator(project_root)
    source_manifest_bytes, source_manifest = _load_source_manifest(project_root)
    source_root = project_root / SOURCE_CANDIDATE_ROOT_RELATIVE_PATH

    with tempfile.TemporaryDirectory(prefix="specsafe-space-prebuilt-build-") as temporary:
        build_root = Path(temporary) / "source"
        _copy_source_candidate(source_root, build_root)
        _run_build(build_root, command_runner=command_runner)
        files = _collect_dist_files(build_root / "dist")

    readme = _space_readme()
    _validate_readme(readme)
    files["README.md"] = readme
    files = dict(sorted(files.items()))

    _validate_candidate_paths(files)
    _validate_evidence(files)
    _validate_html(files)

    if "public/evidence/evidence_index.json" in files:
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Prebuilt candidate must expose evidence at the built runtime path only."
        )
    return files, source_manifest_bytes, source_manifest


def _candidate_tree_sha256(files: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative_path, payload in sorted(files.items()):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(payload).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _build_manifest(
    files: Mapping[str, bytes],
    source_manifest_bytes: bytes,
) -> HuggingFaceSpacePrebuiltCandidateManifest:
    file_digests = tuple(
        CandidateFileDigest(
            relative_path=relative_path,
            byte_count=len(payload),
            sha256=_sha256(payload),
        )
        for relative_path, payload in sorted(files.items())
    )
    return HuggingFaceSpacePrebuiltCandidateManifest(
        schema_version="specsafe_hugging_face_space_prebuilt_candidate_manifest_v1",
        space_repository_name="specsafe-reliability-lab",
        source_candidate_manifest_relative_path=(
            "release/hugging-face-space-publication/specsafe-reliability-lab/"
            "publication_candidate_manifest.json"
        ),
        source_candidate_manifest_sha256=_sha256(source_manifest_bytes),
        source_candidate_tree_sha256=EXPECTED_SOURCE_TREE_SHA256,
        source_candidate_file_count=EXPECTED_SOURCE_FILE_COUNT,
        candidate_root_relative_path=(
            "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/"
            "candidate/space"
        ),
        metadata=PrebuiltSpaceMetadata(
            title="SpecSafe - When Should AI Spend More Compute?",
            emoji="🛡️",
            color_from="yellow",
            color_to="red",
            sdk="static",
            app_file="index.html",
            full_width=True,
            header="mini",
            short_description="AI reliability case study on adaptive verification.",
            datasets=("KaboKableMolefe/specsafe-bounded-negative-evidence-v1",),
            tags=(
                "ai-evaluation",
                "reliability",
                "verification",
                "calibration",
            ),
            pinned=False,
        ),
        evidence_index_relative_path="evidence/evidence_index.json",
        evidence_index_byte_count=EXPECTED_EVIDENCE_BYTE_COUNT,
        evidence_index_sha256=EXPECTED_EVIDENCE_SHA256,
        build_strategy="local_validated_prebuilt_static_assets",
        build_commands=tuple(" ".join(command) for command in BUILD_COMMANDS),
        exact_candidate_file_count=len(files),
        candidate_tree_sha256=_candidate_tree_sha256(files),
        files=file_digests,
        actual_space_publication=False,
        remote_mutation=False,
        provider_side_build_required=False,
        live_inference=False,
        user_input_collection=False,
        next_authorized_step="rebind_controlled_publication_executor_to_prebuilt_candidate",
    )


def build_prebuilt_candidate_payloads(
    project_root: Path,
    *,
    command_runner: CommandRunner = _run_command,
    source_validator: SourceValidator = check_source_candidate,
) -> tuple[dict[str, bytes], bytes, HuggingFaceSpacePrebuiltCandidateManifest]:
    files, source_manifest_bytes, _ = build_prebuilt_candidate_files(
        project_root,
        command_runner=command_runner,
        source_validator=source_validator,
    )
    manifest = _build_manifest(files, source_manifest_bytes)
    manifest_bytes = _canonical_json_bytes(manifest.model_dump(mode="json"))
    return files, manifest_bytes, manifest


def _trash_parent(project_root: Path) -> Path:
    return project_root.parent / TRASH_DIRECTORY_NAME


def _quarantine_existing_candidate(
    project_root: Path,
    candidate_root: Path,
) -> Path | None:
    if not candidate_root.exists():
        return None
    if candidate_root.is_symlink():
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Committed prebuilt candidate root must not be a symlink."
        )

    trash_parent = _trash_parent(project_root)
    trash_parent.mkdir(parents=True, exist_ok=True)
    trash_root = trash_parent / f"{TRASH_PREFIX}{uuid.uuid4().hex}"
    candidate_root.replace(trash_root)
    return trash_root


def _best_effort_remove_tree(path: Path | None) -> None:
    if path is None:
        return
    shutil.rmtree(path, ignore_errors=True)
    parent = path.parent
    try:
        if parent.name == TRASH_DIRECTORY_NAME and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        pass


def _restore_quarantined_candidate(
    candidate_root: Path,
    trash_root: Path | None,
) -> None:
    if trash_root is None or candidate_root.exists() or not trash_root.exists():
        return
    try:
        trash_root.replace(candidate_root)
    except OSError:
        pass


def _write_candidate_tree(root: Path, files: Mapping[str, bytes]) -> None:
    for relative_path, payload in files.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def write_prebuilt_candidate(
    project_root: Path,
    *,
    command_runner: CommandRunner = _run_command,
    source_validator: SourceValidator = check_source_candidate,
) -> HuggingFaceSpacePrebuiltCandidateManifest:
    files, manifest_bytes, manifest = build_prebuilt_candidate_payloads(
        project_root,
        command_runner=command_runner,
        source_validator=source_validator,
    )
    candidate_root = project_root / CANDIDATE_ROOT_RELATIVE_PATH
    candidate_root.parent.mkdir(parents=True, exist_ok=True)

    staging_root = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=candidate_root.parent))
    trash_root: Path | None = None
    try:
        _write_candidate_tree(staging_root, files)
        trash_root = _quarantine_existing_candidate(project_root, candidate_root)
        staging_root.replace(candidate_root)
    except Exception:
        _restore_quarantined_candidate(candidate_root, trash_root)
        _best_effort_remove_tree(staging_root)
        raise
    _best_effort_remove_tree(trash_root)

    manifest_path = project_root / MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_bytes)
    return manifest


def check_committed_prebuilt_candidate(
    project_root: Path,
    *,
    command_runner: CommandRunner = _run_command,
    source_validator: SourceValidator = check_source_candidate,
) -> HuggingFaceSpacePrebuiltCandidateManifest:
    files, manifest_bytes, manifest = build_prebuilt_candidate_payloads(
        project_root,
        command_runner=command_runner,
        source_validator=source_validator,
    )
    candidate_root = project_root / CANDIDATE_ROOT_RELATIVE_PATH
    if not candidate_root.is_dir() or candidate_root.is_symlink():
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Committed prebuilt candidate directory is missing or linked."
        )

    actual_files = tuple(
        sorted(
            path.relative_to(candidate_root).as_posix()
            for path in candidate_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
    )
    expected_files = tuple(files)
    if actual_files != expected_files:
        missing = sorted(set(expected_files) - set(actual_files))
        unexpected = sorted(set(actual_files) - set(expected_files))
        raise HuggingFaceSpacePrebuiltCandidateError(
            f"Committed prebuilt candidate allowlist drifted: "
            f"missing={missing}, unexpected={unexpected}"
        )

    for relative_path, expected_payload in files.items():
        actual_payload = (candidate_root / relative_path).read_bytes()
        if actual_payload != expected_payload:
            raise HuggingFaceSpacePrebuiltCandidateError(
                f"Committed prebuilt candidate drift: {relative_path}"
            )

    manifest_path = project_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise HuggingFaceSpacePrebuiltCandidateError(
            "Committed prebuilt candidate manifest is missing."
        )
    if manifest_path.read_bytes() != manifest_bytes:
        raise HuggingFaceSpacePrebuiltCandidateError("Committed prebuilt candidate manifest drift.")
    return manifest
