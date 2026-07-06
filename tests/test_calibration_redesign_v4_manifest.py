"""Tests for deterministic V4 calibration-manifest freeze behavior."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v4_manifest import (
    CalibrationRedesignV4ManifestError,
    CalibrationRedesignV4ManifestViolationCode,
    build_calibration_redesign_v4_calibration_manifest,
    load_calibration_redesign_v4_calibration_manifest,
    write_calibration_redesign_v4_calibration_manifest,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(101, 149))


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_manifest_hash_verifies_exact_complete_calibration_inventory() -> None:
    manifest = load_calibration_redesign_v4_calibration_manifest(_FIXTURE_ROOT)

    assert manifest.case_ids == _CASE_IDS
    assert manifest.case_pair_count == 48
    assert manifest.asset_count == 96
    assert manifest.observation_count == 192
    assert len(manifest.assets) == 96
    assert len(manifest.case_pairs) == 48
    assert manifest.aggregate_byte_count == sum(
        asset.byte_count for asset in manifest.assets
    )
    assert manifest.assets[0].relative_path == "expected_outcomes/cases/CRV4-101.json"
    assert manifest.assets[-1].relative_path == "inputs/cases/CRV4-148.json"


def test_manifest_write_is_deterministic_and_write_once(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "calibration_manifest.json").unlink()

    first_manifest = write_calibration_redesign_v4_calibration_manifest(root)
    loaded_manifest = load_calibration_redesign_v4_calibration_manifest(root)

    assert loaded_manifest == first_manifest
    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        write_calibration_redesign_v4_calibration_manifest(root)

    assert (
        error.value.code
        is CalibrationRedesignV4ManifestViolationCode.DESTINATION_ALREADY_EXISTS
    )


def test_manifest_detects_one_byte_asset_change(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    runtime_path = root / "inputs" / "cases" / "CRV4-148.json"
    runtime_path.write_bytes(runtime_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        load_calibration_redesign_v4_calibration_manifest(root)

    assert (
        error.value.code
        is CalibrationRedesignV4ManifestViolationCode.ASSET_INTEGRITY_MISMATCH
    )


def test_manifest_detects_registry_provenance_change(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    registry_path = root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["explicit_exclusions"] = [*payload["explicit_exclusions"], "tampered"]
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        load_calibration_redesign_v4_calibration_manifest(root)

    assert (
        error.value.code
        is CalibrationRedesignV4ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH
    )


def test_build_refuses_to_rebuild_existing_manifest(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)

    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        build_calibration_redesign_v4_calibration_manifest(root)

    assert (
        error.value.code
        is CalibrationRedesignV4ManifestViolationCode.DESTINATION_ALREADY_EXISTS
    )
