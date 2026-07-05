"""Immutable V3 calibration-manifest generation and verification.

The manifest freezes the completed 36-case V3 calibration corpus before
``quantile-isotonic-calibration-v1`` is fitted. It never reads V3 final-evaluation
or adversarial-regression assets and never makes policy or promotion decisions.
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
from specsafe.traces.calibration_redesign_v3 import (
    CalibrationRedesignV3RegistryLoadError,
    CalibrationRedesignV3ScenarioFamilyRegistry,
    assert_calibration_redesign_v3_calibration_manifest_fixture_root,
    load_calibration_redesign_v3_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v3_cases import (
    CalibrationRedesignV3CaseContractError,
    CalibrationRedesignV3ReplayCase,
    load_calibration_redesign_v3_replay_case,
)

_MANIFEST_FILENAME = "calibration_manifest.json"
_REGISTRY_FILENAME = "scenario_family_registry.json"
_CALIBRATION_CASE_COUNT = 36
_CALIBRATION_OBSERVATION_COUNT = 144
_CALIBRATION_QUANTILE_GROUP_COUNT = 8
_EXPECTED_FAMILY_CASE_COUNTS = {
    "CRV3-CAL-CURVE-COVERAGE": 12,
    "CRV3-CAL-POSITION-SPREAD": 12,
    "CRV3-CAL-WORKLOAD-MIX": 12,
}


class CalibrationRedesignV3CalibrationManifestViolationCode(StrEnum):
    """Machine-readable reasons the frozen V3 calibration corpus is invalid."""

    MANIFEST_SCHEMA_ERROR = "calibration_redesign_v3_calibration_manifest_schema_error"
    MANIFEST_INTEGRITY_MISMATCH = "calibration_redesign_v3_calibration_manifest_integrity_mismatch"
    MANIFEST_PROVENANCE_MISMATCH = (
        "calibration_redesign_v3_calibration_manifest_provenance_mismatch"
    )
    CALIBRATION_BOUNDARY_VIOLATION = (
        "calibration_redesign_v3_calibration_manifest_boundary_violation"
    )


class CalibrationRedesignV3CalibrationManifestLoadError(ValueError):
    """Typed error raised when V3 calibration evidence cannot be trusted."""

    def __init__(
        self,
        code: CalibrationRedesignV3CalibrationManifestViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV3CalibrationManifestArtifactKind(StrEnum):
    """The two separate evidence assets required for every V3 calibration case."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOMES = "expected_outcomes"


