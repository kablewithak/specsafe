from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

import specsafe.hugging_face_space_prebuilt_candidate.builder as builder
from specsafe.hugging_face_space_prebuilt_candidate import (
    HuggingFaceSpacePrebuiltCandidateError,
    build_prebuilt_candidate_payloads,
    check_committed_prebuilt_candidate,
    write_prebuilt_candidate,
)
from specsafe.hugging_face_space_publication_candidate import (
    CandidateFileDigest,
    HuggingFaceSpacePublicationCandidateManifest,
    SpaceMetadata,
)

SOURCE_FILE_COUNT = 35
SOURCE_TREE_SHA256 = "041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='specsafe'\n", encoding="utf-8")

    evidence = b'{"read_only":true}\n'
    monkeypatch.setattr(builder, "EXPECTED_EVIDENCE_BYTE_COUNT", len(evidence))
    monkeypatch.setattr(builder, "EXPECTED_EVIDENCE_SHA256", _sha256(evidence))

    source_root = root / builder.SOURCE_CANDIDATE_ROOT_RELATIVE_PATH
    source_root.mkdir(parents=True)
    source_files: list[CandidateFileDigest] = []
    for index in range(SOURCE_FILE_COUNT - 1):
        relative_path = f"source-{index:02d}.txt"
        payload = f"source-{index}\n".encode()
        (source_root / relative_path).write_bytes(payload)
        source_files.append(
            CandidateFileDigest(
                relative_path=relative_path,
                byte_count=len(payload),
                sha256=_sha256(payload),
            )
        )

    evidence_path = source_root / "public/evidence/evidence_index.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_bytes(evidence)
    source_files.append(
        CandidateFileDigest(
            relative_path="public/evidence/evidence_index.json",
            byte_count=len(evidence),
            sha256=_sha256(evidence),
        )
    )
    source_files = sorted(source_files, key=lambda item: item.relative_path)

    manifest = HuggingFaceSpacePublicationCandidateManifest(
        schema_version="specsafe_hugging_face_space_publication_candidate_manifest_v1",
        space_repository_name="specsafe-reliability-lab",
        source_app_relative_path="apps/specsafe-reliability-lab",
        candidate_root_relative_path=(
            "release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space"
        ),
        source_commit="2848e80",
        metadata=SpaceMetadata(
            title="SpecSafe - When Should AI Spend More Compute?",
            emoji="🛡️",
            color_from="yellow",
            color_to="red",
            sdk="static",
            app_build_command="npm run build",
            app_file="dist/index.html",
            full_width=True,
            header="mini",
            short_description="AI reliability case study on adaptive verification.",
            datasets=("KaboKableMolefe/specsafe-bounded-negative-evidence-v1",),
            tags=("ai-evaluation",),
            pinned=False,
        ),
        evidence_index_relative_path="public/evidence/evidence_index.json",
        evidence_index_byte_count=len(evidence),
        evidence_index_sha256=_sha256(evidence),
        exact_candidate_file_count=SOURCE_FILE_COUNT,
        candidate_tree_sha256=SOURCE_TREE_SHA256,
        files=tuple(source_files),
        actual_space_publication=False,
        remote_mutation=False,
        live_inference=False,
        user_input_collection=False,
        next_authorized_step="controlled_remote_space_creation_and_upload",
    )
    manifest_path = root / builder.SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return root, evidence


def _source_validator(_: Path) -> None:
    return None


