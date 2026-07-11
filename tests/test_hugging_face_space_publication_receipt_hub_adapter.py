from __future__ import annotations

from dataclasses import dataclass

import pytest

import specsafe.hugging_face_space_publication_receipt.hub_adapter as hub_adapter


@dataclass
class FakeResponse:
    status_code: int


class FakeHttpError(RuntimeError):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.response = FakeResponse(status_code=status_code)


def test_retryable_anonymous_read_recovers_after_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    monkeypatch.setattr(hub_adapter.time, "sleep", lambda _: None)

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise FakeHttpError(503)
        return "passed"

    assert hub_adapter._read_with_retry(operation) == "passed"
    assert attempts == 3


def test_non_retryable_anonymous_read_fails_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    monkeypatch.setattr(hub_adapter.time, "sleep", lambda _: None)

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise FakeHttpError(400)

    with pytest.raises(FakeHttpError, match="HTTP 400"):
        hub_adapter._read_with_retry(operation)

    assert attempts == 1


def test_retryable_anonymous_read_has_finite_attempt_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    monkeypatch.setattr(hub_adapter.time, "sleep", lambda _: None)

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise FakeHttpError(503)

    with pytest.raises(FakeHttpError, match="HTTP 503"):
        hub_adapter._read_with_retry(operation, attempts=3)

    assert attempts == 3
