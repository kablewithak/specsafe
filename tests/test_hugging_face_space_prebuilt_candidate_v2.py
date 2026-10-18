from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path

import pytest

import specsafe.hugging_face_space_prebuilt_candidate.builder as v1_builder
import specsafe.hugging_face_space_prebuilt_candidate_v2.builder as builder
from specsafe.hugging_face_space_prebuilt_candidate_v2 import (
    HuggingFaceSpacePrebuiltCandidateV2Error,
    build_prebuilt_candidate_payloads_v2,
    check_committed_prebuilt_candidate_v2,
    write_prebuilt_candidate_v2,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE_COUNT = 58


class FakeBuildRunner:
    def __init__(
        self,
        evidence: bytes,
        *,
        omit_index: bool = False,
        drift_evidence: bool = False,
    ) -> None:
        self.evidence = evidence
        self.omit_index = omit_index
        self.drift_evidence = drift_evidence
        self.commands: list[tuple[str, ...]] = []
        self.environments: list[Mapping[str, str]] = []

    def __call__(
        self,
        working_directory: Path,
        command: tuple[str, ...],
        timeout_seconds: int,
        environment: Mapping[str, str],
    ) -> None:
        assert timeout_seconds > 0
        self.commands.append(command)
        self.environments.append(environment)
        if command != ("npm", "run", "build"):
            return

        dist = working_directory / "dist"
        assets = dist / "assets"
        evidence_root = dist / "evidence"
        assets.mkdir(parents=True)
        evidence_root.mkdir(parents=True)

        if not self.omit_index:
            (dist / "index.html").write_text(
                (
                    "<!doctype html><html><head><title>SpecSafe</title>"
                    '<link rel="stylesheet" href="/assets/app.css"></head>'
                    '<body><div id="root"></div>'
                    '<script type="module" src="/assets/app.js"></script>'
                    "</body></html>"
                ),
                encoding="utf-8",
                newline="\n",
            )
        (assets / "app.css").write_text("body{margin:0}\n", encoding="utf-8", newline="\n")
        (assets / "app.js").write_text(
            'document.querySelector("#root").textContent="SpecSafe";\n',
            encoding="utf-8",
            newline="\n",
        )
        payload = self.evidence + (b"drift" if self.drift_evidence else b"")
        (evidence_root / "evidence_index.json").write_bytes(payload)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, bytes]:
    # Exercise the real, frozen V2 release contract, not a synthetic manifest.
    # A shallow test-only source path avoids Windows MAX_PATH failures.
    retained_root = PROJECT_ROOT / builder.SOURCE_CANDIDATE_ROOT_RELATIVE_PATH
    retained_manifest = PROJECT_ROOT / builder.SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH

    root = tmp_path / "project"
    root.mkdir()
    source_root = root / "source"
    shutil.copytree(retained_root, source_root)
    shutil.copyfile(retained_manifest, root / "manifest.json")

    monkeypatch.setattr(builder, "SOURCE_CANDIDATE_ROOT_RELATIVE_PATH", Path("source"))
    monkeypatch.setattr(builder, "SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH", Path("manifest.json"))

    # Independently validate each fixture's source bytes before the fake npm
    # runner is allowed to exercise the output and failure gates.
    builder._validate_retained_source(root)
    evidence = (source_root / "public/evidence/evidence_index.json").read_bytes()
    return root, evidence


def _source_validator(_: Path) -> None:
    return None


def test_v2_namespace_is_parallel_to_retained_v1() -> None:
    assert builder.CANDIDATE_ROOT_RELATIVE_PATH != v1_builder.CANDIDATE_ROOT_RELATIVE_PATH
    assert builder.MANIFEST_RELATIVE_PATH != v1_builder.MANIFEST_RELATIVE_PATH
    assert (
        builder.SOURCE_CANDIDATE_ROOT_RELATIVE_PATH
        != v1_builder.SOURCE_CANDIDATE_ROOT_RELATIVE_PATH
    )


def test_v2_prebuilt_candidate_contains_runtime_assets_without_provider_build(
    project: tuple[Path, bytes],
) -> None:
    root, evidence = project
    runner = FakeBuildRunner(evidence)

    files, manifest_bytes, manifest = build_prebuilt_candidate_payloads_v2(
        root,
        command_runner=runner,
        source_validator=_source_validator,
    )

    assert tuple(runner.commands) == builder.BUILD_COMMANDS
    assert set(files) == {
        "README.md",
        "assets/app.css",
        "assets/app.js",
        "evidence/evidence_index.json",
        "index.html",
    }
    assert manifest.lineage_version == "v2"
    assert manifest.source_commit == builder.EXPECTED_SOURCE_COMMIT
    assert manifest.source_candidate_file_count == SOURCE_FILE_COUNT
    assert manifest.provider_side_build_required is False
    assert manifest.remote_mutation is False
    assert manifest.build_strategy == "local_validated_prebuilt_static_assets"
    assert manifest.exact_candidate_file_count == 5
    assert json.loads(manifest_bytes)["candidate_tree_sha256"] == manifest.candidate_tree_sha256