class CalibrationRedesignV3CalibrationManifestEntry(StrictContract):
    """Hash-addressed inventory entry for one calibration evidence asset."""

    artifact_kind: CalibrationRedesignV3CalibrationManifestArtifactKind
    relative_path: str = Field(min_length=1, max_length=300)
    case_id: str = Field(pattern=r"^CRV3-1[0-9]{2}$")
    scenario_family_id: Literal[
        "CRV3-CAL-CURVE-COVERAGE",
        "CRV3-CAL-POSITION-SPREAD",
        "CRV3-CAL-WORKLOAD-MIX",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_asset_path(self) -> CalibrationRedesignV3CalibrationManifestEntry:
        """Require a case-kind-specific path contained by the fixture root."""

        expected_directory = {
            CalibrationRedesignV3CalibrationManifestArtifactKind.RUNTIME_INPUT: "inputs/cases",
            CalibrationRedesignV3CalibrationManifestArtifactKind.EXPECTED_OUTCOMES: (
                "expected_outcomes/cases"
            ),
        }[self.artifact_kind]
        expected_path = f"{expected_directory}/{self.case_id}.json"
        if self.relative_path.replace("\\", "/") != expected_path:
            raise ValueError("manifest entry path must match its case ID and artifact kind")
        return self


class CalibrationRedesignV3CalibrationSplitCount(StrictContract):
    """The only split permitted in this manifest."""

    split: Literal[TraceSplit.CALIBRATION]
    case_count: Literal[36]


class CalibrationRedesignV3CalibrationScenarioFamilyCount(StrictContract):
    """Declared V3 calibration-case count for one authorised family."""

    scenario_family_id: Literal[
        "CRV3-CAL-CURVE-COVERAGE",
        "CRV3-CAL-POSITION-SPREAD",
        "CRV3-CAL-WORKLOAD-MIX",
    ]
    case_count: Literal[12]


class CalibrationRedesignV3CalibrationFixtureManifest(StrictContract):
    """Immutable V3 calibration inventory before any fitter may run."""

    schema_version: Literal["calibration-redesign-v3-calibration-manifest-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    method_constitution_version: Literal["v3-method-and-evidence-constitution-v1"]
    calibration_method_id: Literal["quantile-isotonic-calibration-v1"]
    adaptive_policy_id: Literal["causal-marginal-prefix-v1"]
    scenario_family_registry_path: Literal["scenario_family_registry.json"]
    scenario_family_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_family_registry_byte_count: int = Field(gt=0)
    case_count: Literal[36]
    observation_count: Literal[144]
    calibration_quantile_group_count: Literal[8]
    split_counts: tuple[CalibrationRedesignV3CalibrationSplitCount, ...] = Field(min_length=1)
    scenario_family_counts: tuple[CalibrationRedesignV3CalibrationScenarioFamilyCount, ...] = Field(
        min_length=3,
        max_length=3,
    )
    entries: tuple[CalibrationRedesignV3CalibrationManifestEntry, ...] = Field(min_length=72)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_inventory_shape(self) -> CalibrationRedesignV3CalibrationFixtureManifest:
        """Require complete paired evidence across the full frozen calibration corpus."""

        entry_keys = {(entry.case_id, entry.artifact_kind) for entry in self.entries}
        if len(entry_keys) != len(self.entries):
            raise ValueError("manifest entries must not repeat a case_id/artifact_kind pair")
        if len(self.entries) != _CALIBRATION_CASE_COUNT * 2:
            raise ValueError("V3 calibration manifest must contain exactly 72 paired asset entries")

        case_ids = {entry.case_id for entry in self.entries}
        if len(case_ids) != self.case_count:
            raise ValueError("case_count must equal the number of unique manifest case IDs")
        for case_id in case_ids:
            kinds = {entry.artifact_kind for entry in self.entries if entry.case_id == case_id}
            if kinds != {
                CalibrationRedesignV3CalibrationManifestArtifactKind.RUNTIME_INPUT,
                CalibrationRedesignV3CalibrationManifestArtifactKind.EXPECTED_OUTCOMES,
            }:
                raise ValueError("each V3 calibration case needs one runtime and one outcome asset")

        if len(self.split_counts) != 1 or self.split_counts[0].case_count != self.case_count:
            raise ValueError("V3 calibration manifest must declare exactly one calibration split")

        family_counts = {
            item.scenario_family_id: item.case_count for item in self.scenario_family_counts
        }
        if family_counts != _EXPECTED_FAMILY_CASE_COUNTS:
            raise ValueError("scenario_family_counts must match the three fixed V3 families")

        actual_family_counts: dict[str, int] = defaultdict(int)
        for case_id in case_ids:
            family_ids = {
                entry.scenario_family_id for entry in self.entries if entry.case_id == case_id
            }
            if len(family_ids) != 1:
                raise ValueError("runtime and outcome entries must agree on scenario family")
            actual_family_counts[family_ids.pop()] += 1
        if dict(actual_family_counts) != _EXPECTED_FAMILY_CASE_COUNTS:
            raise ValueError("manifest case inventory must match the fixed V3 family allocation")
        return self


class CalibrationRedesignV3CalibrationManifestedFixtureSet(StrictContract):
    """Verified V3 calibration cases loaded only after manifest integrity checks."""

    manifest: CalibrationRedesignV3CalibrationFixtureManifest
    cases: tuple[CalibrationRedesignV3ReplayCase, ...] = Field(min_length=36, max_length=36)

    @model_validator(mode="after")
    def validate_case_identity(self) -> CalibrationRedesignV3CalibrationManifestedFixtureSet:
        """Require every frozen case exactly once and all 144 observations."""

        case_ids = {case.runtime_input.case_id for case in self.cases}
        if len(case_ids) != len(self.cases):
            raise ValueError("loaded V3 calibration cases must have unique case IDs")
        if len(case_ids) != self.manifest.case_count:
            raise ValueError("loaded V3 calibration case count must match the manifest")
        observation_count = sum(len(case.runtime_input.contexts) for case in self.cases)
        if observation_count != self.manifest.observation_count:
            raise ValueError("loaded V3 calibration observations must match the manifest")
        return self


def build_calibration_redesign_v3_calibration_manifest(fixture_root: Path) -> Path:
    """Freeze the complete V3 calibration corpus into deterministic JSON bytes."""

    root = fixture_root.resolve()
    _assert_calibration_manifest_root(root)
    registry_path = root / _REGISTRY_FILENAME
    registry = _load_registry(registry_path)
    runtime_paths = _discover_calibration_case_assets(root / "inputs" / "cases")
    outcome_paths = _discover_calibration_case_assets(root / "expected_outcomes" / "cases")
    expected_case_ids = _expected_calibration_case_ids(registry)
    _validate_case_inventory(runtime_paths, outcome_paths, expected_case_ids)

    entries: list[CalibrationRedesignV3CalibrationManifestEntry] = []
    family_counts: dict[str, int] = defaultdict(int)
    observation_count = 0
    for case_id in sorted(expected_case_ids):
        replay_case = _load_replay_case(root, case_id)
        runtime = replay_case.runtime_input
        _validate_calibration_case(replay_case, registry)
        entries.extend(
            (
                _manifest_entry(
                    root,
                    runtime_paths[case_id],
                    CalibrationRedesignV3CalibrationManifestArtifactKind.RUNTIME_INPUT,
                    replay_case,
                ),
                _manifest_entry(
                    root,
                    outcome_paths[case_id],
                    CalibrationRedesignV3CalibrationManifestArtifactKind.EXPECTED_OUTCOMES,
                    replay_case,
                ),
            )
        )
        family_counts[runtime.scenario_family_id] += 1
        observation_count += len(runtime.contexts)

    registry_bytes = _read_bytes(registry_path)
    manifest_without_aggregate: dict[str, Any] = {
        "schema_version": "calibration-redesign-v3-calibration-manifest-v1",
        "fixture_set_id": registry.fixture_set_id,
        "fixture_set_version": registry.fixture_set_version,
        "source_type": TraceSourceType.SYNTHETIC.value,
        "method_constitution_version": registry.method_constitution_version,
        "calibration_method_id": registry.calibration_method_id,
        "adaptive_policy_id": registry.adaptive_policy_id,
        "scenario_family_registry_path": _REGISTRY_FILENAME,
        "scenario_family_registry_sha256": _sha256(registry_bytes),
        "scenario_family_registry_byte_count": len(registry_bytes),
        "case_count": len(expected_case_ids),
        "observation_count": observation_count,
        "calibration_quantile_group_count": (
            registry.observation_budget.calibration_quantile_group_count
        ),
        "split_counts": [
            {"split": TraceSplit.CALIBRATION.value, "case_count": len(expected_case_ids)}
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
        CalibrationRedesignV3CalibrationFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"generated V3 calibration manifest schema validation failed: {error}",
        ) from error

    manifest_path = root / _MANIFEST_FILENAME
    manifest_path.write_bytes(_pretty_json_bytes(manifest_payload))
    return manifest_path


def load_calibration_redesign_v3_calibration_manifested_fixture_set(
    fixture_root: Path,
) -> CalibrationRedesignV3CalibrationManifestedFixtureSet:
    """Load the frozen V3 calibration corpus without touching held-out material."""

    root = fixture_root.resolve()
    _assert_calibration_manifest_root(root)
    manifest_path = root / _MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 calibration manifest is missing",
        )
    manifest_payload = _read_json(manifest_path)
    try:
        manifest = CalibrationRedesignV3CalibrationFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V3 calibration manifest schema validation failed: {error}",
        ) from error

    aggregate_payload = dict(manifest_payload)
    declared_aggregate = aggregate_payload.pop("aggregate_sha256", None)
    if declared_aggregate != _aggregate_sha256(aggregate_payload):
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "V3 calibration manifest aggregate hash does not match its inventory",
        )

    registry_path = _resolve_path(root, manifest.scenario_family_registry_path)
    registry_bytes = _read_bytes(registry_path)
    if (
        _sha256(registry_bytes) != manifest.scenario_family_registry_sha256
        or len(registry_bytes) != manifest.scenario_family_registry_byte_count
    ):
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "V3 scenario-family registry does not match calibration-manifest provenance",
        )
    registry = _load_registry(registry_path)
    _validate_manifest_registry_identity(manifest, registry)

    runtime_paths = _discover_calibration_case_assets(root / "inputs" / "cases")
    outcome_paths = _discover_calibration_case_assets(root / "expected_outcomes" / "cases")
    expected_case_ids = _expected_calibration_case_ids(registry)
    _validate_case_inventory(runtime_paths, outcome_paths, expected_case_ids)

    entries_by_case: dict[
        str,
        dict[
            CalibrationRedesignV3CalibrationManifestArtifactKind,
            CalibrationRedesignV3CalibrationManifestEntry,
        ],
    ] = defaultdict(dict)
    for entry in manifest.entries:
        _verify_entry_bytes(root, entry)
        entries_by_case[entry.case_id][entry.artifact_kind] = entry
    if set(entries_by_case) != expected_case_ids:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 calibration manifest case IDs must match the fixed calibration reservation",
        )

    cases: list[CalibrationRedesignV3ReplayCase] = []
    for case_id in sorted(expected_case_ids):
        entries = entries_by_case[case_id]
        if (
            entries.get(CalibrationRedesignV3CalibrationManifestArtifactKind.RUNTIME_INPUT)
            is None
            or entries.get(CalibrationRedesignV3CalibrationManifestArtifactKind.EXPECTED_OUTCOMES)
            is None
        ):
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V3 calibration manifest is missing one asset entry for {case_id}",
            )
        replay_case = _load_replay_case(root, case_id)
        _validate_calibration_case(replay_case, registry)
        if replay_case.runtime_input.scenario_family_id != entries[
            CalibrationRedesignV3CalibrationManifestArtifactKind.RUNTIME_INPUT
        ].scenario_family_id:
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V3 calibration manifest family does not match runtime case for {case_id}",
            )
        cases.append(replay_case)

    try:
        return CalibrationRedesignV3CalibrationManifestedFixtureSet(
            manifest=manifest,
            cases=tuple(cases),
        )
    except ValidationError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"loaded V3 calibration fixture set does not match its manifest: {error}",
        ) from error


