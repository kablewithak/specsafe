"""Strict loader for immutable synthetic SpecSafe trace fixtures."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from specsafe.contracts import (
    SyntheticTraceExpectedOutcomes,
    SyntheticTraceFixtureManifest,
    SyntheticTraceFixtureManifestEntry,
    SyntheticTraceFixtureSet,
    SyntheticTraceReplayCase,
    SyntheticTraceRuntimeInput,
    TraceArtifactKind,
    TraceFixtureViolationCode,
)


class SyntheticTraceFixtureLoadError(ValueError):
    """Typed error returned when a local fixture cannot be trusted for replay."""

    def __init__(self, code: TraceFixtureViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def load_synthetic_trace_fixture_set(fixture_root: Path) -> SyntheticTraceFixtureSet:
    """Load and verify a versioned synthetic fixture set from a local repository path.

    The loader validates the manifest first, hashes every declared artifact, parses runtime
    inputs and expected outcomes through strict Pydantic contracts, and only then composes
    replay cases. Runtime policies remain responsible for consuming only individual
    ``CausalSchedulerContext`` values from the runtime-input side of each loaded case.
    """

    root = fixture_root.resolve()
    manifest_path = root / "manifest.json"
    manifest_payload = _read_json(manifest_path, TraceFixtureViolationCode.TRACE_MANIFEST_MISMATCH)

    try:
        manifest = SyntheticTraceFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_SCHEMA_ERROR,
            f"manifest schema validation failed: {error}",
        ) from error

    artifacts_by_case: dict[str, dict[TraceArtifactKind, object]] = defaultdict(dict)
    for entry in manifest.entries:
        artifact = _load_manifest_artifact(root, entry)
        artifacts_by_case[entry.case_id][entry.artifact_kind] = artifact

    cases: list[SyntheticTraceReplayCase] = []
    for case_id in sorted(artifacts_by_case):
        artifacts = artifacts_by_case[case_id]
        runtime_input = artifacts.get(TraceArtifactKind.RUNTIME_INPUT)
        expected_outcomes = artifacts.get(TraceArtifactKind.EXPECTED_OUTCOMES)
        if not isinstance(runtime_input, SyntheticTraceRuntimeInput):
            raise SyntheticTraceFixtureLoadError(
                TraceFixtureViolationCode.TRACE_SCHEMA_ERROR,
                f"case {case_id} is missing a parsed runtime input",
            )
        if not isinstance(expected_outcomes, SyntheticTraceExpectedOutcomes):
            raise SyntheticTraceFixtureLoadError(
                TraceFixtureViolationCode.TRACE_SCHEMA_ERROR,
                f"case {case_id} is missing parsed expected outcomes",
            )
        try:
            cases.append(
                SyntheticTraceReplayCase(
                    runtime_input=runtime_input,
                    expected_outcomes=expected_outcomes,
                )
            )
        except ValidationError as error:
            raise SyntheticTraceFixtureLoadError(
                TraceFixtureViolationCode.TRACE_PROVENANCE_MISMATCH,
                f"case {case_id} runtime/outcome alignment failed: {error}",
            ) from error

    try:
        return SyntheticTraceFixtureSet(manifest=manifest, cases=tuple(cases))
    except ValidationError as error:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_PROVENANCE_MISMATCH,
            f"loaded fixture set does not match its manifest: {error}",
        ) from error


def _load_manifest_artifact(
    root: Path,
    entry: SyntheticTraceFixtureManifestEntry,
) -> SyntheticTraceRuntimeInput | SyntheticTraceExpectedOutcomes:
    """Hash-check, parse, and provenance-check one manifest-declared JSON artifact."""

    artifact_path = _resolve_artifact_path(root, entry.relative_path)
    raw_bytes = _read_bytes(artifact_path)
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    if actual_hash != entry.sha256 or len(raw_bytes) != entry.byte_count:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_MANIFEST_MISMATCH,
            f"manifest mismatch for {entry.relative_path}",
        )

    try:
        payload: Any = json.loads(raw_bytes)
    except json.JSONDecodeError as error:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_SCHEMA_ERROR,
            f"invalid JSON in {entry.relative_path}: {error.msg}",
        ) from error

    try:
        if entry.artifact_kind is TraceArtifactKind.RUNTIME_INPUT:
            artifact = SyntheticTraceRuntimeInput.model_validate(payload)
        else:
            artifact = SyntheticTraceExpectedOutcomes.model_validate(payload)
    except ValidationError as error:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_SCHEMA_ERROR,
            f"schema validation failed for {entry.relative_path}: {error}",
        ) from error

    _validate_entry_provenance(entry, artifact)
    return artifact


def _validate_entry_provenance(
    entry: SyntheticTraceFixtureManifestEntry,
    artifact: SyntheticTraceRuntimeInput | SyntheticTraceExpectedOutcomes,
) -> None:
    """Reject artifacts that do not carry the exact manifest-declared identity."""

    if (
        artifact.case_id != entry.case_id
        or artifact.split is not entry.split
        or artifact.data_role is not entry.data_role
        or artifact.source_type is not entry.source_type
    ):
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_PROVENANCE_MISMATCH,
            f"artifact provenance does not match manifest entry for {entry.relative_path}",
        )


def _resolve_artifact_path(root: Path, relative_path: str) -> Path:
    """Resolve a manifest path while preventing reads outside the fixture root."""

    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_MANIFEST_MISMATCH,
            f"manifest path escapes fixture root: {relative_path}",
        ) from error
    return candidate


def _read_json(path: Path, code: TraceFixtureViolationCode) -> Any:
    """Read JSON with a typed failure that preserves the local-only boundary."""

    raw_bytes = _read_bytes(path, code)
    try:
        return json.loads(raw_bytes)
    except json.JSONDecodeError as error:
        raise SyntheticTraceFixtureLoadError(
            TraceFixtureViolationCode.TRACE_SCHEMA_ERROR,
            f"invalid JSON in {path.name}: {error.msg}",
        ) from error


def _read_bytes(
    path: Path,
    code: TraceFixtureViolationCode = TraceFixtureViolationCode.TRACE_MANIFEST_MISMATCH,
) -> bytes:
    """Read local fixture bytes without silently falling back on missing artifacts."""

    try:
        return path.read_bytes()
    except OSError as error:
        raise SyntheticTraceFixtureLoadError(
            code,
            f"unable to read fixture artifact: {path}",
        ) from error
