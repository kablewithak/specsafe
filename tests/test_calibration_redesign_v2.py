"""Regression tests for V2 registry provenance and governed case-asset boundaries."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.contracts.models import TraceDataRole, TraceSplit
from specsafe.traces.calibration_redesign_v2 import (
    CalibrationRedesignV2ProposalLoadError,
    CalibrationRedesignV2ProposalViolationCode,
    CalibrationRedesignV2RegistryLoadError,
    CalibrationRedesignV2RegistryViolationCode,
    assert_calibration_redesign_v2_case_authoring_fixture_root,
    assert_calibration_redesign_v2_proposal_only_fixture_root,
    assert_calibration_redesign_v2_registry_finalization_fixture_root,
    build_calibration_redesign_v2_scenario_family_registry,
    load_calibration_redesign_v2_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v2_manifest import (
    CalibrationRedesignV2CalibrationManifestLoadError,
    CalibrationRedesignV2CalibrationManifestViolationCode,
    build_calibration_redesign_v2_calibration_manifest,
    load_calibration_redesign_v2_calibration_manifested_fixture_set,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"


def _root_copy(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(
        V2_FIXTURE_ROOT,
        root,
        ignore=shutil.ignore_patterns(
            "inputs",
            "expected_outcomes",
            "calibration_manifest.json",
            "final_evaluation_manifest.json",
        ),
    )
    generated_registry = root / "scenario_family_registry.json"
    generated_registry.unlink(missing_ok=True)
    return root


def _finalized_root_copy(tmp_path: Path) -> Path:
    root = _root_copy(tmp_path)
    build_calibration_redesign_v2_scenario_family_registry(root)
    return root


def _registry_payload(root: Path) -> dict[str, object]:
    return json.loads((root / "scenario_family_registry.json").read_text(encoding="utf-8"))


def _write_registry(root: Path, payload: dict[str, object]) -> Path:
    path = root / "scenario_family_registry.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_finalized_registry_loads_with_reviewed_case_ranges_and_quarantine(
    tmp_path: Path,
) -> None:
    root = _finalized_root_copy(tmp_path)
    registry = load_calibration_redesign_v2_scenario_family_registry(
        root / "scenario_family_registry.json"
    )
    families_by_split = {
        split: tuple(family for family in registry.families if family.split is split)
        for split in TraceSplit
    }

    assert registry.registry_status == "finalized_for_case_contract_authoring"
    assert registry.v2_runtime_or_outcome_assets_authored is False
    assert registry.v2_manifests_authored is False
    assert len(families_by_split[TraceSplit.CALIBRATION]) == 3
    assert len(families_by_split[TraceSplit.FINAL_EVALUATION]) == 3
    assert all(
        family.primary_data_role is TraceDataRole.CALIBRATION
        for family in families_by_split[TraceSplit.CALIBRATION]
    )
    assert all(
        family.is_final_evaluation_quarantined
        for family in families_by_split[TraceSplit.FINAL_EVALUATION]
    )
    assert sum(len(family.case_ids) for family in families_by_split[TraceSplit.CALIBRATION]) == 12
    assert (
        sum(len(family.case_ids) for family in families_by_split[TraceSplit.FINAL_EVALUATION]) == 9
    )


def test_finalization_root_permits_only_governance_json(tmp_path: Path) -> None:
    root = _finalized_root_copy(tmp_path)

    assert_calibration_redesign_v2_registry_finalization_fixture_root(root)


def test_proposal_only_guard_rejects_finalized_registry_root(tmp_path: Path) -> None:
    root = _finalized_root_copy(tmp_path)

    with pytest.raises(CalibrationRedesignV2ProposalLoadError) as error_info:
        assert_calibration_redesign_v2_proposal_only_fixture_root(root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION
    )


def test_finalization_root_rejects_runtime_asset_before_authoring_boundary(
    tmp_path: Path,
) -> None:
    root = _finalized_root_copy(tmp_path)
    runtime_path = root / "inputs" / "cases" / "CRV2-101.json"
    runtime_path.parent.mkdir(parents=True)
    runtime_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV2RegistryLoadError) as error_info:
        assert_calibration_redesign_v2_registry_finalization_fixture_root(root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2RegistryViolationCode.FINALIZATION_BOUNDARY_VIOLATION
    )


def test_case_authoring_root_permits_only_governed_runtime_and_outcome_paths(
    tmp_path: Path,
) -> None:
    root = _finalized_root_copy(tmp_path)
    runtime_path = root / "inputs" / "cases" / "CRV2-101.json"
    outcomes_path = root / "expected_outcomes" / "cases" / "CRV2-101.json"
    runtime_path.parent.mkdir(parents=True)
    outcomes_path.parent.mkdir(parents=True)
    runtime_path.write_text("{}\n", encoding="utf-8")
    outcomes_path.write_text("{}\n", encoding="utf-8")

    assert_calibration_redesign_v2_case_authoring_fixture_root(root)


def test_case_authoring_root_rejects_unapproved_json_or_manifest(
    tmp_path: Path,
) -> None:
    root = _finalized_root_copy(tmp_path)
    invalid_path = root / "inputs" / "cases" / "not-a-v2-case.json"
    invalid_path.parent.mkdir(parents=True)
    invalid_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV2RegistryLoadError) as error_info:
        assert_calibration_redesign_v2_case_authoring_fixture_root(root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2RegistryViolationCode.CASE_AUTHORING_BOUNDARY_VIOLATION
    )

    invalid_path.unlink()
    (root / "calibration_manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV2RegistryLoadError) as error_info:
        assert_calibration_redesign_v2_case_authoring_fixture_root(root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2RegistryViolationCode.CASE_AUTHORING_BOUNDARY_VIOLATION
    )


def test_finalized_registry_rejects_changed_proposal_hash(tmp_path: Path) -> None:
    root = _finalized_root_copy(tmp_path)
    payload = _registry_payload(root)
    payload["proposal_sha256"] = "0" * 64
    registry_path = _write_registry(root, payload)

    with pytest.raises(CalibrationRedesignV2RegistryLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry(registry_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH
    )


def test_finalized_registry_rejects_v1_case_reference(tmp_path: Path) -> None:
    root = _finalized_root_copy(tmp_path)
    payload = _registry_payload(root)
    families = payload["families"]
    assert isinstance(families, list)
    first_family = families[0]
    assert isinstance(first_family, dict)
    case_ids = first_family["case_ids"]
    assert isinstance(case_ids, list)
    case_ids[0] = "CRV1-001"
    registry_path = _write_registry(root, payload)

    with pytest.raises(CalibrationRedesignV2RegistryLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry(registry_path)

    assert error_info.value.code is CalibrationRedesignV2RegistryViolationCode.V1_EVIDENCE_REFERENCE


def test_finalized_registry_rejects_case_range_change_after_review(
    tmp_path: Path,
) -> None:
    root = _finalized_root_copy(tmp_path)
    payload = _registry_payload(root)
    families = payload["families"]
    assert isinstance(families, list)
    first_family = families[0]
    assert isinstance(first_family, dict)
    case_ids = first_family["case_ids"]
    assert isinstance(case_ids, list)
    case_ids[0] = "CRV2-999"
    registry_path = _write_registry(root, payload)

    with pytest.raises(CalibrationRedesignV2RegistryLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry(registry_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH
    )


EXPECTED_CALIBRATION_CASE_IDS = {f"CRV2-{case_number}" for case_number in range(101, 113)}
EXPECTED_CALIBRATION_FAMILIES = {
    "CRV2-CAL-GLOBAL-ORDINAL",
    "CRV2-CAL-CROSS-CONTEXT",
    "CRV2-CAL-DOMAIN-BOUNDARIES",
}


def _calibration_manifest_root_copy(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(V2_FIXTURE_ROOT, root)
    return root


def test_v2_calibration_manifest_verifies_complete_committed_corpus(tmp_path: Path) -> None:
    fixture_root = _calibration_manifest_root_copy(tmp_path)

    manifest_path = build_calibration_redesign_v2_calibration_manifest(fixture_root)
    fixture_set = load_calibration_redesign_v2_calibration_manifested_fixture_set(fixture_root)

    assert manifest_path.name == "calibration_manifest.json"
    assert fixture_set.manifest.case_count == 12
    assert fixture_set.manifest.observation_count == 48
    assert fixture_set.manifest.minimum_required_observation_count == 48
    assert len(fixture_set.cases) == 12
    assert {
        case.runtime_input.case_id for case in fixture_set.cases
    } == EXPECTED_CALIBRATION_CASE_IDS
    assert {
        case.runtime_input.scenario_family_id for case in fixture_set.cases
    } == EXPECTED_CALIBRATION_FAMILIES
    assert {case.runtime_input.split.value for case in fixture_set.cases} == {"calibration"}
    assert {case.runtime_input.data_role.value for case in fixture_set.cases} == {"calibration"}


def test_v2_calibration_manifest_loader_rejects_tampered_case_bytes(tmp_path: Path) -> None:
    fixture_root = _calibration_manifest_root_copy(tmp_path)
    build_calibration_redesign_v2_calibration_manifest(fixture_root)
    tampered_path = fixture_root / "inputs" / "cases" / "CRV2-109.json"
    tampered_path.write_bytes(tampered_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV2CalibrationManifestLoadError) as error_info:
        load_calibration_redesign_v2_calibration_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_v2_calibration_manifest_loader_rejects_tampered_aggregate_hash(tmp_path: Path) -> None:
    fixture_root = _calibration_manifest_root_copy(tmp_path)
    manifest_path = build_calibration_redesign_v2_calibration_manifest(fixture_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["aggregate_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV2CalibrationManifestLoadError) as error_info:
        load_calibration_redesign_v2_calibration_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_v2_calibration_manifest_builder_rejects_missing_case_pair(tmp_path: Path) -> None:
    fixture_root = _calibration_manifest_root_copy(tmp_path)
    (fixture_root / "expected_outcomes" / "cases" / "CRV2-112.json").unlink()

    with pytest.raises(CalibrationRedesignV2CalibrationManifestLoadError) as error_info:
        build_calibration_redesign_v2_calibration_manifest(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2CalibrationManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH
    )


def test_v2_calibration_manifest_keeps_calibration_inventory_isolated_after_final_manifest(
    tmp_path: Path,
) -> None:
    fixture_root = _calibration_manifest_root_copy(tmp_path)
    final_manifest = fixture_root / "final_evaluation_manifest.json"
    final_manifest.write_text("{\n  \"placeholder\": true\n}\n", encoding="utf-8")

    fixture_set = load_calibration_redesign_v2_calibration_manifested_fixture_set(fixture_root)

    assert {case.runtime_input.case_id for case in fixture_set.cases} == (
        EXPECTED_CALIBRATION_CASE_IDS
    )
    assert all(entry.case_id.startswith("CRV2-1") for entry in fixture_set.manifest.entries)
