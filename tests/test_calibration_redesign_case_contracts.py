"""Regression tests for fresh calibration-redesign case contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from specsafe.traces import (
    CalibrationRedesignCaseLoadError,
    CalibrationRedesignCaseViolationCode,
    CalibrationRedesignExpectedOutcomes,
    CalibrationRedesignRuntimeInput,
    load_calibration_redesign_replay_case,
    load_calibration_redesign_scenario_family_registry,
)

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign"
    / "scenario_family_registry.json"
)


def _runtime_payload() -> dict[str, Any]:
    return {
        "schema_version": "calibration-redesign-trace-v1",
        "fixture_set_id": "synthetic-calibration-redesign-v1",
        "fixture_set_version": "1.0.0",
        "fixture_id": "CRV1-001-calibration-broad-range-low",
        "case_id": "CRV1-001",
        "trace_id": "crv1-trace-001",
        "request_id": "crv1-request-001",
        "scenario_family_id": "CRV1-CAL-BROAD-RANGE",
        "split": "calibration",
        "data_role": "calibration",
        "source_type": "synthetic",
        "generation_note": "Self-authored fresh calibration case with lawful confidence inputs.",
        "contexts": [
            {
                "trace_id": "crv1-trace-001",
                "request_id": "crv1-request-001",
                "workload_type": "structured_text",
                "decode_round": 0,
                "block_position_index": 1,
                "visible_prefix_token_ids": [],
                "conditional_survival_confidence": 0.78,
                "capacity_snapshot": {
                    "profile_id": "synthetic-calibration-v1",
                    "source": "synthetic",
                    "active_request_count": 2,
                    "verification_batch_tokens": 4,
                },
            },
            {
                "trace_id": "crv1-trace-001",
                "request_id": "crv1-request-001",
                "workload_type": "structured_text",
                "decode_round": 0,
                "block_position_index": 2,
                "visible_prefix_token_ids": [501],
                "conditional_survival_confidence": 0.67,
                "capacity_snapshot": {
                    "profile_id": "synthetic-calibration-v1",
                    "source": "synthetic",
                    "active_request_count": 2,
                    "verification_batch_tokens": 5,
                },
            },
        ],
    }


def _outcomes_payload() -> dict[str, Any]:
    return {
        "schema_version": "calibration-redesign-trace-v1",
        "fixture_set_id": "synthetic-calibration-redesign-v1",
        "fixture_set_version": "1.0.0",
        "fixture_id": "CRV1-001-calibration-broad-range-low",
        "case_id": "CRV1-001",
        "trace_id": "crv1-trace-001",
        "scenario_family_id": "CRV1-CAL-BROAD-RANGE",
        "split": "calibration",
        "data_role": "calibration",
        "source_type": "synthetic",
        "provenance_note": "Self-authored post-hoc labels retained outside runtime input.",
        "outcomes": [
            {
                "trace_id": "crv1-trace-001",
                "decode_round": 0,
                "block_position_index": 1,
                "candidate_token_id": 501,
                "observed_acceptance": True,
                "prefix_survival_label": True,
            },
            {
                "trace_id": "crv1-trace-001",
                "decode_round": 0,
                "block_position_index": 2,
                "candidate_token_id": 502,
                "observed_acceptance": False,
                "prefix_survival_label": False,
            },
        ],
    }


def _write_case_assets(tmp_path: Path) -> tuple[Path, Path]:
    runtime_path = tmp_path / "CRV1-001.json"
    outcomes_path = tmp_path / "CRV1-001.json.outcomes"
    runtime_path.write_text(json.dumps(_runtime_payload()), encoding="utf-8")
    outcomes_path.write_text(json.dumps(_outcomes_payload()), encoding="utf-8")
    return runtime_path, outcomes_path


def test_loader_accepts_a_case_declared_by_its_scenario_family(tmp_path: Path) -> None:
    registry = load_calibration_redesign_scenario_family_registry(REGISTRY_PATH)
    runtime_path, outcomes_path = _write_case_assets(tmp_path)

    replay_case = load_calibration_redesign_replay_case(runtime_path, outcomes_path, registry)

    assert replay_case.runtime_input.case_id == "CRV1-001"
    assert replay_case.expected_outcomes.scenario_family_id == "CRV1-CAL-BROAD-RANGE"


def test_runtime_input_rejects_evaluation_only_outcomes() -> None:
    payload = _runtime_payload()
    payload["observed_acceptance"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CalibrationRedesignRuntimeInput.model_validate(payload)


def test_loader_rejects_runtime_and_outcome_family_mismatch(tmp_path: Path) -> None:
    registry = load_calibration_redesign_scenario_family_registry(REGISTRY_PATH)
    runtime_path, outcomes_path = _write_case_assets(tmp_path)
    outcomes_payload = _outcomes_payload()
    outcomes_payload["scenario_family_id"] = "CRV1-CAL-POSITIONAL-DECAY"
    outcomes_path.write_text(json.dumps(outcomes_payload), encoding="utf-8")

    with pytest.raises(CalibrationRedesignCaseLoadError) as error:
        load_calibration_redesign_replay_case(runtime_path, outcomes_path, registry)

    assert error.value.code is CalibrationRedesignCaseViolationCode.CASE_PROVENANCE_MISMATCH


def test_loader_rejects_case_id_not_declared_by_its_scenario_family(tmp_path: Path) -> None:
    registry = load_calibration_redesign_scenario_family_registry(REGISTRY_PATH)
    runtime_path, outcomes_path = _write_case_assets(tmp_path)
    runtime_payload = _runtime_payload()
    outcomes_payload = _outcomes_payload()
    runtime_payload["case_id"] = "CRV1-099"
    outcomes_payload["case_id"] = "CRV1-099"
    runtime_path.write_text(json.dumps(runtime_payload), encoding="utf-8")
    outcomes_path.write_text(json.dumps(outcomes_payload), encoding="utf-8")

    with pytest.raises(CalibrationRedesignCaseLoadError) as error:
        load_calibration_redesign_replay_case(runtime_path, outcomes_path, registry)

    assert error.value.code is CalibrationRedesignCaseViolationCode.REGISTRY_CASE_MISMATCH


def test_expected_outcomes_reject_non_cumulative_prefix_label() -> None:
    payload = _outcomes_payload()
    outcomes = payload["outcomes"]
    assert isinstance(outcomes, list)
    outcomes[1]["prefix_survival_label"] = True

    with pytest.raises(ValidationError, match="prefix_survival_label"):
        CalibrationRedesignExpectedOutcomes.model_validate(payload)
