"""Immutable V2 final-evaluation manifest generation and verification.

This module freezes the complete quarantined V2 final corpus after all three reserved
held-out families exist. It validates bytes, provenance, and split isolation only. It
does not load the bounded-Platt artifact, transform confidences, calculate metrics, or
make a promotion decision.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract, TraceDataRole, TraceSourceType, TraceSplit
from specsafe.traces.calibration_redesign_v2 import (
    CalibrationRedesignV2RegistryLoadError,
    CalibrationRedesignV2ScenarioFamilyRegistry,
    assert_calibration_redesign_v2_final_evaluation_manifest_fixture_root,
    load_calibration_redesign_v2_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v2_cases import (
    CalibrationRedesignV2CaseContractError,
    CalibrationRedesignV2ReplayCase,
    load_calibration_redesign_v2_replay_case,
)

_FINAL_MANIFEST_FILENAME = "final_evaluation_manifest.json"
_REGISTRY_FILENAME = "scenario_family_registry.json"
_FINAL_SPLIT = TraceSplit.FINAL_EVALUATION
_FINAL_DATA_ROLE = TraceDataRole.HELD_OUT_EVALUATION


class CalibrationRedesignV2FinalManifestViolationCode(StrEnum):
    """Machine-readable reasons the V2 final corpus cannot be trusted."""

    MANIFEST_SCHEMA_ERROR = "calibration_redesign_v2_final_manifest_schema_error"
    MANIFEST_INTEGRITY_MISMATCH = "calibration_redesign_v2_final_manifest_integrity_mismatch"
    MANIFEST_PROVENANCE_MISMATCH = "calibration_redesign_v2_final_manifest_provenance_mismatch"
    FINAL_EVALUATION_BOUNDARY_VIOLATION = (
        "calibration_redesign_v2_final_manifest_boundary_violation"
    )


class CalibrationRedesignV2FinalManifestLoadError(ValueError):
    """Typed error raised when the quarantined V2 final inventory is invalid."""

    def __init__(
        self,
        code: CalibrationRedesignV2FinalManifestViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV2FinalManifestArtifactKind(StrEnum):
    """The two physically separate assets required for each held-out V2 case."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOMES = "expected_outcomes"


class CalibrationRedesignV2FinalManifestEntry(StrictContract):
    """Hash-addressed inventory entry for one quarantined V2 final asset."""

    artifact_kind: CalibrationRedesignV2FinalManifestArtifactKind
    relative_path: str = Field(min_length=1, max_length=300)
    case_id: str = Field(pattern=r"^CRV2-2[0-9]{2}$")
    scenario_family_id: str = Field(pattern=r"^CRV2-FINAL-[A-Z0-9-]+$")
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    is_final_evaluation_quarantined: Literal[True]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_asset_path(self) -> CalibrationRedesignV2FinalManifestEntry:
        """Require a fixed case-kind path that cannot escape the fixture root."""

        expected_directory = {
            CalibrationRedesignV2FinalManifestArtifactKind.RUNTIME_INPUT: "inputs/cases",
            CalibrationRedesignV2FinalManifestArtifactKind.EXPECTED_OUTCOMES: (
                "expected_outcomes/cases"
            ),
        }[self.artifact_kind]
        expected_path = f"{expected_directory}/{self.case_id}.json"
        if self.relative_path.replace("\\", "/") != expected_path:
            raise ValueError("manifest entry path must match its case ID and artifact kind")
        return self


class CalibrationRedesignV2FinalSplitCount(StrictContract):
    """Declared case count for the single quarantined final-evaluation split."""

    split: Literal[TraceSplit.FINAL_EVALUATION]
    case_count: int = Field(ge=1)


class CalibrationRedesignV2FinalScenarioFamilyCount(StrictContract):
    """Declared held-out case count for one finalized V2 final family."""

    scenario_family_id: str = Field(pattern=r"^CRV2-FINAL-[A-Z0-9-]+$")
    case_count: int = Field(ge=1)


