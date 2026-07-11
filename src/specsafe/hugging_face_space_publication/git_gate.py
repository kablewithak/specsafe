from __future__ import annotations

import re
import subprocess
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class PublicationGitState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    branch: str
    head_sha: str
    clean: bool


class PublicationGitGateErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_space_publish_git_invalid_project_root"
    GIT_COMMAND_FAILED = "hf_space_publish_git_command_failed"
    DETACHED_HEAD = "hf_space_publish_git_detached_head"
    NOT_MAIN = "hf_space_publish_git_not_main"
    WORKTREE_DIRTY = "hf_space_publish_git_worktree_dirty"
    HEAD_SHA_INVALID = "hf_space_publish_git_head_sha_invalid"


class PublicationGitGateError(RuntimeError):
    def __init__(self, code: PublicationGitGateErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def read_publication_git_state(project_root: Path | str) -> PublicationGitState:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise PublicationGitGateError(
            PublicationGitGateErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )

    branch = _run_git(root, "branch", "--show-current").strip()
    if not branch:
        raise PublicationGitGateError(
            PublicationGitGateErrorCode.DETACHED_HEAD,
            "Hugging Face Space publication requires an attached main branch",
        )

    head_sha = _run_git(root, "rev-parse", "HEAD").strip()
    status = _run_git(root, "status", "--porcelain")
    return PublicationGitState(
        branch=branch,
        head_sha=head_sha,
        clean=not status.strip(),
    )


def validate_publication_git_state(state: PublicationGitState) -> PublicationGitState:
    if state.branch != "main":
        raise PublicationGitGateError(
            PublicationGitGateErrorCode.NOT_MAIN,
            "Hugging Face Space publication may run only from branch main",
        )
    if not state.clean:
        raise PublicationGitGateError(
            PublicationGitGateErrorCode.WORKTREE_DIRTY,
            "Hugging Face Space publication requires a clean working tree",
        )
    if not re.fullmatch(r"[0-9a-f]{40}", state.head_sha):
        raise PublicationGitGateError(
            PublicationGitGateErrorCode.HEAD_SHA_INVALID,
            "Hugging Face Space publication requires a canonical 40-character Git SHA",
        )
    return state


def _run_git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PublicationGitGateError(
            PublicationGitGateErrorCode.GIT_COMMAND_FAILED,
            f"Git state check failed for arguments: {' '.join(arguments)}",
        ) from error
    return result.stdout
