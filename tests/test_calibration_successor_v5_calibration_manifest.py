"""Integrity tests for the immutable V5 calibration-manifest freeze."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_successor_v5_manifest import (
    CalibrationSuccessorV5ManifestError,
    CalibrationSuccessorV5ManifestViolationCode,
    build_calibration_successor_v5_calibration_manifest,
    freeze_calibration_successor_v5_calibration_manifest,
    load_calibration_successor_v5_calibration_manifest,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"

_NO_MANIFEST_EXCLUSION = "No V5 calibration or final-evaluation manifest is present."
_FROZEN_EXCLUSION = (
    "V5 calibration manifest is frozen and hash-addressed; final-evaluation "
    "and adversarial reservations remain quarantined."
)


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def _restore_pre_freeze_root(root: Path) -> None:
    (root / "calibration_manifest.json").unlink()
    registry_path = root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload.update(
        {
            "registry_status": "calibration_mixed_reliability_contrast_authored",
            "v5_calibration_manifest_authored": False,
            "frozen_calibration_manifest_sha256": None,
            "frozen_calibration_pre_freeze_registry_sha256": None,
            "next_authorized_artifact": "v5-calibration-manifest-freeze",
        }
    )
    payload["explicit_exclusions"] = [
        exclusion for exclusion in payload["explicit_exclusions"] if exclusion != _FROZEN_EXCLUSION
    ]
    payload["explicit_exclusions"].append(_NO_MANIFEST_EXCLUSION)
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_loads_frozen_manifest_with_complete_inventory_and_provenance() -> None:
    manifest = load_calibration_successor_v5_calibration_manifest(_FIXTURE_ROOT)

    assert manifest.case_pair_count == 48
    assert manifest.asset_count == 96
    assert manifest.observation_count == 192
    assert len(manifest.assets) == 96
    assert len(manifest.case_pairs) == 48
    assert manifest.case_ids[0] == "CSV5-101"
    assert manifest.case_ids[-1] == "CSV5-148"


def test_frozen_manifest_assets_are_sorted_and_pair_complete() -> None:
    manifest = load_calibration_successor_v5_calibration_manifest(_FIXTURE_ROOT)

    assert tuple(asset.relative_path for asset in manifest.assets) == tuple(
        sorted(asset.relative_path for asset in manifest.assets)
    )
    assert all(
        pair.runtime_input_relative_path == f"inputs/cases/{pair.case_id}.json"
        for pair in manifest.case_pairs
    )
    assert all(
        pair.expected_outcome_relative_path == f"expected_outcomes/cases/{pair.case_id}.json"
        for pair in manifest.case_pairs
    )


def test_manifest_detects_one_tampered_calibration_asset(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    input_path = root / "inputs" / "cases" / "CSV5-101.json"
    input_path.write_text(input_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(CalibrationSuccessorV5ManifestError) as error:
        load_calibration_successor_v5_calibration_manifest(root)

    assert error.value.code is CalibrationSuccessorV5ManifestViolationCode.ASSET_INTEGRITY_MISMATCH


def test_manifest_detects_registry_manifest_hash_mismatch(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    registry_path = root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["frozen_calibration_manifest_sha256"] = "0" * 64
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CalibrationSuccessorV5ManifestError) as error:
        load_calibration_successor_v5_calibration_manifest(root)

    assert (
        error.value.code is CalibrationSuccessorV5ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH
    )


def test_freeze_writes_one_manifest_and_advances_registry_once(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    _restore_pre_freeze_root(root)

    manifest = freeze_calibration_successor_v5_calibration_manifest(root)
    loaded_manifest = load_calibration_successor_v5_calibration_manifest(root)
    registry = json.loads((root / "scenario_family_registry.json").read_text(encoding="utf-8"))

    assert manifest == loaded_manifest
    assert registry["registry_status"] == "calibration_manifest_frozen"
    assert registry["v5_calibration_manifest_authored"] is True
    assert registry["frozen_calibration_manifest_sha256"]
    assert registry["frozen_calibration_pre_freeze_registry_sha256"] == (
        manifest.pre_freeze_registry_sha256
    )


def test_freeze_rejects_an_existing_manifest_destination(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)

    with pytest.raises(CalibrationSuccessorV5ManifestError) as error:
        build_calibration_successor_v5_calibration_manifest(root)

    assert (
        error.value.code is CalibrationSuccessorV5ManifestViolationCode.DESTINATION_ALREADY_EXISTS
    )
