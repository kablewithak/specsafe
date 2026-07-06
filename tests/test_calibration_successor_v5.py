"""Tests for V5 schema-only namespace and scenario-family reservations."""

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
    assert_calibration_successor_v5_schema_only_fixture_root,
    load_calibration_successor_v5_scenario_family_registry,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = (
    _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
)
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"
_VIOLATION_CODE = CalibrationSuccessorV5RegistryViolationCode


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_the_v5_schema_only_registry_through_the_governed_root() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(_REGISTRY_PATH)

    assert registry.registry_status == "schema_only"
    assert registry.v5_runtime_or_outcome_assets_authored is False
    assert registry.v5_calibration_manifest_authored is False
    assert registry.v5_calibration_artifact_authored is False
    assert registry.v5_final_evaluation_manifest_authored is False
    assert registry.v5_final_heldout_calibration_assessment_authored is False
    assert registry.next_authorized_artifact == "v5-calibration-curve-coverage-fixtures"


def test_registry_retains_exact_split_case_and_observation_budgets() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(_REGISTRY_PATH)

    split_counts: dict[str, int] = {}
    for family in registry.families:
        split_counts[family.split.value] = (
            split_counts.get(family.split.value, 0) + len(family.reserved_case_ids)
        )

    assert split_counts == {
        "calibration": 48,
        "final_evaluation": 36,
        "adversarial_regression": 12,
    }
    assert registry.observation_budget.calibration_observation_count == 192
    assert registry.observation_budget.final_evaluation_observation_count == 144
    assert registry.observation_budget.adversarial_regression_observation_count == 48


def test_final_families_are_quarantined_and_balanced_by_workload() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(_REGISTRY_PATH)

    final_families = [
        family
        for family in registry.families
        if family.split.value == "final_evaluation"
    ]

    assert len(final_families) == 4
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(len(family.reserved_case_ids) == 9 for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)
    assert all(
        family.workload_allocation.structured_text_case_count == 3
        and family.workload_allocation.code_case_count == 3
        and family.workload_allocation.open_ended_chat_case_count == 3
        for family in final_families
    )


def test_schema_only_root_rejects_case_bearing_directories(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "inputs").mkdir()

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_schema_only_fixture_root(root)

    assert error.value.code is _VIOLATION_CODE.SCHEMA_ONLY_BOUNDARY_VIOLATION


def test_schema_only_root_rejects_a_manifest_before_case_authoring(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "calibration_manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_schema_only_fixture_root(root)

    assert error.value.code is _VIOLATION_CODE.SCHEMA_ONLY_BOUNDARY_VIOLATION


def test_schema_only_root_rejects_historical_data_bearing_markers(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    ledger_path = root / "authoring_ledger.md"
    ledger_path.write_text(
        ledger_path.read_text(encoding="utf-8") + "\nCRV4-201\n",
        encoding="utf-8",
    )

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_schema_only_fixture_root(root)

    assert error.value.code is _VIOLATION_CODE.HISTORICAL_EVIDENCE_REFERENCE


def test_registry_rejects_any_claim_that_case_or_final_assets_exist() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["v5_final_evaluation_runtime_or_outcome_assets_authored"] = True

    with pytest.raises(ValidationError):
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)


def test_registry_rejects_case_reservation_drift() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["families"][0]["reserved_case_ids"][0] = "CSV5-102"

    with pytest.raises(ValidationError):
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)
