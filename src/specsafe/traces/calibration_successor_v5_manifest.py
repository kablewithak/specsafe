"""Immutable manifest freeze and integrity checks for the complete V5 calibration corpus.

This module freezes the 48 calibration-only V5 case pairs after all authoring families are
complete. It does not fit the bounded monotone-beta calibrator, author final-evaluation assets,
or execute a held-out assessment.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    assert_calibration_successor_v5_calibration_mixed_reliability_contrast_fixture_root,
    load_calibration_successor_v5_scenario_family_registry,
)

_MANIFEST_FILENAME = "calibration_manifest.json"
_MANIFEST_SCHEMA_VERSION = "calibration-successor-v5-manifest-v1"
_MANIFEST_ID = "v5-calibration-manifest-freeze"
_FIXTURE_SET_ID = "synthetic-calibration-successor-v5"
_FIXTURE_SET_VERSION = "1.0.0"
_METHOD_CONSTITUTION_VERSION = "v5-bounded-monotone-beta-calibration-eligibility-charter-v1"
_CALIBRATION_METHOD_ID = "bounded-monotone-beta-calibration-v5"
_EXPECTED_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(101, 149))
_EXPECTED_CASE_COUNT = 48
_EXPECTED_ASSET_COUNT = 96
_EXPECTED_OBSERVATION_COUNT = 192
_FROZEN_BOUNDARY_EXCLUSION = (
    "V5 calibration manifest is frozen and hash-addressed; final-evaluation "
    "and adversarial reservations remain quarantined."
)
_NO_MANIFEST_EXCLUSION = "No V5 calibration or final-evaluation manifest is present."


class CalibrationSuccessorV5ManifestViolationCode(StrEnum):
    """Machine-readable reasons a V5 calibration manifest is not trustworthy."""

    DESTINATION_ALREADY_EXISTS = "calibration_successor_v5_manifest_destination_exists"
    DESTINATION_WRITE_ERROR = "calibration_successor_v5_manifest_destination_write_error"
    MANIFEST_READ_ERROR = "calibration_successor_v5_manifest_read_error"
    MANIFEST_SCHEMA_ERROR = "calibration_successor_v5_manifest_schema_error"
    PRE_FREEZE_ROOT_INVALID = "calibration_successor_v5_manifest_pre_freeze_root_invalid"
    FINAL_ROOT_INVALID = "calibration_successor_v5_manifest_final_root_invalid"
    REGISTRY_PROVENANCE_MISMATCH = "calibration_successor_v5_manifest_registry_provenance_mismatch"
    INVENTORY_MISMATCH = "calibration_successor_v5_manifest_inventory_mismatch"
    ASSET_INTEGRITY_MISMATCH = "calibration_successor_v5_manifest_asset_integrity_mismatch"
    AGGREGATE_MISMATCH = "calibration_successor_v5_manifest_aggregate_mismatch"


class CalibrationSuccessorV5ManifestError(ValueError):
    """Raised when the V5 calibration-manifest freeze cannot be trusted."""

    def __init__(
        self,
        code: CalibrationSuccessorV5ManifestViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationSuccessorV5ManifestAsset(StrictContract):
    """One immutable file record inside the V5 calibration-only corpus."""

    relative_path: str = Field(pattern=r"^(inputs|expected_outcomes)/cases/CSV5-[0-9]{3}\.json$")
    case_id: str = Field(pattern=r"^CSV5-[0-9]{3}$")
    asset_kind: Literal["runtime_input", "expected_outcome"]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_path_and_kind(self) -> CalibrationSuccessorV5ManifestAsset:
        expected_parent = (
            "inputs/cases" if self.asset_kind == "runtime_input" else "expected_outcomes/cases"
        )
        if self.relative_path != f"{expected_parent}/{self.case_id}.json":
            raise ValueError(
                "V5 calibration manifest asset path must match its declared case and kind"
            )
        return self


class CalibrationSuccessorV5ManifestCasePair(StrictContract):
    """The two separately retained evidence halves for one V5 calibration replay case."""

    case_id: str = Field(pattern=r"^CSV5-[0-9]{3}$")
    runtime_input_relative_path: str = Field(pattern=r"^inputs/cases/CSV5-[0-9]{3}\.json$")
    expected_outcome_relative_path: str = Field(
        pattern=r"^expected_outcomes/cases/CSV5-[0-9]{3}\.json$"
    )
    runtime_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_outcome_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_case_pair_paths(self) -> CalibrationSuccessorV5ManifestCasePair:
        if self.runtime_input_relative_path != f"inputs/cases/{self.case_id}.json":
            raise ValueError("V5 runtime-input pair path does not match its case ID")
        if self.expected_outcome_relative_path != (f"expected_outcomes/cases/{self.case_id}.json"):
            raise ValueError("V5 expected-outcome pair path does not match its case ID")
        return self


class CalibrationSuccessorV5CalibrationManifest(StrictContract):
    """Frozen deterministic provenance for all 48 V5 calibration-only case pairs."""

    schema_version: Literal["calibration-successor-v5-manifest-v1"] = _MANIFEST_SCHEMA_VERSION
    manifest_id: Literal["v5-calibration-manifest-freeze"] = _MANIFEST_ID
    manifest_scope: Literal["calibration_only"] = "calibration_only"
    fixture_set_id: Literal["synthetic-calibration-successor-v5"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    method_constitution_version: Literal[
        "v5-bounded-monotone-beta-calibration-eligibility-charter-v1"
    ] = _METHOD_CONSTITUTION_VERSION
    calibration_method_id: Literal["bounded-monotone-beta-calibration-v5"] = _CALIBRATION_METHOD_ID
    pre_freeze_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_ids: tuple[str, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )
    case_pair_count: Literal[48] = _EXPECTED_CASE_COUNT
    asset_count: Literal[96] = _EXPECTED_ASSET_COUNT
    observation_count: Literal[192] = _EXPECTED_OBSERVATION_COUNT
    aggregate_byte_count: int = Field(ge=1)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assets: tuple[CalibrationSuccessorV5ManifestAsset, ...] = Field(
        min_length=_EXPECTED_ASSET_COUNT,
        max_length=_EXPECTED_ASSET_COUNT,
    )
    case_pairs: tuple[CalibrationSuccessorV5ManifestCasePair, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )

    @model_validator(mode="after")
    def validate_manifest_shape(self) -> CalibrationSuccessorV5CalibrationManifest:
        if self.case_ids != _EXPECTED_CASE_IDS:
            raise ValueError("V5 calibration manifest case IDs must be CSV5-101 through CSV5-148")
        expected_paths = tuple(
            sorted(
                (
                    *(f"inputs/cases/{case_id}.json" for case_id in _EXPECTED_CASE_IDS),
                    *(f"expected_outcomes/cases/{case_id}.json" for case_id in _EXPECTED_CASE_IDS),
                )
            )
        )
        if tuple(asset.relative_path for asset in self.assets) != expected_paths:
            raise ValueError(
                "V5 calibration manifest assets must be complete and sorted by relative path"
            )
        if tuple(pair.case_id for pair in self.case_pairs) != _EXPECTED_CASE_IDS:
            raise ValueError(
                "V5 calibration manifest case pairs must be complete and sorted by case ID"
            )
        if self.aggregate_byte_count != sum(asset.byte_count for asset in self.assets):
            raise ValueError(
                "V5 calibration manifest aggregate byte count must match asset records"
            )
        return self


def build_calibration_successor_v5_calibration_manifest(
    root: Path,
) -> CalibrationSuccessorV5CalibrationManifest:
    """Build one deterministic manifest from a complete, pre-freeze V5 fixture root."""

    resolved_root = root.resolve()
    destination = resolved_root / _MANIFEST_FILENAME
    if destination.exists():
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            "V5 calibration manifest already exists and must not be rebuilt in place",
        )
    try:
        assert_calibration_successor_v5_calibration_mixed_reliability_contrast_fixture_root(
            resolved_root
        )
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_calibration_mixed_reliability_contrast_assets=True,
        )
    except CalibrationSuccessorV5RegistryLoadError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V5 calibration manifest requires a complete pre-freeze root: {error}",
        ) from error
    return _build_manifest_from_root(resolved_root, registry)


def freeze_calibration_successor_v5_calibration_manifest(
    root: Path,
) -> CalibrationSuccessorV5CalibrationManifest:
    """Write the manifest once and advance registry metadata to the frozen stage."""

    resolved_root = root.resolve()
    manifest = build_calibration_successor_v5_calibration_manifest(resolved_root)
    final_registry_payload = _build_frozen_registry_payload(
        registry=load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_calibration_mixed_reliability_contrast_assets=True,
        ),
        manifest=manifest,
    )
    try:
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(final_registry_payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V5 frozen registry payload is invalid: {error}",
        ) from error

    manifest_path = resolved_root / _MANIFEST_FILENAME
    try:
        with manifest_path.open("xb") as file_handle:
            file_handle.write(_manifest_file_bytes(manifest))
    except FileExistsError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            "V5 calibration manifest already exists and must not be overwritten",
        ) from error
    except OSError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.DESTINATION_WRITE_ERROR,
            f"unable to write V5 calibration manifest: {error}",
        ) from error

    registry_path = resolved_root / "scenario_family_registry.json"
    try:
        registry_path.write_bytes(_canonical_json_file_bytes(final_registry_payload))
    except OSError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.DESTINATION_WRITE_ERROR,
            f"unable to advance V5 registry after manifest freeze: {error}",
        ) from error
    return manifest


def load_calibration_successor_v5_calibration_manifest(
    root: Path,
) -> CalibrationSuccessorV5CalibrationManifest:
    """Load and hash-verify the frozen V5 calibration manifest and all named assets."""

    resolved_root = root.resolve()
    fit_artifact_names = {
        "bounded_monotone_beta_calibration_artifact.json",
        "bounded_monotone_beta_calibration_fit_diagnostics.json",
    }
    present_names = {child.name for child in resolved_root.iterdir()}
    if present_names & fit_artifact_names and not fit_artifact_names.issubset(present_names):
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.FINAL_ROOT_INVALID,
            "V5 fit-stage root must retain both artifact and diagnostics files together",
        )
    final_evaluation_present = "final_evaluation" in present_names
    final_manifest_present = "final_evaluation_manifest.json" in present_names
    fit_diagnostics_present = fit_artifact_names.issubset(present_names)
    try:
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=final_manifest_present,
            allow_final_mixed_reliability_contrast_assets=(
                final_evaluation_present and not final_manifest_present
            ),
            allow_calibration_fit_diagnostics_assets=(
                fit_diagnostics_present and not final_evaluation_present
            ),
            allow_calibration_manifest_assets=(
                not fit_diagnostics_present and not final_evaluation_present
            ),
        )
    except CalibrationSuccessorV5RegistryLoadError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.FINAL_ROOT_INVALID,
            f"V5 calibration manifest root is not authorised: {error}",
        ) from error

    manifest_path = resolved_root / _MANIFEST_FILENAME
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.MANIFEST_READ_ERROR,
            f"unable to read V5 calibration manifest: {error}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V5 calibration manifest is not valid JSON: {error}",
        ) from error
    try:
        manifest = CalibrationSuccessorV5CalibrationManifest.model_validate(payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V5 calibration manifest validation failed: {error}",
        ) from error
    _verify_manifest_against_root(resolved_root, manifest, registry)
    return manifest


def _build_manifest_from_root(
    root: Path,
    registry: CalibrationSuccessorV5ScenarioFamilyRegistry,
) -> CalibrationSuccessorV5CalibrationManifest:
    assets = _collect_asset_records(root)
    assets_by_path = {asset.relative_path: asset for asset in assets}
    return CalibrationSuccessorV5CalibrationManifest(
        pre_freeze_registry_sha256=_sha256(root / "scenario_family_registry.json"),
        case_ids=_EXPECTED_CASE_IDS,
        aggregate_byte_count=sum(asset.byte_count for asset in assets),
        aggregate_sha256=_aggregate_sha256(assets),
        assets=assets,
        case_pairs=tuple(
            CalibrationSuccessorV5ManifestCasePair(
                case_id=case_id,
                runtime_input_relative_path=f"inputs/cases/{case_id}.json",
                expected_outcome_relative_path=(f"expected_outcomes/cases/{case_id}.json"),
                runtime_input_sha256=assets_by_path[f"inputs/cases/{case_id}.json"].sha256,
                expected_outcome_sha256=assets_by_path[
                    f"expected_outcomes/cases/{case_id}.json"
                ].sha256,
            )
            for case_id in _EXPECTED_CASE_IDS
        ),
    )


def _build_frozen_registry_payload(
    *,
    registry: CalibrationSuccessorV5ScenarioFamilyRegistry,
    manifest: CalibrationSuccessorV5CalibrationManifest,
) -> dict[str, object]:
    payload = registry.model_dump(mode="json")
    exclusions = [item for item in payload["explicit_exclusions"] if item != _NO_MANIFEST_EXCLUSION]
    exclusions.append(_FROZEN_BOUNDARY_EXCLUSION)
    payload.update(
        {
            "registry_status": "calibration_manifest_frozen",
            "v5_calibration_manifest_authored": True,
            "frozen_calibration_manifest_sha256": hashlib.sha256(
                _manifest_file_bytes(manifest)
            ).hexdigest(),
            "frozen_calibration_pre_freeze_registry_sha256": (manifest.pre_freeze_registry_sha256),
            "explicit_exclusions": exclusions,
            "next_authorized_artifact": "v5-bounded-monotone-beta-fit-diagnostics",
        }
    )
    return payload


def _verify_manifest_against_root(
    root: Path,
    manifest: CalibrationSuccessorV5CalibrationManifest,
    registry: CalibrationSuccessorV5ScenarioFamilyRegistry,
) -> None:
    if (
        registry.frozen_calibration_pre_freeze_registry_sha256
        != manifest.pre_freeze_registry_sha256
    ):
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 frozen registry does not carry the manifest pre-freeze registry SHA-256",
        )
    if registry.frozen_calibration_manifest_sha256 != _sha256(root / _MANIFEST_FILENAME):
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 frozen registry does not carry the immutable manifest SHA-256",
        )
    actual_assets = _collect_asset_records(root)
    if manifest.assets != actual_assets:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.ASSET_INTEGRITY_MISMATCH,
            "V5 calibration manifest asset hashes or byte counts do not match the fixture root",
        )
    if manifest.aggregate_byte_count != sum(asset.byte_count for asset in actual_assets):
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.INVENTORY_MISMATCH,
            "V5 calibration manifest aggregate byte count does not match the fixture root",
        )
    if manifest.aggregate_sha256 != _aggregate_sha256(actual_assets):
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.AGGREGATE_MISMATCH,
            "V5 calibration manifest aggregate SHA-256 does not match the fixture root",
        )


def _collect_asset_records(root: Path) -> tuple[CalibrationSuccessorV5ManifestAsset, ...]:
    assets: list[CalibrationSuccessorV5ManifestAsset] = []
    for case_id in _EXPECTED_CASE_IDS:
        assets.extend(
            (
                _asset_record(
                    root,
                    relative_path=f"inputs/cases/{case_id}.json",
                    case_id=case_id,
                    asset_kind="runtime_input",
                ),
                _asset_record(
                    root,
                    relative_path=f"expected_outcomes/cases/{case_id}.json",
                    case_id=case_id,
                    asset_kind="expected_outcome",
                ),
            )
        )
    return tuple(sorted(assets, key=lambda asset: asset.relative_path))


def _asset_record(
    root: Path,
    *,
    relative_path: str,
    case_id: str,
    asset_kind: Literal["runtime_input", "expected_outcome"],
) -> CalibrationSuccessorV5ManifestAsset:
    path = root / relative_path
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.INVENTORY_MISMATCH,
            f"unable to read V5 calibration asset {relative_path}: {error}",
        ) from error
    return CalibrationSuccessorV5ManifestAsset(
        relative_path=relative_path,
        case_id=case_id,
        asset_kind=asset_kind,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        byte_count=len(raw_bytes),
    )


def _aggregate_sha256(assets: tuple[CalibrationSuccessorV5ManifestAsset, ...]) -> str:
    payload = [asset.model_dump(mode="json") for asset in assets]
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _sha256(path: Path) -> str:
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationSuccessorV5ManifestError(
            CalibrationSuccessorV5ManifestViolationCode.MANIFEST_READ_ERROR,
            f"unable to read V5 manifest provenance input {path.name}: {error}",
        ) from error
    return hashlib.sha256(raw_bytes).hexdigest()


def _manifest_file_bytes(manifest: CalibrationSuccessorV5CalibrationManifest) -> bytes:
    return _canonical_json_file_bytes(manifest.model_dump(mode="json"))


def _canonical_json_file_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
