"""Regression tests for the immutable V5 final-evaluation manifest freeze."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_successor_v5_final_manifest import (
    CalibrationSuccessorV5FinalManifestError,
    CalibrationSuccessorV5FinalManifestViolationCode,
    freeze_calibration_successor_v5_final_evaluation_manifest,
    load_calibration_successor_v5_final_manifested_fixture_set,
)

_PRE_MANIFEST_BLOCKED_EXCLUSION = (
    "No V5 final-evaluation manifest, held-out assessment, scheduler, baseline "
    "comparison, capacity profile, utility scorer, or runtime control is authorized."
)
_FINAL_MANIFEST_FROZEN_EXCLUSION = (
    "V5 final-evaluation manifest and final-evidence index are frozen provenance boundaries."
)
_FINAL_MANIFEST_NON_ASSESSMENT_EXCLUSION = (
    "V5 final-evaluation manifest freeze does not author an assessment, baseline, or policy result."
)
_FINAL_ASSESSMENT_BLOCKED_EXCLUSION = (
    "No V5 held-out assessment, scheduler, baseline comparison, capacity "
    "profile, utility scorer, or runtime control is authorized."
)

_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_successor_v5"
)


def _copy_root(tmp_path: Path) -> Path:
    target = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_ROOT, target)
    return target


def _restore_pre_freeze(root: Path) -> None:
    for filename in ("final_evaluation_manifest.json", "final_evidence_index.json"):
        (root / filename).unlink()
    path = root / "scenario_family_registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "registry_status": "final_mixed_reliability_contrast_authored",
            "v5_final_evaluation_manifest_authored": False,
            "frozen_final_evaluation_manifest_sha256": None,
            "frozen_final_evaluation_pre_freeze_registry_sha256": None,
            "final_evidence_index_sha256": None,
            "next_authorized_artifact": "v5-final-evaluation-manifest-freeze",
        }
    )
    obsolete = {
        _FINAL_MANIFEST_FROZEN_EXCLUSION,
        _FINAL_MANIFEST_NON_ASSESSMENT_EXCLUSION,
        _FINAL_ASSESSMENT_BLOCKED_EXCLUSION,
    }
    payload["explicit_exclusions"] = [
        item for item in payload["explicit_exclusions"] if item not in obsolete
    ]
    payload["explicit_exclusions"].append(_PRE_MANIFEST_BLOCKED_EXCLUSION)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_loads_complete_frozen_final_inventory() -> None:
    fixture_set = load_calibration_successor_v5_final_manifested_fixture_set(_ROOT)
    assert fixture_set.manifest.case_pair_count == 36
    assert fixture_set.manifest.asset_count == 72
    assert fixture_set.manifest.observation_count == 144
    assert len(fixture_set.index.entries) == 36
    assert len(fixture_set.cases) == 36
    assert fixture_set.manifest.case_ids[0] == "CSV5-201"
    assert fixture_set.manifest.case_ids[-1] == "CSV5-236"


def test_registry_carries_manifest_and_index_hashes() -> None:
    fixture_set = load_calibration_successor_v5_final_manifested_fixture_set(_ROOT)
    registry = json.loads((_ROOT / "scenario_family_registry.json").read_text(encoding="utf-8"))
    assert (
        registry["frozen_final_evaluation_manifest_sha256"]
        == hashlib.sha256((_ROOT / "final_evaluation_manifest.json").read_bytes()).hexdigest()
    )
    assert (
        registry["final_evidence_index_sha256"]
        == hashlib.sha256((_ROOT / "final_evidence_index.json").read_bytes()).hexdigest()
    )
    assert (
        fixture_set.manifest.final_evidence_index_sha256 == registry["final_evidence_index_sha256"]
    )


def test_detects_one_byte_final_asset_change(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    path = root / "final_evaluation" / "inputs" / "cases" / "CSV5-236.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(CalibrationSuccessorV5FinalManifestError) as error:
        load_calibration_successor_v5_final_manifested_fixture_set(root)
    assert (
        error.value.code
        is CalibrationSuccessorV5FinalManifestViolationCode.ASSET_INTEGRITY_MISMATCH
    )


def test_freeze_is_deterministic_and_write_once(tmp_path: Path) -> None:
    first = _copy_root(tmp_path / "first")
    second = _copy_root(tmp_path / "second")
    _restore_pre_freeze(first)
    _restore_pre_freeze(second)
    freeze_calibration_successor_v5_final_evaluation_manifest(first)
    freeze_calibration_successor_v5_final_evaluation_manifest(second)
    assert (first / "final_evaluation_manifest.json").read_bytes() == (
        second / "final_evaluation_manifest.json"
    ).read_bytes()
    assert (first / "final_evidence_index.json").read_bytes() == (
        second / "final_evidence_index.json"
    ).read_bytes()
    with pytest.raises(CalibrationSuccessorV5FinalManifestError) as error:
        freeze_calibration_successor_v5_final_evaluation_manifest(first)
    assert (
        error.value.code
        is CalibrationSuccessorV5FinalManifestViolationCode.DESTINATION_ALREADY_EXISTS
    )


def test_final_manifest_freeze_does_not_write_final_assessment(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    _restore_pre_freeze(root)
    freeze_calibration_successor_v5_final_evaluation_manifest(root)
    assert not (root / "final_assessment_result.json").exists()
    registry = json.loads((root / "scenario_family_registry.json").read_text(encoding="utf-8"))
    assert registry["v5_final_heldout_calibration_assessment_authored"] is False
    assert registry["next_authorized_artifact"] == "v5-final-heldout-calibration-assessment"