def test_prebuilt_candidate_contains_runtime_assets_without_provider_build(
    project: tuple[Path, bytes],
) -> None:
    root, evidence = project
    runner = FakeBuildRunner(evidence)

    files, manifest_bytes, manifest = build_prebuilt_candidate_payloads(
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
    readme = files["README.md"].decode("utf-8")
    assert "sdk: static" in readme
    assert "app_file: index.html" in readme
    assert "app_build_command:" not in readme
    assert "provider_side_build_required=false" in readme
    assert manifest.provider_side_build_required is False
    assert manifest.build_strategy == "local_validated_prebuilt_static_assets"
    assert manifest.exact_candidate_file_count == 5
    assert json.loads(manifest_bytes)["candidate_tree_sha256"] == (manifest.candidate_tree_sha256)


def test_build_environment_does_not_inherit_hugging_face_tokens(
    project: tuple[Path, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, evidence = project
    monkeypatch.setenv("HF_TOKEN", "hf_should_not_escape")
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "also_should_not_escape")
    runner = FakeBuildRunner(evidence)

    build_prebuilt_candidate_payloads(
        root,
        command_runner=runner,
        source_validator=_source_validator,
    )

    for environment in runner.environments:
        assert "HF_TOKEN" not in environment
        assert "HUGGING_FACE_HUB_TOKEN" not in environment


def test_missing_index_is_rejected(project: tuple[Path, bytes]) -> None:
    root, evidence = project
    runner = FakeBuildRunner(evidence, omit_index=True)

    with pytest.raises(HuggingFaceSpacePrebuiltCandidateError, match="index.html"):
        build_prebuilt_candidate_payloads(
            root,
            command_runner=runner,
            source_validator=_source_validator,
        )


def test_evidence_drift_is_rejected(project: tuple[Path, bytes]) -> None:
    root, evidence = project
    runner = FakeBuildRunner(evidence, drift_evidence=True)

    with pytest.raises(HuggingFaceSpacePrebuiltCandidateError, match="byte count"):
        build_prebuilt_candidate_payloads(
            root,
            command_runner=runner,
            source_validator=_source_validator,
        )


def test_write_and_check_round_trip(project: tuple[Path, bytes]) -> None:
    root, evidence = project

    written = write_prebuilt_candidate(
        root,
        command_runner=FakeBuildRunner(evidence),
        source_validator=_source_validator,
    )
    checked = check_committed_prebuilt_candidate(
        root,
        command_runner=FakeBuildRunner(evidence),
        source_validator=_source_validator,
    )

    assert checked == written
    assert (root / builder.CANDIDATE_ROOT_RELATIVE_PATH / "index.html").is_file()
    assert (root / builder.MANIFEST_RELATIVE_PATH).is_file()


def test_committed_candidate_drift_is_rejected(project: tuple[Path, bytes]) -> None:
    root, evidence = project
    write_prebuilt_candidate(
        root,
        command_runner=FakeBuildRunner(evidence),
        source_validator=_source_validator,
    )
    index = root / builder.CANDIDATE_ROOT_RELATIVE_PATH / "index.html"
    index.write_bytes(index.read_bytes() + b"drift")

    with pytest.raises(
        HuggingFaceSpacePrebuiltCandidateError,
        match="Committed prebuilt candidate drift: index.html",
    ):
        check_committed_prebuilt_candidate(
            root,
            command_runner=FakeBuildRunner(evidence),
            source_validator=_source_validator,
        )


def test_unknown_source_candidate_tree_is_rejected(
    project: tuple[Path, bytes],
) -> None:
    root, evidence = project
    manifest_path = root / builder.SOURCE_CANDIDATE_MANIFEST_RELATIVE_PATH
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["candidate_tree_sha256"] = "f" * 64
    manifest_path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(
        HuggingFaceSpacePrebuiltCandidateError,
        match="outside the frozen prebuilt-build boundary",
    ):
        build_prebuilt_candidate_payloads(
            root,
            command_runner=FakeBuildRunner(evidence),
            source_validator=_source_validator,
        )


def test_command_resolution_prefers_npm_cmd_on_windows() -> None:
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


def test_command_resolution_falls_back_to_npm_on_windows() -> None:
    looked_up: list[str] = []

    def fake_which(name: str) -> str | None:
        looked_up.append(name)
        if name == "npm":
            return r"C:\tools\npm.exe"
        return None

    resolved = builder._resolve_command(
        ("npm", "run", "build"),
        which=fake_which,
        platform_name="nt",
    )

    assert resolved == (r"C:\tools\npm.exe", "run", "build")
    assert looked_up == ["npm.cmd", "npm"]


def test_command_resolution_uses_npm_on_non_windows() -> None:
    looked_up: list[str] = []

    def fake_which(name: str) -> str | None:
        looked_up.append(name)
        return "/usr/local/bin/npm" if name == "npm" else None

    resolved = builder._resolve_command(
        ("npm", "run", "test"),
        which=fake_which,
        platform_name="posix",
    )

    assert resolved == ("/usr/local/bin/npm", "run", "test")
    assert looked_up == ["npm"]


def test_command_resolution_rejects_missing_npm() -> None:
    with pytest.raises(
        HuggingFaceSpacePrebuiltCandidateError,
        match="Install Node.js/npm and ensure it is on PATH",
    ):
        builder._resolve_command(
            ("npm", "ci"),
            which=lambda _: None,
            platform_name="nt",
        )
