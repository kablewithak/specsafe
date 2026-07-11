from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .service import HubGateway


class HuggingFaceSpaceHubGateway(HubGateway):
    def __init__(self, *, token: str) -> None:
        if not token.strip():
            raise ValueError("a non-empty Hugging Face token is required")
        try:
            from huggingface_hub import HfApi
        except ImportError as error:
            raise RuntimeError(
                "Install the publication dependency with: python -m pip install -e '.[publish]'"
            ) from error
        self._api = HfApi(token=token)

    def identity(self) -> Mapping[str, object]:
        return self._api.whoami(cache=True)

    def repository_exists(self, repo_id: str) -> bool:
        return self._api.repo_exists(repo_id, repo_type="space")

    def create_private_space(self, repo_id: str) -> str:
        result = self._api.create_repo(
            repo_id,
            repo_type="space",
            visibility="private",
            exist_ok=False,
            space_sdk="static",
        )
        return str(result)

    def list_files(
        self,
        repo_id: str,
        *,
        revision: str | None,
        anonymous: bool,
    ) -> tuple[str, ...]:
        files = self._api.list_repo_files(
            repo_id,
            repo_type="space",
            revision=revision,
            token=False if anonymous else None,
        )
        return tuple(sorted(files))

    def commit_exact_files(
        self,
        repo_id: str,
        files: Mapping[str, Path],
        *,
        delete_paths: tuple[str, ...],
    ) -> str:
        from huggingface_hub import CommitOperationAdd, CommitOperationDelete

        operations = [
            CommitOperationAdd(path_in_repo=name, path_or_fileobj=path)
            for name, path in sorted(files.items())
        ]
        operations.extend(
            CommitOperationDelete(path_in_repo=path, is_folder=False) for path in delete_paths
        )
        result = self._api.create_commit(
            repo_id,
            operations=operations,
            commit_message="Publish exact SpecSafe reliability Space",
            commit_description=(
                "Exact authorized static-Space candidate. Read-only evidence presentation; "
                "no live inference, input collection, or production performance claim."
            ),
            repo_type="space",
            revision="main",
            create_pr=False,
        )
        return result.oid

    def read_file(
        self,
        repo_id: str,
        filename: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> bytes:
        from huggingface_hub import hf_hub_download

        cached = hf_hub_download(
            repo_id,
            filename,
            repo_type="space",
            revision=revision,
            force_download=True,
            token=False if anonymous else None,
        )
        return Path(cached).read_bytes()

    def space_state(
        self,
        repo_id: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> Mapping[str, object]:
        info = self._api.space_info(
            repo_id,
            revision=revision,
            token=False if anonymous else None,
        )
        return {
            "id": info.id,
            "sha": info.sha,
            "private": info.private,
            "gated": getattr(info, "gated", False),
            "sdk": info.sdk,
            "host": getattr(info, "host", None),
            "subdomain": getattr(info, "subdomain", None),
        }

    def make_public(self, repo_id: str) -> None:
        self._api.update_repo_settings(
            repo_id,
            repo_type="space",
            visibility="public",
            gated=False,
        )

    def make_private(self, repo_id: str) -> None:
        self._api.update_repo_settings(
            repo_id,
            repo_type="space",
            visibility="private",
            gated=False,
        )

    def delete_space(self, repo_id: str) -> None:
        self._api.delete_repo(repo_id, repo_type="space", missing_ok=True)

    def wait_for_public_application(
        self,
        repo_id: str,
        *,
        timeout_seconds: int,
    ) -> Mapping[str, object]:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        deadline = time.monotonic() + timeout_seconds
        last_state: dict[str, object] = {}
        last_error = "public application was not reachable"
        while time.monotonic() < deadline:
            try:
                info = self._api.space_info(repo_id, token=False)
                runtime = getattr(info, "runtime", None)
                stage = getattr(runtime, "stage", None)
                host = getattr(info, "host", None)
                subdomain = getattr(info, "subdomain", None)
                application_url = _normalize_application_url(host, subdomain)
                last_state = {
                    "stage": stage,
                    "application_url": application_url,
                }

                if stage in {"BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"}:
                    raise RuntimeError(f"Space entered terminal error stage: {stage}")
                if application_url is not None:
                    response = _fetch_application(application_url)
                    last_state.update(response)
                    if (
                        response["status_code"] == 200
                        and "text/html" in str(response["content_type"]).lower()
                    ):
                        return last_state
            except Exception as error:
                last_error = str(error)
            time.sleep(min(5.0, max(0.0, deadline - time.monotonic())))

        raise TimeoutError(
            "public Space application did not become ready before timeout; "
            f"last_state={_safe_state(last_state)}, last_error={last_error}"
        )


def _normalize_application_url(host: Any, subdomain: Any) -> str | None:
    value: str | None = None
    if isinstance(host, str) and host.strip():
        value = host.strip()
    elif isinstance(subdomain, str) and subdomain.strip():
        value = subdomain.strip()
        if "." not in value:
            value = f"{value}.hf.space"

    if value is None:
        return None
    if value.startswith("https://"):
        return value.rstrip("/")
    if value.startswith("http://"):
        return f"https://{value.removeprefix('http://').rstrip('/')}"
    return f"https://{value.rstrip('/')}"


def _fetch_application(application_url: str) -> dict[str, object]:
    request = urllib.request.Request(
        application_url,
        headers={"User-Agent": "SpecSafe-Publication-Verification/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return {
            "status_code": response.status,
            "content_type": response.headers.get("Content-Type", ""),
            "body": response.read(2_000_000),
        }


def _safe_state(state: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in state.items()
        if key in {"stage", "application_url", "status_code", "content_type"}
    }
