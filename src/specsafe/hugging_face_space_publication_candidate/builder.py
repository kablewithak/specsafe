from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Final

from specsafe.hugging_face_space_publication_candidate.models import (
    CandidateFileDigest,
    HuggingFaceSpacePublicationCandidateManifest,
    SpaceMetadata,
)

SOURCE_APP_RELATIVE_PATH: Final = Path("apps/specsafe-reliability-lab")
CANONICAL_EVIDENCE_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space/specsafe-reliability-lab/evidence_index.json"
)
CANDIDATE_ROOT_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space"
)
MANIFEST_RELATIVE_PATH: Final = Path(
    "release/hugging-face-space-publication/specsafe-reliability-lab/"
    "publication_candidate_manifest.json"
)

EXPECTED_EVIDENCE_SHA256: Final = "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e"
EXPECTED_EVIDENCE_BYTE_COUNT: Final = 9206
SOURCE_COMMIT: Final = "2848e80"

SOURCE_COPY_FILES: Final = (
    ".gitignore",
    "eslint.config.js",
    "index.html",
    "package-lock.json",
    "playwright.config.ts",
    "postcss.config.js",
    "src/App.test.tsx",
    "src/App.tsx",
    "src/components/metric-card.tsx",
    "src/components/policy-case-matrix.test.tsx",
    "src/components/policy-case-matrix.tsx",
    "src/components/section-heading.tsx",
    "src/components/ui/badge.tsx",
    "src/components/ui/card.tsx",
    "src/components/ui/tabs.tsx",
    "src/components/ui/tooltip.tsx",
    "src/index.css",
    "src/lib/evidence.test.ts",
    "src/lib/evidence.ts",
    "src/lib/format.ts",
    "src/lib/utils.ts",
    "src/main.tsx",
    "src/test/setup.ts",
    "src/vite-env.d.ts",
    "tailwind.config.ts",
    "tests/smoke.spec.ts",
    "tsconfig.app.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "vite.config.ts",
)

GENERATED_FILES: Final = (
    ".npmrc",
    "README.md",
    "package.json",
    "public/evidence/evidence_index.json",
    "scripts/verify-evidence.mjs",
)

FORBIDDEN_PATH_PARTS: Final = (
    "node_modules",
    "dist",
    "playwright-report",
    "test-results",
)

FORBIDDEN_LOCKFILE_MARKERS: Final = (
    "applied-caas-gateway",
    "internal.api.openai.org",
)

STAGING_PREFIX: Final = ".space-candidate-staging-"
TRASH_DIRECTORY_NAME: Final = ".specsafe-publication-candidate-trash"
TRASH_PREFIX: Final = "specsafe-reliability-lab-"