def _assert_calibration_manifest_root(root: Path) -> None:
    try:
        assert_calibration_redesign_v3_calibration_manifest_fixture_root(root)
    except CalibrationRedesignV3RegistryLoadError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.CALIBRATION_BOUNDARY_VIOLATION,
            f"V3 calibration-manifest root is not authorized: {error}",
        ) from error


def _load_registry(registry_path: Path) -> CalibrationRedesignV3ScenarioFamilyRegistry:
    try:
        return load_calibration_redesign_v3_scenario_family_registry(
            registry_path,
            allow_calibration_manifest_assets=True,
        )
    except CalibrationRedesignV3RegistryLoadError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to load V3 registry for calibration manifest: {error}",
        ) from error


def _load_replay_case(root: Path, case_id: str) -> CalibrationRedesignV3ReplayCase:
    try:
        return load_calibration_redesign_v3_replay_case(root, case_id)
    except CalibrationRedesignV3CaseContractError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 calibration case {case_id} cannot be loaded: {error}",
        ) from error


def _discover_calibration_case_assets(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 calibration asset directory is missing: {directory}",
        )
    assets: dict[str, Path] = {}
    for path in sorted(directory.glob("CRV3-*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"V3 calibration asset must contain a JSON object: {path.name}",
            )
        if (
            payload.get("split") != TraceSplit.CALIBRATION.value
            or payload.get("data_role") != TraceDataRole.CALIBRATION.value
        ):
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode
                .CALIBRATION_BOUNDARY_VIOLATION,
                f"non-calibration asset is prohibited in the V3 calibration manifest: {path.name}",
            )
        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or path.name != f"{case_id}.json":
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"V3 calibration asset filename and case_id must agree: {path.name}",
            )
        if case_id in assets:
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"duplicate V3 calibration case ID in one asset directory: {case_id}",
            )
        assets[case_id] = path
    if not assets:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 calibration asset directory contains no case JSON: {directory}",
        )
    return assets