class CalibrationRedesignV2FinalEvaluationFixtureManifest(StrictContract):
    """Immutable, hash-addressed inventory for the V2 held-out evaluation corpus."""

    schema_version: Literal["calibration-redesign-v2-final-evaluation-manifest-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    authoring_protocol_version: Literal["calibration-redesign-v2-entry-protocol-v1"]
    candidate_artifact_id: Literal["bounded-platt-scaling-v1"]
    scenario_family_registry_path: Literal["scenario_family_registry.json"]
    scenario_family_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_family_registry_byte_count: int = Field(gt=0)
    case_count: int = Field(ge=1)
    observation_count: int = Field(ge=1)
    minimum_required_observation_count: int = Field(ge=1)
    split_counts: tuple[CalibrationRedesignV2FinalSplitCount, ...] = Field(min_length=1)
    scenario_family_counts: tuple[CalibrationRedesignV2FinalScenarioFamilyCount, ...] = Field(
        min_length=1
    )
    entries: tuple[CalibrationRedesignV2FinalManifestEntry, ...] = Field(min_length=2)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_inventory_shape(self) -> CalibrationRedesignV2FinalEvaluationFixtureManifest:
        """Require complete paired held-out evidence and an auditable observation floor."""

        entry_keys = {(entry.case_id, entry.artifact_kind) for entry in self.entries}
        if len(entry_keys) != len(self.entries):
            raise ValueError("manifest entries must not repeat a case_id/artifact_kind pair")

        case_ids = {entry.case_id for entry in self.entries}
        if len(case_ids) != self.case_count:
            raise ValueError("case_count must equal the number of unique manifest case IDs")
        required_kinds = {
            CalibrationRedesignV2FinalManifestArtifactKind.RUNTIME_INPUT,
            CalibrationRedesignV2FinalManifestArtifactKind.EXPECTED_OUTCOMES,
        }
        for case_id in case_ids:
            kinds = {entry.artifact_kind for entry in self.entries if entry.case_id == case_id}
            if kinds != required_kinds:
                raise ValueError("each V2 final case needs one runtime and one outcome asset")

        if len(self.split_counts) != 1 or self.split_counts[0].case_count != self.case_count:
            raise ValueError("V2 final manifest must declare one matching final split count")
        if self.observation_count < self.minimum_required_observation_count:
            raise ValueError("V2 final observations do not meet the declared minimum")

        family_counts = {
            item.scenario_family_id: item.case_count for item in self.scenario_family_counts
        }
        if len(family_counts) != len(self.scenario_family_counts):
            raise ValueError("scenario_family_counts must not repeat a family")
        actual_family_counts: dict[str, int] = defaultdict(int)
        for case_id in case_ids:
            family_ids = {
                entry.scenario_family_id for entry in self.entries if entry.case_id == case_id
            }
            if len(family_ids) != 1:
                raise ValueError("runtime and outcome entries must agree on scenario family")
            actual_family_counts[family_ids.pop()] += 1
        if dict(actual_family_counts) != family_counts:
            raise ValueError("scenario_family_counts must match manifest case families")
        return self


class CalibrationRedesignV2FinalManifestedFixtureSet(StrictContract):
    """Final V2 cases loaded only after manifest, asset, and registry verification."""

    manifest: CalibrationRedesignV2FinalEvaluationFixtureManifest
    cases: tuple[CalibrationRedesignV2ReplayCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_identity(self) -> CalibrationRedesignV2FinalManifestedFixtureSet:
        """Require each final manifest case to load exactly once after verification."""

        case_ids = {case.runtime_input.case_id for case in self.cases}
        if len(case_ids) != len(self.cases):
            raise ValueError("loaded V2 final cases must have unique case IDs")
        if len(case_ids) != self.manifest.case_count:
            raise ValueError("loaded V2 final case count must match the manifest")
        observation_count = sum(len(case.runtime_input.contexts) for case in self.cases)
        if observation_count != self.manifest.observation_count:
            raise ValueError("loaded V2 final observations must match the manifest")
        return self


def build_calibration_redesign_v2_final_evaluation_manifest(fixture_root: Path) -> Path:
    """Freeze the complete authored V2 held-out corpus into a deterministic manifest."""

    root = fixture_root.resolve()
    _assert_final_manifest_root(root)
    registry_path = root / _REGISTRY_FILENAME
    registry = _load_registry(registry_path)
    runtime_paths = _discover_final_case_assets(root / "inputs" / "cases")
    outcome_paths = _discover_final_case_assets(root / "expected_outcomes" / "cases")
    expected_case_ids = _expected_final_case_ids(registry)
    _validate_case_inventory(runtime_paths, outcome_paths, expected_case_ids)

    entries: list[CalibrationRedesignV2FinalManifestEntry] = []
    family_counts: dict[str, int] = defaultdict(int)
    observation_count = 0
    for case_id in sorted(expected_case_ids):
        replay_case = _load_replay_case(root, case_id)
        runtime = replay_case.runtime_input
        _validate_final_case(replay_case, registry)
        entries.extend(
            (
                _manifest_entry(
                    root,
                    runtime_paths[case_id],
                    CalibrationRedesignV2FinalManifestArtifactKind.RUNTIME_INPUT,
                    replay_case,
                ),
                _manifest_entry(
                    root,
                    outcome_paths[case_id],
                    CalibrationRedesignV2FinalManifestArtifactKind.EXPECTED_OUTCOMES,
                    replay_case,
                ),
            )
        )
        family_counts[runtime.scenario_family_id] += 1
        observation_count += len(runtime.contexts)

    registry_bytes = _read_bytes(registry_path)
    manifest_without_aggregate: dict[str, Any] = {
        "schema_version": "calibration-redesign-v2-final-evaluation-manifest-v1",
        "fixture_set_id": registry.fixture_set_id,
        "fixture_set_version": registry.fixture_set_version,
        "source_type": TraceSourceType.SYNTHETIC.value,
        "authoring_protocol_version": registry.authoring_protocol_version,
        "candidate_artifact_id": registry.candidate_artifact_id,
        "scenario_family_registry_path": _REGISTRY_FILENAME,
        "scenario_family_registry_sha256": _sha256(registry_bytes),
        "scenario_family_registry_byte_count": len(registry_bytes),
        "case_count": len(expected_case_ids),
        "observation_count": observation_count,
        "minimum_required_observation_count": (
            registry.observation_budget.minimum_final_evaluation_observation_count
        ),
        "split_counts": [
            {"split": TraceSplit.FINAL_EVALUATION.value, "case_count": len(expected_case_ids)}
        ],
        "scenario_family_counts": [
            {"scenario_family_id": family_id, "case_count": family_counts[family_id]}
            for family_id in sorted(family_counts)
        ],
        "entries": [
            entry.model_dump(mode="json") for entry in sorted(entries, key=_entry_sort_key)
        ],
    }
    manifest_payload = {
        **manifest_without_aggregate,
        "aggregate_sha256": _aggregate_sha256(manifest_without_aggregate),
    }
    try:
        CalibrationRedesignV2FinalEvaluationFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"generated V2 final manifest schema validation failed: {error}",
        ) from error

    manifest_path = root / _FINAL_MANIFEST_FILENAME
    manifest_path.write_bytes(_pretty_json_bytes(manifest_payload))
    return manifest_path


def load_calibration_redesign_v2_final_evaluation_manifested_fixture_set(
    fixture_root: Path,
) -> CalibrationRedesignV2FinalManifestedFixtureSet:
    """Load the frozen V2 final corpus without fitting, scoring, or promoting anything."""

    root = fixture_root.resolve()
    _assert_final_manifest_root(root)
    manifest_path = root / _FINAL_MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V2 final-evaluation manifest is missing",
        )
    manifest_payload = _read_json(manifest_path)
    try:
        manifest = CalibrationRedesignV2FinalEvaluationFixtureManifest.model_validate(
            manifest_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V2 final manifest schema validation failed: {error}",
        ) from error

    aggregate_payload = dict(manifest_payload)
    declared_aggregate = aggregate_payload.pop("aggregate_sha256", None)
    if declared_aggregate != _aggregate_sha256(aggregate_payload):
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "V2 final manifest aggregate hash does not match its inventory",
        )

    registry_path = _resolve_path(root, manifest.scenario_family_registry_path)
    registry_bytes = _read_bytes(registry_path)
    if (
        _sha256(registry_bytes) != manifest.scenario_family_registry_sha256
        or len(registry_bytes) != manifest.scenario_family_registry_byte_count
    ):
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "V2 scenario-family registry does not match final-manifest provenance",
        )
    registry = _load_registry(registry_path)
    _validate_manifest_registry_identity(manifest, registry)

    runtime_paths = _discover_final_case_assets(root / "inputs" / "cases")
    outcome_paths = _discover_final_case_assets(root / "expected_outcomes" / "cases")
    expected_case_ids = _expected_final_case_ids(registry)
    _validate_case_inventory(runtime_paths, outcome_paths, expected_case_ids)

    entries_by_case: dict[
        str,
        dict[
            CalibrationRedesignV2FinalManifestArtifactKind,
            CalibrationRedesignV2FinalManifestEntry,
        ],
    ] = defaultdict(dict)
    for entry in manifest.entries:
        _verify_entry_bytes(root, entry)
        entries_by_case[entry.case_id][entry.artifact_kind] = entry
    if set(entries_by_case) != expected_case_ids:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V2 final manifest case IDs must match the finalized held-out reservation",
        )

    cases: list[CalibrationRedesignV2ReplayCase] = []
    for case_id in sorted(expected_case_ids):
        entries = entries_by_case[case_id]
        runtime_entry = entries.get(CalibrationRedesignV2FinalManifestArtifactKind.RUNTIME_INPUT)
        outcome_entry = entries.get(
            CalibrationRedesignV2FinalManifestArtifactKind.EXPECTED_OUTCOMES
        )
        if runtime_entry is None or outcome_entry is None:
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V2 final manifest is missing one asset entry for {case_id}",
            )
        replay_case = _load_replay_case(root, case_id)
        _validate_final_case(replay_case, registry)
        if replay_case.runtime_input.scenario_family_id != runtime_entry.scenario_family_id:
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V2 final manifest family does not match runtime case for {case_id}",
            )
        cases.append(replay_case)

    try:
        return CalibrationRedesignV2FinalManifestedFixtureSet(manifest=manifest, cases=tuple(cases))
    except ValidationError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"loaded V2 final fixture set does not match its manifest: {error}",
        ) from error


