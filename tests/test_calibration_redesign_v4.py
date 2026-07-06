"""Tests for the V4 final-evaluation manifest-freeze registry boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    CalibrationRedesignV4RegistryViolationCode,
    CalibrationRedesignV4ScenarioFamilyRegistry,
    assert_calibration_redesign_v4_final_evaluation_manifest_fixture_root,
    load_calibration_redesign_v4_scenario_family_registry,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"
_FINAL_MANIFEST_PATH = _FIXTURE_ROOT / "final_evaluation_manifest.json"
_FINAL_INDEX_PATH = _FIXTURE_ROOT / "final_evidence_index.json"
_VIOLATION_CODE = CalibrationRedesignV4RegistryViolationCode


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_final_manifest_registry_only_through_active_boundary() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(
        _REGISTRY_PATH,
        allow_final_evaluation_manifest_assets=True,
    )

    assert registry.registry_status == "final_evaluation_manifest_frozen"
    assert registry.v4_final_evaluation_manifest_authored is True
    assert (
        registry.next_authorized_artifact == "v4-final-heldout-calibration-assessment"
    )
    assert (
        registry.frozen_final_evaluation_manifest_sha256
        == hashlib.sha256(_FINAL_MANIFEST_PATH.read_bytes()).hexdigest()
    )
    assert (
        registry.final_evidence_index_sha256
        == hashlib.sha256(_FINAL_INDEX_PATH.read_bytes()).hexdigest()
    )
    assert (
        registry.frozen_final_evaluation_registry_sha256
        != hashlib.sha256(_REGISTRY_PATH.read_bytes()).hexdigest()
    )


def test_current_root_rejects_previous_final_authoring_loader_path() -> None:
    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        load_calibration_redesign_v4_scenario_family_registry(
            _REGISTRY_PATH,
            allow_final_evaluation_fixture_assets=True,
        )

    expected_code = (
        _VIOLATION_CODE.FINAL_EVALUATION_FIXTURE_AUTHORING_BOUNDARY_VIOLATION
    )
    assert error.value.code is expected_code


def test_final_manifest_boundary_requires_complete_provenance_files(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "final_evidence_index.json").unlink()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_final_evaluation_manifest_fixture_root(root)

    expected_code = _VIOLATION_CODE.FINAL_EVALUATION_MANIFEST_BOUNDARY_VIOLATION
    assert error.value.code is expected_code


def test_final_manifest_boundary_rejects_adversarial_paths(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "adversarial_regression").mkdir()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_final_evaluation_manifest_fixture_root(root)

    expected_code = _VIOLATION_CODE.FINAL_EVALUATION_MANIFEST_BOUNDARY_VIOLATION
    assert error.value.code is expected_code


def test_registry_retains_exact_split_counts_and_final_manifest_state() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(
        _REGISTRY_PATH,
        allow_final_evaluation_manifest_assets=True,
    )

    split_counts: dict[str, int] = {}
    for family in registry.families:
        split_counts[family.split.value] = split_counts.get(
            family.split.value, 0
        ) + len(family.reserved_case_ids)

    assert split_counts == {
        "calibration": 48,
        "final_evaluation": 36,
        "adversarial_regression": 12,
    }
    final_families = [
        family
        for family in registry.families
        if family.split.value == "final_evaluation"
    ]
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)
    assert all(
        family.authoring_status == "final_evaluation_fixtures_authored"
        for family in final_families
    )


def test_registry_rejects_false_claim_that_final_manifest_is_not_frozen() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["v4_final_evaluation_manifest_authored"] = False

    with pytest.raises(ValidationError):
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
