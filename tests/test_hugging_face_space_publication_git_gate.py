from __future__ import annotations

import pytest

from specsafe.hugging_face_space_publication import (
    PublicationGitGateError,
    PublicationGitState,
    validate_publication_git_state,
)

VALID_SHA = "a" * 40


def test_main_clean_git_state_is_authorized() -> None:
    state = PublicationGitState(branch="main", head_sha=VALID_SHA, clean=True)
    assert validate_publication_git_state(state) == state


def test_feature_branch_is_rejected() -> None:
    state = PublicationGitState(
        branch="feat/hugging-face-space-publication-executor",
        head_sha=VALID_SHA,
        clean=True,
    )
    with pytest.raises(PublicationGitGateError, match="only from branch main"):
        validate_publication_git_state(state)


def test_dirty_worktree_is_rejected() -> None:
    state = PublicationGitState(branch="main", head_sha=VALID_SHA, clean=False)
    with pytest.raises(PublicationGitGateError, match="clean working tree"):
        validate_publication_git_state(state)


def test_noncanonical_git_sha_is_rejected() -> None:
    state = PublicationGitState(branch="main", head_sha="abc123", clean=True)
    with pytest.raises(PublicationGitGateError, match="40-character Git SHA"):
        validate_publication_git_state(state)