def _assert_final_manifest_root(root: Path) -> None:
    try:
        assert_calibration_redesign_v2_final_evaluation_manifest_fixture_root(root)
    except CalibrationRedesignV2RegistryLoadError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
            f"V2 final-manifest root is not authorized: {error}",
        ) from error


def _load_registry(registry_path: Path) -> CalibrationRedesignV2ScenarioFamilyRegistry:
    try:
        return load_calibration_redesign_v2_scenario_family_registry(
            registry_path,
            allow_final_evaluation_manifest=True,
        )
    except CalibrationRedesignV2RegistryLoadError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to load finalized V2 registry for final manifest: {error}",
        ) from error


def _load_replay_case(root: Path, case_id: str) -> CalibrationRedesignV2ReplayCase:
    try:
        return load_calibration_redesign_v2_replay_case(root, case_id)
    except CalibrationRedesignV2CaseContractError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V2 final case {case_id} cannot be loaded: {error}",
        ) from error


def _discover_final_case_assets(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V2 final asset directory is missing: {directory}",
        )
    assets: dict[str, Path] = {}
    for path in sorted(directory.glob("CRV2-2*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"V2 final asset must contain a JSON object: {path.name}",
            )
        if (
            payload.get("split") != _FINAL_SPLIT.value
            or payload.get("data_role") != _FINAL_DATA_ROLE.value
        ):
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
                f"non-final asset is prohibited in the V2 final manifest: {path.name}",
            )
        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or path.name != f"{case_id}.json":
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"V2 final asset filename and case_id must agree: {path.name}",
            )
        if case_id in assets:
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"duplicate V2 final case ID in one asset directory: {case_id}",
            )
        assets[case_id] = path
    if not assets:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V2 final asset directory contains no case JSON: {directory}",
        )
    return assets


