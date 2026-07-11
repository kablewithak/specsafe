from __future__ import annotations

from types import SimpleNamespace

import pytest

from specsafe.hugging_face_space_publication.hub_adapter import (
    HuggingFaceSpaceHubGateway,
    _merge_initial_scaffold_deletions,
    _normalize_initial_space_files,
)


def test_known_static_space_scaffold_is_normalized_for_service_validation() -> None:
    files = (
        ".gitattributes",
        "README.md",
        "index.html",
        "style.css",
    )

    assert _normalize_initial_space_files(files) == (".gitattributes",)


def test_known_static_space_scaffold_subset_is_accepted() -> None:
    assert _normalize_initial_space_files(("README.md", "index.html")) == ()


def test_unknown_initial_file_is_not_hidden_from_service_validation() -> None:
    files = (
        ".gitattributes",
        "README.md",
        "index.html",
        "secrets.txt",
        "style.css",
    )

    assert _normalize_initial_space_files(files) == files


def test_stale_scaffold_is_deleted_but_candidate_paths_are_overwritten() -> None:
    delete_paths = _merge_initial_scaffold_deletions(
        initial_files=(
            ".gitattributes",
            "README.md",
            "index.html",
            "style.css",
        ),
        candidate_files=(
            "README.md",
            "assets/index.css",
            "assets/index.js",
            "evidence/evidence_index.json",
            "index.html",
        ),
        requested_delete_paths=(".gitattributes",),
    )

    assert delete_paths == (".gitattributes", "style.css")


def test_explicit_delete_paths_are_retained_and_deduplicated() -> None:
    delete_paths = _merge_initial_scaffold_deletions(
        initial_files=(".gitattributes",),
        candidate_files=("README.md",),
        requested_delete_paths=(".gitattributes", ".gitattributes"),
    )

    assert delete_paths == (".gitattributes",)


def test_terminal_space_stage_fails_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeApi:
        def space_info(self, repo_id: str, token: bool) -> SimpleNamespace:
            return SimpleNamespace(
                runtime=SimpleNamespace(stage="CONFIG_ERROR"),
                host="example.static.hf.space",
                subdomain=None,
            )

    gateway = object.__new__(HuggingFaceSpaceHubGateway)
    gateway._api = FakeApi()
    gateway._initial_scaffold_files = ()

    def fail_sleep(seconds: float) -> None:
        pytest.fail(f"terminal state must not sleep or retry: {seconds}")

    monkeypatch.setattr(
        "specsafe.hugging_face_space_publication.hub_adapter.time.sleep",
        fail_sleep,
    )

    with pytest.raises(RuntimeError, match="terminal error stage: CONFIG_ERROR"):
        gateway.wait_for_public_application(
            "KaboKableMolefe/specsafe-reliability-lab",
            timeout_seconds=900,
        )