class HuggingFaceSpacePublicationCandidateError(ValueError):
    """Raised when the standalone Space candidate cannot be built safely."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validate_output_namespace() -> None:
    frozen_evidence_root = CANONICAL_EVIDENCE_RELATIVE_PATH.parent
    candidate_paths = (
        CANDIDATE_ROOT_RELATIVE_PATH,
        MANIFEST_RELATIVE_PATH,
    )
    if any(path.is_relative_to(frozen_evidence_root) for path in candidate_paths):
        raise HuggingFaceSpacePublicationCandidateError(
            "Publication candidate output must be outside the frozen evidence directory."
        )


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _read_required(path: Path) -> bytes:
    if not path.is_file():
        raise HuggingFaceSpacePublicationCandidateError(
            f"Required candidate source file is missing: {path}"
        )
    return path.read_bytes()


def _validated_evidence_bytes(project_root: Path) -> bytes:
    canonical_path = project_root / CANONICAL_EVIDENCE_RELATIVE_PATH
    frontend_path = project_root / SOURCE_APP_RELATIVE_PATH / "public/evidence/evidence_index.json"
    canonical = _read_required(canonical_path)
    frontend = _read_required(frontend_path)

    if len(canonical) != EXPECTED_EVIDENCE_BYTE_COUNT:
        raise HuggingFaceSpacePublicationCandidateError("Canonical evidence byte-count mismatch.")
    if _sha256(canonical) != EXPECTED_EVIDENCE_SHA256:
        raise HuggingFaceSpacePublicationCandidateError("Canonical evidence SHA-256 mismatch.")
    if frontend != canonical:
        raise HuggingFaceSpacePublicationCandidateError(
            "Frontend evidence copy does not match the canonical frozen index."
        )
    return canonical


def _normalized_package_lock(payload: bytes) -> bytes:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HuggingFaceSpacePublicationCandidateError(
            "Package lock is not valid UTF-8."
        ) from error

    for marker in FORBIDDEN_LOCKFILE_MARKERS:
        if marker in text:
            raise HuggingFaceSpacePublicationCandidateError(
                f"Package lock contains forbidden registry marker: {marker}"
            )
    if "https://registry.npmjs.org/" not in text:
        raise HuggingFaceSpacePublicationCandidateError(
            "Package lock does not contain the public npm registry."
        )

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise HuggingFaceSpacePublicationCandidateError(
            "Package lock is not valid JSON."
        ) from error

    if not isinstance(value, dict):
        raise HuggingFaceSpacePublicationCandidateError("Package lock root must be a JSON object.")

    lockfile_version = value.get("lockfileVersion")
    if (
        isinstance(lockfile_version, bool)
        or not isinstance(lockfile_version, int)
        or lockfile_version < 1
    ):
        raise HuggingFaceSpacePublicationCandidateError(
            "Package lock must have lockfileVersion >= 1."
        )

    return text.encode("utf-8")


def _candidate_package_json(source_payload: bytes) -> bytes:
    try:
        value = json.loads(source_payload)
    except json.JSONDecodeError as error:
        raise HuggingFaceSpacePublicationCandidateError(
            "Source package.json is not valid JSON."
        ) from error

    scripts = value.get("scripts")
    if not isinstance(scripts, dict):
        raise HuggingFaceSpacePublicationCandidateError(
            "Source package.json has no scripts object."
        )

    value["scripts"] = {
        "dev": "npm run evidence:check && vite",
        "build": "npm run evidence:check && tsc -b && vite build",
        "preview": "vite preview",
        "lint": "eslint .",
        "test": "vitest run",
        "test:watch": "vitest",
        "test:e2e": "playwright test",
        "test:e2e:install": "playwright install chromium",
        "evidence:check": "node ./scripts/verify-evidence.mjs",
        "check": ("npm run evidence:check && npm run lint && npm run test && npm run build"),
    }
    return _canonical_json_bytes(value)


def _space_readme() -> bytes:
    return b"""---