def _expected_final_case_ids(registry: CalibrationRedesignV2ScenarioFamilyRegistry) -> set[str]:
    return {
        case_id
        for family in registry.families
        if family.split is _FINAL_SPLIT
        for case_id in family.case_ids
    }


def _validate_case_inventory(
    runtime_paths: dict[str, Path],
    outcome_paths: dict[str, Path],
    expected_case_ids: set[str],
) -> None:
    if set(runtime_paths) != set(outcome_paths):
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V2 final runtime and expected-outcome case IDs must match",
        )
    if set(runtime_paths) != expected_case_ids:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V2 final assets must match exactly the finalized held-out case reservation",
        )


def _validate_final_case(
    replay_case: CalibrationRedesignV2ReplayCase,
    registry: CalibrationRedesignV2ScenarioFamilyRegistry,
) -> None:
    runtime = replay_case.runtime_input
    is_final_case = runtime.split is _FINAL_SPLIT and runtime.data_role is _FINAL_DATA_ROLE
    if not is_final_case:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
            f"V2 manifest case {runtime.case_id} is not held-out final-evaluation evidence",
        )
    family = next(
        (
            item
            for item in registry.families
            if item.scenario_family_id == runtime.scenario_family_id
        ),
        None,
    )
    if family is None or not family.is_final_evaluation_quarantined:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V2 manifest case {runtime.case_id} is not in a quarantined final family",
        )
    if runtime.case_id not in _expected_final_case_ids(registry):
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V2 manifest case {runtime.case_id} is not reserved for final evaluation",
        )


