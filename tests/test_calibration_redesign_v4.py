"""Tests for the V4 completed calibration-authoring boundary."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    CalibrationRedesignV4RegistryViolationCode,
    CalibrationRedesignV4ScenarioFamilyRegistry,
    assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root,
    load_calibration_redesign_v4_scenario_family_registry,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v4"
)
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"

_V4_REGISTRY_VIOLATION_CODE = CalibrationRedesignV4RegistryViolationCode


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_completed_v4_calibration_authoring_only_through_active_boundary() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_capacity_contrast_assets=True,
    )

    assert registry.registry_status == "calibration_capacity_contrast_authored"
    assert registry.v4_runtime_or_outcome_assets_authored is True
    assert registry.v4_manifests_authored is False
    assert registry.next_authorized_artifact == "v4-calibration-manifest-freeze"
    statuses = {family.scenario_family_id: family.authoring_status for family in registry.families}
    assert statuses == {
        "CRV4-CAL-CURVE-COVERAGE": "calibration_curve_coverage_authored",
        "CRV4-CAL-POSITION-SPREAD": "calibration_position_spread_authored",
        "CRV4-CAL-WORKLOAD-MIX": "calibration_workload_mix_authored",
        "CRV4-CAL-CAPACITY-CONTRAST": "calibration_capacity_contrast_authored",
        "CRV4-FINAL-LIGHT-CAPACITY": "reserved_for_v4_case_authoring",
        "CRV4-FINAL-MODERATE-CAPACITY": "reserved_for_v4_case_authoring",
        "CRV4-FINAL-SATURATED-CAPACITY": "reserved_for_v4_case_authoring",
        "CRV4-FINAL-JAGGED-CAPACITY": "reserved_for_v4_case_authoring",
        "CRV4-ADV-CAUSAL-GUARD": "reserved_for_v4_case_authoring",
        "CRV4-ADV-PROVENANCE-GATE": "reserved_for_v4_case_authoring",
    }


def test_current_root_rejects_previous_workload_mix_loader_path() -> None:
    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        load_calibration_redesign_v4_scenario_family_registry(
            _REGISTRY_PATH,
            allow_calibration_workload_mix_assets=True,
        )

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.CALIBRATION_WORKLOAD_MIX_BOUNDARY_VIOLATION
    )


def test_capacity_contrast_boundary_requires_complete_inventory(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "inputs" / "cases" / "CRV4-148.json").unlink()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root(root)

    expected_code = _V4_REGISTRY_VIOLATION_CODE.CALIBRATION_CAPACITY_CONTRAST_BOUNDARY_VIOLATION
    assert error.value.code is expected_code


def test_capacity_contrast_boundary_rejects_final_or_adversarial_paths(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "final_evaluation").mkdir()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root(root)

    expected_code = _V4_REGISTRY_VIOLATION_CODE.CALIBRATION_CAPACITY_CONTRAST_BOUNDARY_VIOLATION
    assert error.value.code is expected_code


def test_registry_retains_exact_split_counts_and_final_quarantine() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_capacity_contrast_assets=True,
    )

    split_counts: dict[str, int] = {}
    for family in registry.families:
        split_counts[family.split.value] = split_counts.get(
            family.split.value,
            0,
        ) + len(family.reserved_case_ids)

    assert split_counts == {
        "calibration": 48,
        "final_evaluation": 36,
        "adversarial_regression": 12,
    }
    final_families = [
        family for family in registry.families if family.split.value == "final_evaluation"
    ]
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)


def test_registry_rejects_false_claim_that_manifests_exist() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["v4_manifests_authored"] = True

    with pytest.raises(ValidationError):
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