def test_v2_build_environment_does_not_inherit_hugging_face_tokens(
    project: tuple[Path, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, evidence = project
    monkeypatch.setenv("HF_TOKEN", "hf_should_not_escape")
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "also_should_not_escape")
    monkeypatch.setenv("HUGGINGFACE_TOKEN", "also_should_not_escape")
    runner = FakeBuildRunner(evidence)

    build_prebuilt_candidate_payloads_v2(
        root,
        command_runner=runner,
        source_validator=_source_validator,
    )

    for environment in runner.environments:
        assert "HF_TOKEN" not in environment
        assert "HUGGING_FACE_HUB_TOKEN" not in environment
        assert "HUGGINGFACE_TOKEN" not in environment


def test_v2_retained_source_candidate_drift_is_rejected(
    project: tuple[Path, bytes],
) -> None:
    root, _ = project
    source = root / builder.SOURCE_CANDIDATE_ROOT_RELATIVE_PATH / "src/App.tsx"
    source.write_bytes(source.read_bytes() + b"drift")

    with pytest.raises(
        HuggingFaceSpacePrebuiltCandidateV2Error,
        match="Retained V2 source candidate drift",
    ):
        builder._validate_retained_source(root)


def test_v2_unknown_source_tree_is_rejected(
    project: tuple[Path, bytes],
) -> None:
    root, _ = project
    manifest_path = root / builder.SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["candidate_tree_sha256"] = "f" * 64
    manifest_path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(
        HuggingFaceSpacePrebuiltCandidateV2Error,
        match="outside the frozen prebuilt-build boundary",
    ):
        builder._validate_retained_source(root)


def test_v2_missing_index_is_rejected(project: tuple[Path, bytes]) -> None:
    root, evidence = project
    runner = FakeBuildRunner(evidence, omit_index=True)

    with pytest.raises(HuggingFaceSpacePrebuiltCandidateV2Error, match="index.html"):
        build_prebuilt_candidate_payloads_v2(
            root,
            command_runner=runner,
            source_validator=_source_validator,
        )


def test_v2_evidence_drift_is_rejected(project: tuple[Path, bytes]) -> None:
    root, evidence = project
    runner = FakeBuildRunner(evidence, drift_evidence=True)

    with pytest.raises(HuggingFaceSpacePrebuiltCandidateV2Error, match="byte count"):
        build_prebuilt_candidate_payloads_v2(
            root,
            command_runner=runner,
            source_validator=_source_validator,
        )


def test_v2_write_and_check_round_trip(project: tuple[Path, bytes]) -> None:
    root, evidence = project

    written = write_prebuilt_candidate_v2(
        root,
        command_runner=FakeBuildRunner(evidence),
        source_validator=_source_validator,
    )
    checked = check_committed_prebuilt_candidate_v2(
        root,
        command_runner=FakeBuildRunner(evidence),
        source_validator=_source_validator,
    )

    assert checked == written
    assert (root / builder.CANDIDATE_ROOT_RELATIVE_PATH / "index.html").is_file()
    assert (root / builder.MANIFEST_RELATIVE_PATH).is_file()


def test_v2_committed_candidate_drift_is_rejected(
    project: tuple[Path, bytes],
) -> None:
    root, evidence = project
    write_prebuilt_candidate_v2(
        root,
        command_runner=FakeBuildRunner(evidence),
        source_validator=_source_validator,
    )
    index = root / builder.CANDIDATE_ROOT_RELATIVE_PATH / "index.html"
    index.write_bytes(index.read_bytes() + b"drift")

    with pytest.raises(
        HuggingFaceSpacePrebuiltCandidateV2Error,
        match="Committed V2 prebuilt candidate drift: index.html",
    ):
        check_committed_prebuilt_candidate_v2(
            root,
            command_runner=FakeBuildRunner(evidence),
            source_validator=_source_validator,
        )


def test_v2_command_resolution_prefers_npm_cmd_on_windows() -> None:
    looked_up: list[str] = []

    def fake_which(name: str) -> str | None:
        looked_up.append(name)
        if name == "npm.cmd":
            return r"C:\Program Files\nodejs\npm.cmd"
        return None

    resolved = builder._resolve_command(
        ("npm", "ci"),
        which=fake_which,
        platform_name="nt",
    )

    assert resolved == (r"C:\Program Files\nodejs\npm.cmd", "ci")
    assert looked_up == ["npm.cmd"]


def test_committed_v2_prebuilt_candidate_is_canonical() -> None:
    check_committed_prebuilt_candidate_v2(PROJECT_ROOT)
