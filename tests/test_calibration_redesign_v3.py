from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v3 import (
    CalibrationRedesignV3RegistryLoadError,
    CalibrationRedesignV3RegistryViolationCode,
    assert_calibration_redesign_v3_calibration_curve_coverage_fixture_root,
    assert_calibration_redesign_v3_calibration_position_spread_fixture_root,
    assert_calibration_redesign_v3_calibration_workload_mix_fixture_root,
    assert_calibration_redesign_v3_schema_only_fixture_root,
    load_calibration_redesign_v3_scenario_family_registry,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
)


def _copy_workload_mix_root(tmp_path: Path) -> Path:
    destination = tmp_path / "synthetic_calibration_redesign_v3"
    shutil.copytree(FIXTURE_ROOT, destination)
    return destination


def _load_registry():
    return load_calibration_redesign_v3_scenario_family_registry(
        FIXTURE_ROOT / "scenario_family_registry.json",
        allow_calibration_workload_mix_assets=True,
    )


def test_v3_registry_loads_at_workload_mix_boundary() -> None:
    registry = _load_registry()

    assert registry.fixture_set_id == "synthetic-calibration-redesign-v3"
    assert registry.registry_status == "calibration_workload_mix_authored"
    assert registry.v1_or_v2_data_bearing_evidence_used is False
    assert registry.v3_runtime_or_outcome_assets_authored is True
    assert registry.v3_manifests_authored is False
    assert registry.next_authorized_artifact == "v3-calibration-manifest-authoring"
    assert registry.observation_budget.calibration_observation_count == 144
    assert registry.observation_budget.final_evaluation_observation_count == 96
    assert registry.observation_budget.adversarial_regression_observation_count == 32


def test_v3_workload_mix_root_is_exact_and_earlier_guards_reject_it() -> None:
    assert_calibration_redesign_v3_calibration_workload_mix_fixture_root(FIXTURE_ROOT)

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as position_error_info:
        assert_calibration_redesign_v3_calibration_position_spread_fixture_root(FIXTURE_ROOT)
    assert (
        position_error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION
    )

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as curve_error_info:
        assert_calibration_redesign_v3_calibration_curve_coverage_fixture_root(FIXTURE_ROOT)
    assert (
        curve_error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION
    )

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as schema_error_info:
        assert_calibration_redesign_v3_schema_only_fixture_root(FIXTURE_ROOT)
    assert (
        schema_error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION
    )


def test_v3_registry_reserves_exact_split_capacity_and_authored_calibration_shape() -> None:
    registry = _load_registry()

    case_count_by_split = {
        split.value: sum(
            len(family.reserved_case_ids)
            for family in registry.families
            if family.split.value == split.value
        )
        for split in {family.split for family in registry.families}
    }
    final_families = [
        family for family in registry.families if family.is_final_evaluation_quarantined
    ]
    curve_family = next(
        family
        for family in registry.families
        if family.scenario_family_id == "CRV3-CAL-CURVE-COVERAGE"
    )
    position_family = next(
        family
        for family in registry.families
        if family.scenario_family_id == "CRV3-CAL-POSITION-SPREAD"
    )
    workload_mix_family = next(
        family
        for family in registry.families
        if family.scenario_family_id == "CRV3-CAL-WORKLOAD-MIX"
    )

    assert case_count_by_split == {
        "calibration": 36,
        "final_evaluation": 24,
        "adversarial_regression": 8,
    }
    assert curve_family.authoring_status == "calibration_curve_coverage_authored"
    assert curve_family.reserved_case_ids == tuple(
        f"CRV3-{number:03d}" for number in range(101, 113)
    )
    assert position_family.authoring_status == "calibration_position_spread_authored"
    assert position_family.reserved_case_ids == tuple(
        f"CRV3-{number:03d}" for number in range(113, 125)
    )
    assert workload_mix_family.authoring_status == "calibration_workload_mix_authored"
    assert workload_mix_family.reserved_case_ids == tuple(
        f"CRV3-{number:03d}" for number in range(125, 137)
    )
    assert {family.scenario_family_id for family in final_families} == {
        "CRV3-FINAL-LIGHT-CAPACITY",
        "CRV3-FINAL-MODERATE-CAPACITY",
        "CRV3-FINAL-SATURATED-CAPACITY",
        "CRV3-FINAL-JAGGED-CAPACITY",
    }
    assert all(len(family.reserved_case_ids) == 6 for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)


def test_v3_workload_mix_root_rejects_final_case_bytes(tmp_path: Path) -> None:
    fixture_root = _copy_workload_mix_root(tmp_path)
    source = fixture_root / "inputs" / "cases" / "CRV3-125.json"
    (fixture_root / "inputs" / "cases" / "CRV3-201.json").write_bytes(source.read_bytes())

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        assert_calibration_redesign_v3_calibration_workload_mix_fixture_root(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.CALIBRATION_WORKLOAD_MIX_BOUNDARY_VIOLATION
    )


def test_v3_workload_mix_root_rejects_manifest(tmp_path: Path) -> None:
    fixture_root = _copy_workload_mix_root(tmp_path)
    (fixture_root / "calibration_manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        assert_calibration_redesign_v3_calibration_workload_mix_fixture_root(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.CALIBRATION_WORKLOAD_MIX_BOUNDARY_VIOLATION
    )


def test_v3_registry_rejects_closed_v2_reference(tmp_path: Path) -> None:
    fixture_root = _copy_workload_mix_root(tmp_path)
    registry_path = fixture_root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["explicit_exclusions"].append("CRV2-201 must not be read")
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        load_calibration_redesign_v3_scenario_family_registry(
            registry_path,
            allow_calibration_workload_mix_assets=True,
        )

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.V1_OR_V2_EVIDENCE_REFERENCE
    )


def test_v3_registry_rejects_changed_workload_mix_case_budget(tmp_path: Path) -> None:
    fixture_root = _copy_workload_mix_root(tmp_path)
    registry_path = fixture_root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    workload_mix_family = next(
        family
        for family in payload["families"]
        if family["scenario_family_id"] == "CRV3-CAL-WORKLOAD-MIX"
    )
    workload_mix_family["reserved_case_ids"] = workload_mix_family["reserved_case_ids"][:-1]
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        load_calibration_redesign_v3_scenario_family_registry(
            registry_path,
            allow_calibration_workload_mix_assets=True,
        )

    assert error_info.value.code is CalibrationRedesignV3RegistryViolationCode.REGISTRY_SCHEMA_ERROR


def test_v3_registry_rejects_multiple_selected_authoring_boundaries() -> None:
    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        load_calibration_redesign_v3_scenario_family_registry(
            FIXTURE_ROOT / "scenario_family_registry.json",
            allow_calibration_position_spread_assets=True,
            allow_calibration_workload_mix_assets=True,
        )

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH
    )