def _expected_calibration_case_ids(
    registry: CalibrationRedesignV3ScenarioFamilyRegistry,
) -> set[str]:
    return {
        case_id
        for family in registry.families
        if family.split is TraceSplit.CALIBRATION
        for case_id in family.reserved_case_ids
    }


def _validate_case_inventory(
    runtime_paths: dict[str, Path],
    outcome_paths: dict[str, Path],
    expected_case_ids: set[str],
) -> None:
    if set(runtime_paths) != set(outcome_paths):
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 calibration runtime and expected-outcome case IDs must match",
        )
    if set(runtime_paths) != expected_case_ids:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 calibration assets must match exactly the fixed calibration reservation",
        )


def _validate_calibration_case(
    replay_case: CalibrationRedesignV3ReplayCase,
    registry: CalibrationRedesignV3ScenarioFamilyRegistry,
) -> None:
    runtime = replay_case.runtime_input
    if not (
        runtime.split is TraceSplit.CALIBRATION and runtime.data_role is TraceDataRole.CALIBRATION
    ):
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.CALIBRATION_BOUNDARY_VIOLATION,
            f"V3 manifest case {runtime.case_id} is not calibration-only",
        )
    if runtime.case_id not in _expected_calibration_case_ids(registry):
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 manifest case {runtime.case_id} is not reserved for calibration",
        )


