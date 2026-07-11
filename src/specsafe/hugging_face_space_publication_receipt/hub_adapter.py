from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypeVar

from .service import AnonymousPublicationGateway

T = TypeVar("T")
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class HuggingFaceAnonymousPublicationGateway(AnonymousPublicationGateway):
    def __init__(self) -> None:
        try:
            from huggingface_hub import HfApi
        except ImportError as error:
            raise RuntimeError(
                "Install the publication dependency with: python -m pip install -e '.[publish]'"
            ) from error
        self._api = HfApi(token=False)

    def repository_state(
        self,
        repo_id: str,
        *,
        revision: str,
    ) -> Mapping[str, object]:
        def read() -> Mapping[str, object]:
            info = self._api.space_info(
                repo_id,
                revision=revision,
                token=False,
            )
            runtime = getattr(info, "runtime", None)
            return {
                "id": info.id,
                "sha": info.sha,
                "private": info.private,
                "gated": getattr(info, "gated", False),
                "sdk": info.sdk,
                "stage": getattr(runtime, "stage", None),
            }

        return _read_with_retry(read)

    def list_files(
        self,
        repo_id: str,
        *,
        revision: str,
    ) -> tuple[str, ...]:
        return _read_with_retry(
            lambda: tuple(
                sorted(
                    self._api.list_repo_files(
                        repo_id,
                        repo_type="space",
                        revision=revision,
                        token=False,
                    )
                )
            )
        )

    def read_file(
        self,
        repo_id: str,
        filename: str,
        *,
        revision: str,
    ) -> bytes:
        from huggingface_hub import hf_hub_download

        def read() -> bytes:
            cached = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type="space",
                revision=revision,
                token=False,
                force_download=True,
            )
            return Path(cached).read_bytes()

        return _read_with_retry(read)

    def fetch_application(self, application_url: str) -> Mapping[str, object]:
        def read() -> Mapping[str, object]:
            request = urllib.request.Request(
                application_url,
                headers={
                    "User-Agent": "SpecSafe-Receipt-Reconciliation/1.0",
                },
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return {
                    "application_url": application_url,
                    "status_code": response.status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "body": response.read(2_000_000),
                }

        return _read_with_retry(read)


def _read_with_retry(
    operation: Callable[[], T],
    *,
    attempts: int = 6,
) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as error:
            status_code = _status_code(error)
            if status_code not in _RETRYABLE_STATUS_CODES or attempt == attempts:
                raise
            time.sleep(min(5 * (2 ** (attempt - 1)), 60))
    raise RuntimeError("anonymous Hugging Face read retry loop exhausted")


def _status_code(error: Exception) -> int | None:
    if isinstance(error, urllib.error.HTTPError):
        return error.code
    response = getattr(error, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None