def _manifest_entry(
    root: Path,
    path: Path,
    artifact_kind: CalibrationRedesignV2FinalManifestArtifactKind,
    replay_case: CalibrationRedesignV2ReplayCase,
) -> CalibrationRedesignV2FinalManifestEntry:
    raw_bytes = _read_bytes(path)
    runtime = replay_case.runtime_input
    return CalibrationRedesignV2FinalManifestEntry(
        artifact_kind=artifact_kind,
        relative_path=path.resolve().relative_to(root).as_posix(),
        case_id=runtime.case_id,
        scenario_family_id=runtime.scenario_family_id,
        split=runtime.split,
        data_role=runtime.data_role,
        source_type=runtime.source_type,
        is_final_evaluation_quarantined=True,
        sha256=_sha256(raw_bytes),
        byte_count=len(raw_bytes),
    )


def _validate_manifest_registry_identity(
    manifest: CalibrationRedesignV2FinalEvaluationFixtureManifest,
    registry: CalibrationRedesignV2ScenarioFamilyRegistry,
) -> None:
    for field_name in (
        "fixture_set_id",
        "fixture_set_version",
        "source_type",
        "authoring_protocol_version",
        "candidate_artifact_id",
    ):
        if getattr(manifest, field_name) != getattr(registry, field_name):
            raise CalibrationRedesignV2FinalManifestLoadError(
                CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V2 final manifest disagrees with registry on {field_name}",
            )
    if (
        manifest.minimum_required_observation_count
        != registry.observation_budget.minimum_final_evaluation_observation_count
    ):
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V2 final manifest observation floor disagrees with finalized registry",
        )


def _verify_entry_bytes(root: Path, entry: CalibrationRedesignV2FinalManifestEntry) -> None:
    raw_bytes = _read_bytes(_resolve_path(root, entry.relative_path))
    if _sha256(raw_bytes) != entry.sha256 or len(raw_bytes) != entry.byte_count:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            f"V2 final manifest entry does not match current bytes: {entry.relative_path}",
        )


def _resolve_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V2 final manifest path escapes fixture root: {relative_path}",
        ) from error
    return candidate


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read_bytes(path))
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"invalid JSON in {path.name}: {error.msg}",
        ) from error


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV2FinalManifestLoadError(
            CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to read V2 final fixture asset: {path}",
        ) from error


def _entry_sort_key(entry: CalibrationRedesignV2FinalManifestEntry) -> tuple[str, str]:
    return (entry.case_id, entry.artifact_kind.value)


def _sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def _aggregate_sha256(payload: dict[str, Any]) -> str:
    return _sha256(_canonical_json_bytes(payload))


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pretty_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")