def _manifest_entry(
    root: Path,
    path: Path,
    artifact_kind: CalibrationRedesignV3CalibrationManifestArtifactKind,
    replay_case: CalibrationRedesignV3ReplayCase,
) -> CalibrationRedesignV3CalibrationManifestEntry:
    raw_bytes = _read_bytes(path)
    runtime = replay_case.runtime_input
    return CalibrationRedesignV3CalibrationManifestEntry(
        artifact_kind=artifact_kind,
        relative_path=path.resolve().relative_to(root).as_posix(),
        case_id=runtime.case_id,
        scenario_family_id=runtime.scenario_family_id,
        split=runtime.split,
        data_role=runtime.data_role,
        source_type=runtime.source_type,
        sha256=_sha256(raw_bytes),
        byte_count=len(raw_bytes),
    )


def _validate_manifest_registry_identity(
    manifest: CalibrationRedesignV3CalibrationFixtureManifest,
    registry: CalibrationRedesignV3ScenarioFamilyRegistry,
) -> None:
    for field_name in (
        "fixture_set_id",
        "fixture_set_version",
        "source_type",
        "method_constitution_version",
        "calibration_method_id",
        "adaptive_policy_id",
    ):
        if getattr(manifest, field_name) != getattr(registry, field_name):
            raise CalibrationRedesignV3CalibrationManifestLoadError(
                CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V3 calibration manifest disagrees with registry on {field_name}",
            )
    if (
        manifest.calibration_quantile_group_count
        != registry.observation_budget.calibration_quantile_group_count
    ):
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 calibration manifest quantile-group count disagrees with registry",
        )


def _verify_entry_bytes(root: Path, entry: CalibrationRedesignV3CalibrationManifestEntry) -> None:
    raw_bytes = _read_bytes(_resolve_path(root, entry.relative_path))
    if _sha256(raw_bytes) != entry.sha256 or len(raw_bytes) != entry.byte_count:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            f"V3 calibration manifest entry does not match current bytes: {entry.relative_path}",
        )


def _resolve_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 calibration manifest path escapes fixture root: {relative_path}",
        ) from error
    return candidate


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read_bytes(path))
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"invalid JSON in {path.name}: {error.msg}",
        ) from error


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV3CalibrationManifestLoadError(
            CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to read V3 calibration fixture asset: {path}",
        ) from error


def _entry_sort_key(entry: CalibrationRedesignV3CalibrationManifestEntry) -> tuple[str, str]:
    return (entry.case_id, entry.artifact_kind.value)


def _sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def _aggregate_sha256(payload: dict[str, Any]) -> str:
    return _sha256(_canonical_json_bytes(payload))


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pretty_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")
