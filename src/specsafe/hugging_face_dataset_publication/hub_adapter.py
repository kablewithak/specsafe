from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .service import HubGateway


class HuggingFaceHubGateway(HubGateway):
    def __init__(self) -> None:
        try:
            from huggingface_hub import HfApi
        except ImportError as error:
            raise RuntimeError(
                "Install the publication dependency with: python -m pip install -e '.[publish]'"
            ) from error
        self._api = HfApi()

    def identity(self) -> Mapping[str, object]:
        return self._api.whoami(cache=True)

    def repository_exists(self, repo_id: str) -> bool:
        return self._api.repo_exists(repo_id, repo_type="dataset")

    def create_private_dataset(self, repo_id: str) -> str:
        result = self._api.create_repo(
            repo_id,
            repo_type="dataset",
            visibility="private",
            exist_ok=False,
        )
        return str(result)

    def list_files(self, repo_id: str, *, revision: str | None, anonymous: bool) -> tuple[str, ...]:
        files = self._api.list_repo_files(
            repo_id,
            repo_type="dataset",
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
            commit_message="Publish exact SpecSafe bounded negative-evidence release",
            commit_description=(
                "Exact authorized candidate bytes. No calibrator, scheduler, or production "
                "promotion is claimed."
            ),
            repo_type="dataset",
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
            repo_type="dataset",
            revision=revision,
            force_download=True,
            token=False if anonymous else None,
        )
        return Path(cached).read_bytes()

    def dataset_state(
        self,
        repo_id: str,
        *,
        revision: str,
        anonymous: bool,
    ) -> Mapping[str, object]:
        info = self._api.dataset_info(
            repo_id,
            revision=revision,
            token=False if anonymous else None,
        )
        return {
            "id": info.id,
            "sha": info.sha,
            "private": info.private,
            "gated": info.gated,
        }

    def make_public(self, repo_id: str) -> None:
        self._api.update_repo_settings(
            repo_id,
            repo_type="dataset",
            visibility="public",
            gated=False,
        )

    def make_private(self, repo_id: str) -> None:
        self._api.update_repo_settings(
            repo_id,
            repo_type="dataset",
            visibility="private",
            gated=False,
        )

    def delete_dataset(self, repo_id: str) -> None:
        self._api.delete_repo(repo_id, repo_type="dataset", missing_ok=True)
