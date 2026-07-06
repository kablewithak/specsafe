"""Regression tests for V4 final manifest and final evidence-index freeze controls."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v4_final_manifest import (
    CalibrationRedesignV4FinalManifestError,
    CalibrationRedesignV4FinalManifestViolationCode,
    freeze_calibration_redesign_v4_final_evaluation_manifest,
    load_calibration_redesign_v4_final_manifested_fixture_set,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(201, 237))


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def _restore_pre_freeze_registry(root: Path) -> None:
    registry_path = root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["registry_status"] = "final_evaluation_fixtures_authored"
    payload["v4_final_evaluation_manifest_authored"] = False
    payload["v4_final_heldout_calibration_assessment_authored"] = False
    payload["next_authorized_artifact"] = "v4-final-evaluation-manifest-freeze"
    for field_name in (
        "frozen_final_evaluation_registry_sha256",
        "frozen_final_evaluation_manifest_sha256",
        "final_evidence_index_sha256",
        "final_heldout_calibration_assessment_sha256",
        "final_heldout_calibration_assessment_relative_path",
        "final_heldout_calibration_status",
    ):
        payload.pop(field_name, None)
    obsolete = {
        "No V4 final-evaluation held-out assessment or result is present.",
        "V4 final-evaluation manifest and final-evidence index are frozen provenance boundaries.",
        (
            "V4 final-evaluation manifest freeze does not author an assessment, "
            "baseline, or policy result."
        ),
        "V4 held-out calibration assessment is write-once evidence.",
        "V4 held-out calibration evidence does not establish production performance.",
        "V4 policy, baseline, replay, and runtime-control work remain blocked pending remediation.",
        "V4 runtime control remains prohibited pending policy and baseline evidence.",
    }
    exclusions = [
        item for item in payload["explicit_exclusions"] if item not in obsolete
    ]
    exclusions.extend(
        (
            "No V4 final-evaluation manifest is present.",
            "No V4 final-evidence index or held-out result is present.",
            "V4 final-evaluation fixtures remain quarantined until their manifest is frozen.",
        )
    )
    payload["explicit_exclusions"] = exclusions
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (root / "final_evaluation_manifest.json").unlink()
    (root / "final_evidence_index.json").unlink()


def test_final_manifest_loads_complete_verified_heldout_inventory() -> None:
    fixture_set = load_calibration_redesign_v4_final_manifested_fixture_set(
        _FIXTURE_ROOT
    )

    assert fixture_set.manifest.case_ids == _CASE_IDS
    assert fixture_set.manifest.case_pair_count == 36
    assert fixture_set.manifest.asset_count == 72
    assert fixture_set.manifest.observation_count == 144
    assert fixture_set.index.case_count == 36
    assert len(fixture_set.index.entries) == 36
    assert len(fixture_set.cases) == 36
    assert fixture_set.manifest.aggregate_byte_count == sum(
        asset.byte_count for asset in fixture_set.manifest.assets
    )


def test_final_manifest_carry_forward_hashes_bind_active_stage_to_frozen_files() -> (
    None
):
    fixture_set = load_calibration_redesign_v4_final_manifested_fixture_set(
        _FIXTURE_ROOT
    )
    registry_payload = json.loads(
        (_FIXTURE_ROOT / "scenario_family_registry.json").read_text(encoding="utf-8")
    )

    assert (
        registry_payload["frozen_final_evaluation_manifest_sha256"]
        == hashlib.sha256(
            (_FIXTURE_ROOT / "final_evaluation_manifest.json").read_bytes()
        ).hexdigest()
    )
    assert (
        registry_payload["final_evidence_index_sha256"]
        == hashlib.sha256(
            (_FIXTURE_ROOT / "final_evidence_index.json").read_bytes()
        ).hexdigest()
    )
    assert (
        fixture_set.manifest.final_evidence_index_sha256
        == registry_payload["final_evidence_index_sha256"]
    )


def test_final_manifest_detects_one_byte_final_asset_change(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    runtime_path = root / "final_evaluation" / "inputs" / "cases" / "CRV4-236.json"
    runtime_path.write_bytes(runtime_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV4FinalManifestError) as error:
        load_calibration_redesign_v4_final_manifested_fixture_set(root)

    expected_code = (
        CalibrationRedesignV4FinalManifestViolationCode.ASSET_INTEGRITY_MISMATCH
    )
    assert error.value.code is expected_code


def test_final_manifest_detects_changed_index_bytes(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    index_path = root / "final_evidence_index.json"
    index_path.write_bytes(index_path.read_bytes() + b" ")

    with pytest.raises(CalibrationRedesignV4FinalManifestError) as error:
        load_calibration_redesign_v4_final_manifested_fixture_set(root)

    expected_code = (
        CalibrationRedesignV4FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH
    )
    assert error.value.code is expected_code


def test_final_manifest_freeze_is_deterministic_and_write_once(tmp_path: Path) -> None:
    first_root = _copy_fixture_root(tmp_path / "first")
    second_root = _copy_fixture_root(tmp_path / "second")
    _restore_pre_freeze_registry(first_root)
    _restore_pre_freeze_registry(second_root)

    freeze_calibration_redesign_v4_final_evaluation_manifest(first_root)
    freeze_calibration_redesign_v4_final_evaluation_manifest(second_root)

    assert (first_root / "final_evaluation_manifest.json").read_bytes() == (
        second_root / "final_evaluation_manifest.json"
    ).read_bytes()
    assert (first_root / "final_evidence_index.json").read_bytes() == (
        second_root / "final_evidence_index.json"
    ).read_bytes()

    with pytest.raises(CalibrationRedesignV4FinalManifestError) as error:
        freeze_calibration_redesign_v4_final_evaluation_manifest(first_root)

    expected_code = (
        CalibrationRedesignV4FinalManifestViolationCode.DESTINATION_ALREADY_EXISTS
    )
    assert error.value.code is expected_code
