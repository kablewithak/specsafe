"""Tests for V5 curve, position, and workload-variation evidence progression."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5RegistryViolationCode,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    assert_calibration_successor_v5_calibration_workload_variation_fixture_root,
    load_calibration_successor_v5_scenario_family_registry,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"


_POSITION_SPREAD_BOUNDARY_VIOLATION = (
    CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION
)
_WORKLOAD_VARIATION_BOUNDARY_VIOLATION = (
    CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_WORKLOAD_VARIATION_BOUNDARY_VIOLATION
)


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_the_v5_registry_only_through_workload_variation_boundary() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_workload_variation_assets=True,
    )

    assert registry.registry_status == "calibration_workload_variation_authored"
    assert registry.v5_runtime_or_outcome_assets_authored is True
    assert registry.v5_calibration_manifest_authored is False
    assert registry.v5_calibration_artifact_authored is False
    assert registry.v5_final_evaluation_runtime_or_outcome_assets_authored is False
    assert registry.next_authorized_artifact == "v5-calibration-mixed-reliability-contrast-fixtures"


def test_active_root_rejects_obsolete_position_spread_loader_path() -> None:
    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        load_calibration_successor_v5_scenario_family_registry(
            _REGISTRY_PATH,
            allow_calibration_position_spread_assets=True,
        )

    assert error.value.code is _POSITION_SPREAD_BOUNDARY_VIOLATION


def test_workload_variation_root_requires_exactly_thirty_six_case_pairs(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "inputs" / "cases" / "CSV5-136.json").unlink()

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_calibration_workload_variation_fixture_root(root)

    assert error.value.code is _WORKLOAD_VARIATION_BOUNDARY_VIOLATION


def test_workload_variation_root_rejects_a_manifest_or_final_path(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "calibration_manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_calibration_workload_variation_fixture_root(root)

    assert error.value.code is _WORKLOAD_VARIATION_BOUNDARY_VIOLATION


def test_registry_rejects_authored_status_outside_active_families() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["families"][3]["authoring_status"] = "calibration_workload_variation_authored"

    with pytest.raises(ValidationError):
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)


def test_registry_retains_final_and_adversarial_reservations_as_quarantined() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_workload_variation_assets=True,
    )
    final_families = [
        family for family in registry.families if family.split.value == "final_evaluation"
    ]
    adversarial_families = [
        family for family in registry.families if family.split.value == "adversarial_regression"
    ]

    assert all(
        family.authoring_status == "reserved_for_v5_case_authoring" for family in final_families
    )
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(
        family.authoring_status == "reserved_for_v5_case_authoring"
        for family in adversarial_families
    )
    assert all(family.is_adversarial_regression_quarantined for family in adversarial_families)