title: SpecSafe - When Should AI Spend More Compute?
emoji: \xf0\x9f\x9b\xa1\xef\xb8\x8f
colorFrom: yellow
colorTo: red
sdk: static
app_build_command: npm run build
app_file: dist/index.html
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
```

## Evidence boundary

This Space reads one frozen, SHA-256-bound evidence index. It does not run a
model, accept user input, tune thresholds, mutate evidence, or establish
production throughput, latency, cost, or serving performance.
"""


def _npmrc() -> bytes:
    return b"""registry=https://registry.npmjs.org/
save-exact=true
fund=false
audit=true
"""


def _evidence_verifier() -> bytes:
    return f"""import {{ createHash }} from "node:crypto";
import {{ readFile }} from "node:fs/promises";

const evidencePath = new URL(
  "../public/evidence/evidence_index.json",
  import.meta.url,
);
const expectedByteCount = {EXPECTED_EVIDENCE_BYTE_COUNT};
const expectedSha256 = "{EXPECTED_EVIDENCE_SHA256}";

const payload = await readFile(evidencePath);
if (payload.byteLength !== expectedByteCount) {{
  throw new Error(
    `Evidence byte-count mismatch: ${{payload.byteLength}} !== ${{expectedByteCount}}`,
  );
}}

const actualSha256 = createHash("sha256").update(payload).digest("hex");
if (actualSha256 !== expectedSha256) {{
  throw new Error(
    `Evidence SHA-256 mismatch: ${{actualSha256}} !== ${{expectedSha256}}`,
  );
}}

const evidence = JSON.parse(payload.toString("utf8"));
if (
  evidence.read_only !== true ||
  evidence.live_inference !== false ||
  evidence.user_input_collection !== false
) {{
  throw new Error("Evidence authorization boundary changed.");
}}

console.log(`Evidence check passed: ${{actualSha256}}`);
""".encode()


def build_candidate_files(project_root: Path) -> dict[str, bytes]:
    _validate_output_namespace()
    source_root = project_root / SOURCE_APP_RELATIVE_PATH
    files: dict[str, bytes] = {}

    for relative_path in SOURCE_COPY_FILES:
        payload = _read_required(source_root / relative_path)
        if relative_path == "package-lock.json":
            payload = _normalized_package_lock(payload)
        files[relative_path] = payload

    source_package = _read_required(source_root / "package.json")
    files.update(
        {
            ".npmrc": _npmrc(),
            "README.md": _space_readme(),
            "package.json": _candidate_package_json(source_package),
            "public/evidence/evidence_index.json": _validated_evidence_bytes(project_root),
            "scripts/verify-evidence.mjs": _evidence_verifier(),
        }
    )

    expected_paths = set(SOURCE_COPY_FILES) | set(GENERATED_FILES)
    if set(files) != expected_paths:
        raise HuggingFaceSpacePublicationCandidateError(
            "Candidate payload does not match the exact file allowlist."
        )

    for path in files:
        parts = Path(path).parts
        if any(part in FORBIDDEN_PATH_PARTS for part in parts):
            raise HuggingFaceSpacePublicationCandidateError(f"Forbidden generated path: {path}")

    return dict(sorted(files.items()))


def _candidate_tree_sha256(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative_path, payload in sorted(files.items()):
        digest.update(relative_path.encode())
        digest.update(b"\0")
        digest.update(_sha256(payload).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def build_candidate_manifest(
    project_root: Path,
) -> HuggingFaceSpacePublicationCandidateManifest:
    files = build_candidate_files(project_root)
    file_digests = tuple(
        CandidateFileDigest(
            relative_path=relative_path,
            byte_count=len(payload),
            sha256=_sha256(payload),
        )
        for relative_path, payload in files.items()
    )
    return HuggingFaceSpacePublicationCandidateManifest(
        schema_version=("specsafe_hugging_face_space_publication_candidate_manifest_v1"),
        space_repository_name="specsafe-reliability-lab",
        source_app_relative_path="apps/specsafe-reliability-lab",
        candidate_root_relative_path=(
            "release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space"
        ),
        source_commit=SOURCE_COMMIT,
        metadata=SpaceMetadata(
            title="SpecSafe - When Should AI Spend More Compute?",
            emoji="\U0001f6e1\ufe0f",
            color_from="yellow",
            color_to="red",
            sdk="static",
            app_build_command="npm run build",
            app_file="dist/index.html",
            full_width=True,
            header="mini",
            short_description=("AI reliability case study on adaptive verification."),
            datasets=("KaboKableMolefe/specsafe-bounded-negative-evidence-v1",),
            tags=(
                "ai-evaluation",
                "reliability",
                "verification",
                "calibration",
            ),
            pinned=False,
        ),
        evidence_index_relative_path="public/evidence/evidence_index.json",
        evidence_index_byte_count=EXPECTED_EVIDENCE_BYTE_COUNT,
        evidence_index_sha256=EXPECTED_EVIDENCE_SHA256,
        exact_candidate_file_count=len(files),
        candidate_tree_sha256=_candidate_tree_sha256(files),
        files=file_digests,
        actual_space_publication=False,
        remote_mutation=False,
        live_inference=False,
        user_input_collection=False,
        next_authorized_step="controlled_remote_space_creation_and_upload",
    )


def build_candidate_payloads(project_root: Path) -> tuple[dict[str, bytes], bytes]:
    files = build_candidate_files(project_root)
    manifest = build_candidate_manifest(project_root)
    manifest_bytes = _canonical_json_bytes(manifest.model_dump(mode="json"))
    return files, manifest_bytes


def _trash_parent(project_root: Path) -> Path:
    return project_root.parent / TRASH_DIRECTORY_NAME


def _quarantine_existing_candidate(
    project_root: Path,
    candidate_root: Path,
) -> Path | None:
    if not candidate_root.exists():
        return None

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


def _write_candidate_tree(root: Path, files: dict[str, bytes]) -> None:
    for relative_path, payload in files.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def write_candidate(project_root: Path) -> HuggingFaceSpacePublicationCandidateManifest:
    files, manifest_bytes = build_candidate_payloads(project_root)
    candidate_root = project_root / CANDIDATE_ROOT_RELATIVE_PATH
    candidate_parent = candidate_root.parent
    candidate_parent.mkdir(parents=True, exist_ok=True)

    if candidate_root.is_symlink():
        raise HuggingFaceSpacePublicationCandidateError(
            "Committed publication candidate root must not be a symlink."
        )

    staging_root = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=candidate_parent))
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
    return build_candidate_manifest(project_root)


def check_committed_candidate(project_root: Path) -> None:
    files, manifest_bytes = build_candidate_payloads(project_root)
    candidate_root = project_root / CANDIDATE_ROOT_RELATIVE_PATH

    if not candidate_root.is_dir():
        raise HuggingFaceSpacePublicationCandidateError(
            "Committed publication candidate directory is missing."
        )

    actual_files = {
        path.relative_to(candidate_root).as_posix()
        for path in candidate_root.rglob("*")
        if path.is_file()
    }
    expected_files = set(files)
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        unexpected = sorted(actual_files - expected_files)
        runtime_artifacts = [
            relative_path
            for relative_path in unexpected
            if any(
                relative_path == forbidden or relative_path.startswith(f"{forbidden}/")
                for forbidden in FORBIDDEN_PATH_PARTS
            )
        ]
        unexpected_source_files = sorted(set(unexpected) - set(runtime_artifacts))
        runtime_roots = sorted(
            {relative_path.split("/", maxsplit=1)[0] for relative_path in runtime_artifacts}
        )
        if runtime_artifacts and not missing and not unexpected_source_files:
            raise HuggingFaceSpacePublicationCandidateError(
                "Committed candidate contains generated runtime artifacts; "
                "validate npm and browser gates in a disposable copy, then regenerate "
                "the committed candidate. "
                f"runtime_roots={runtime_roots}, "
                f"runtime_file_count={len(runtime_artifacts)}"
            )
        raise HuggingFaceSpacePublicationCandidateError(
            "Candidate allowlist mismatch; "
            f"missing={missing}, "
            f"unexpected={unexpected_source_files}, "
            f"unexpected_runtime_roots={runtime_roots}, "
            f"unexpected_runtime_file_count={len(runtime_artifacts)}"
        )

    for relative_path, expected_payload in files.items():
        actual_payload = (candidate_root / relative_path).read_bytes()
        if actual_payload != expected_payload:
            raise HuggingFaceSpacePublicationCandidateError(
                f"Committed candidate drift: {relative_path}"
            )

    manifest_path = project_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise HuggingFaceSpacePublicationCandidateError(
            "Committed publication candidate manifest is missing."
        )
    if manifest_path.read_bytes() != manifest_bytes:
        raise HuggingFaceSpacePublicationCandidateError(
            "Committed publication candidate manifest drift."
        )
