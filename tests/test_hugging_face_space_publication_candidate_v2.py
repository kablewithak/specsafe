from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from specsafe.hugging_face_space_publication_candidate.builder import (
    CANDIDATE_ROOT_RELATIVE_PATH as V1_CANDIDATE_ROOT,
)
from specsafe.hugging_face_space_publication_candidate.builder import (
    MANIFEST_RELATIVE_PATH as V1_MANIFEST_PATH,
)
from specsafe.hugging_face_space_publication_candidate_v2 import (
    CANDIDATE_ROOT_RELATIVE_PATH,
    MANIFEST_RELATIVE_PATH,
    REDESIGN_SOURCE_COMMIT,
    SOURCE_APP_RELATIVE_PATH,
    HuggingFaceSpacePublicationCandidateV2Error,
    build_candidate_files_v2,
    build_candidate_manifest_v2,
    check_committed_candidate_v2,
    write_candidate_v2,
)
from specsafe.hugging_face_space_publication_candidate_v2.builder import (
    CANONICAL_EVIDENCE_RELATIVE_PATH,
    EXPECTED_EVIDENCE_SHA256,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_v2_namespace_is_parallel_to_retained_v1() -> None:
    assert CANDIDATE_ROOT_RELATIVE_PATH != V1_CANDIDATE_ROOT
    assert MANIFEST_RELATIVE_PATH != V1_MANIFEST_PATH
    assert "publication-v2" in CANDIDATE_ROOT_RELATIVE_PATH.as_posix()
    assert "publication-v2" in MANIFEST_RELATIVE_PATH.as_posix()


def test_v2_candidate_binds_redesign_source_and_frozen_evidence() -> None:
    files = build_candidate_files_v2(PROJECT_ROOT)
    manifest = build_candidate_manifest_v2(PROJECT_ROOT)

    assert manifest.source_commit == REDESIGN_SOURCE_COMMIT
    assert manifest.evidence_index_sha256 == EXPECTED_EVIDENCE_SHA256
    assert manifest.actual_space_publication is False
    assert manifest.remote_mutation is False
    assert manifest.next_authorized_step == "build_and_qualify_prebuilt_candidate_v2"

    required_redesign_files = {
        "src/components/site-header.tsx",
        "src/content/definitions.ts",
        "src/content/explanations.ts",
        "src/content/navigation.ts",
        "src/sections/hero-section.tsx",
        "src/sections/results-section.tsx",
        "src/sections/confidence-gate-section.tsx",
        "src/sections/findings-section.tsx",
        "src/sections/evidence-explorer-section.tsx",
        "tests/navigation.spec.ts",
    }
    assert required_redesign_files.issubset(files)


def test_v2_candidate_is_standalone_and_fail_closed() -> None:
    files = build_candidate_files_v2(PROJECT_ROOT)

    assert "package.json" in files
    assert "public/evidence/evidence_index.json" in files
    assert "scripts/verify-evidence.mjs" in files
    assert b"evidence:sync" not in files["package.json"]
    assert b"applied-caas-gateway" not in files["package-lock.json"]
    assert not files["package-lock.json"].startswith(b"\xef\xbb\xbf")


def test_v2_normalizes_source_line_endings(tmp_path: Path) -> None:
    project = _copy_inputs(tmp_path)
    css_path = project / SOURCE_APP_RELATIVE_PATH / "src" / "index.css"

    original = css_path.read_bytes().replace(b"\r\n", b"\n")
    css_path.write_bytes(original.replace(b"\n", b"\r\n"))

    files = build_candidate_files_v2(project)

    assert b"\r\n" not in files["src/index.css"]
    assert files["src/index.css"] == original


def test_v2_rejects_unreviewed_source_file(tmp_path: Path) -> None:
    project = _copy_inputs(tmp_path)
    unexpected = project / SOURCE_APP_RELATIVE_PATH / "src" / "unexpected.ts"
    unexpected.write_text("export const unexpected = true;\n", encoding="utf-8")

    with pytest.raises(
        HuggingFaceSpacePublicationCandidateV2Error,
        match="source allowlist mismatch",
    ):
        build_candidate_files_v2(project)


def test_v2_rejects_evidence_drift(tmp_path: Path) -> None:
    project = _copy_inputs(tmp_path)
    evidence = project / CANONICAL_EVIDENCE_RELATIVE_PATH
    evidence.write_bytes(evidence.read_bytes() + b"drift")

    with pytest.raises(
        HuggingFaceSpacePublicationCandidateV2Error,
        match="byte-count mismatch",
    ):
        build_candidate_files_v2(project)


def test_v2_write_and_check_round_trip(tmp_path: Path) -> None:
    project = _copy_inputs(tmp_path)

    written = write_candidate_v2(project)
    check_committed_candidate_v2(project)

    assert written.source_commit == REDESIGN_SOURCE_COMMIT
    assert (project / CANDIDATE_ROOT_RELATIVE_PATH).is_dir()
    assert (project / MANIFEST_RELATIVE_PATH).is_file()


def test_committed_v2_candidate_is_canonical() -> None:
    check_committed_candidate_v2(PROJECT_ROOT)


def _copy_inputs(tmp_path: Path) -> Path:
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
