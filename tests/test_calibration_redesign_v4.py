"""Tests for the V4 schema-only evidence reservation boundary."""

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
    assert_calibration_redesign_v4_schema_only_fixture_root,
    load_calibration_redesign_v4_scenario_family_registry,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_complete_v4_schema_only_reservation() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(_REGISTRY_PATH)

    assert registry.registry_status == "schema_only"
    assert registry.fixture_set_id == "synthetic-calibration-redesign-v4"
    assert registry.observation_budget.calibration_case_count == 48
    assert registry.observation_budget.final_evaluation_case_count == 36
    assert registry.observation_budget.adversarial_regression_case_count == 12
    assert registry.v4_runtime_or_outcome_assets_authored is False
    assert registry.v4_manifests_authored is False
    assert registry.next_authorized_artifact == "v4-calibration-curve-coverage-fixtures"


def test_registry_reserves_exact_split_and_position_budgets() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(_REGISTRY_PATH)

    split_counts = {}
    for family in registry.families:
        split = family.split.value
        split_counts[split] = split_counts.get(split, 0) + len(family.reserved_case_ids)

    assert split_counts["calibration"] == 48
    assert split_counts["final_evaluation"] == 36
    assert split_counts["adversarial_regression"] == 12
    assert registry.observation_budget.final_evaluation_observation_count == 144
    assert registry.observation_budget.candidate_positions_per_case == 4


def test_final_families_reserve_balanced_workloads_and_remain_quarantined() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(_REGISTRY_PATH)
    final_families = [
        family
        for family in registry.families
        if family.split.value == "final_evaluation"
    ]

    assert len(final_families) == 4
    assert all(len(family.reserved_case_ids) == 9 for family in final_families)
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)
    assert all(
        family.workload_allocation.structured_text_case_count == 3
        and family.workload_allocation.code_case_count == 3
        and family.workload_allocation.open_ended_chat_case_count == 3
        for family in final_families
        if family.workload_allocation is not None
    )


def test_schema_only_root_rejects_case_bearing_directories(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "inputs").mkdir()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_schema_only_fixture_root(root)

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION
    )


def test_schema_only_root_rejects_unknown_root_asset(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "calibration_manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_schema_only_fixture_root(root)

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION
    )


def test_schema_only_root_rejects_closed_case_namespace_reference(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    manifest_path = root / "PROPOSAL_MANIFEST.md"
    manifest_path.write_text("reference CRV3-201\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_schema_only_fixture_root(root)

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.CLOSED_EVIDENCE_REFERENCE
    )


def test_registry_rejects_any_claim_that_case_assets_or_manifests_exist() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["v4_runtime_or_outcome_assets_authored"] = True

    with pytest.raises(ValidationError) as error:
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
    assert "v4_runtime_or_outcome_assets_authored" in str(error.value)

    payload["v4_runtime_or_outcome_assets_authored"] = False
    payload["v4_manifests_authored"] = True
    with pytest.raises(ValidationError) as error:
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
    assert "v4_manifests_authored" in str(error.value)


def test_registry_rejects_altered_reserved_case_range() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["families"][0]["reserved_case_ids"][0] = "CRV4-999"

    with pytest.raises(ValidationError, match="reservation ranges"):
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
