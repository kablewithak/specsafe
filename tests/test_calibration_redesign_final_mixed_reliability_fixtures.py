"""Regression tests for quarantined final mixed-reliability fixture assets."""

from __future__ import annotations

import json
from pathlib import Path

from specsafe.contracts import TraceDataRole, TraceSplit
from specsafe.traces import (
    load_calibration_redesign_replay_case,
    load_calibration_redesign_scenario_family_registry,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign"
)
FAMILY_ID = "CRV1-FINAL-MIXED-RELIABILITY"
CASE_STEMS = (
    "CRV1-009-final-mixed-reliability-structured",
    "CRV1-010-final-mixed-reliability-open-ended-chat",
)
FINAL_CASE_IDS = frozenset({"CRV1-009", "CRV1-010"})


def _load_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_final_mixed_reliability_pairs_load_under_quarantined_registry() -> None:
    registry = load_calibration_redesign_scenario_family_registry(
        FIXTURE_ROOT / "scenario_family_registry.json"
    )
    family_by_id = {
        family.scenario_family_id: family
        for family in registry.families
    }
    family = family_by_id[FAMILY_ID]

    assert family.is_final_evaluation_quarantined is True
    assert family.split is TraceSplit.FINAL_EVALUATION
    assert family.primary_data_role is TraceDataRole.HELD_OUT_EVALUATION

    loaded_case_ids: set[str] = set()
    for case_stem in CASE_STEMS:
        replay_case = load_calibration_redesign_replay_case(
            FIXTURE_ROOT / "inputs" / "cases" / f"{case_stem}.json",
            FIXTURE_ROOT / "expected_outcomes" / f"{case_stem}.json",
            registry,
        )
        runtime = replay_case.runtime_input

        assert runtime.scenario_family_id == FAMILY_ID
        assert runtime.split is TraceSplit.FINAL_EVALUATION
        assert runtime.data_role is TraceDataRole.HELD_OUT_EVALUATION
        assert len(runtime.contexts) == 4
        loaded_case_ids.add(runtime.case_id)

    assert loaded_case_ids == FINAL_CASE_IDS


def test_final_runtime_assets_do_not_expose_post_hoc_outcomes() -> None:
    forbidden_runtime_fields = {
        "candidate_token_id",
        "observed_acceptance",
        "outcomes",
        "prefix_survival_label",
    }

    for case_stem in CASE_STEMS:
        runtime_payload = _load_payload(
            FIXTURE_ROOT / "inputs" / "cases" / f"{case_stem}.json"
        )
        outcome_payload = _load_payload(
            FIXTURE_ROOT / "expected_outcomes" / f"{case_stem}.json"
        )

        assert forbidden_runtime_fields.isdisjoint(runtime_payload)
        assert "outcomes" in outcome_payload
        assert runtime_payload["case_id"] == outcome_payload["case_id"]
        assert runtime_payload["trace_id"] == outcome_payload["trace_id"]


def test_fitted_temperature_artifact_excludes_quarantined_final_case_ids() -> None:
    artifact_path = (
        Path(__file__).resolve().parents[1]
        / "evidence"
        / "calibration"
        / "logit-temperature-scaling-v1"
        / "artifact.json"
    )
    artifact_payload = _load_payload(artifact_path)
    fitted_case_ids = set(artifact_payload["fitted_case_ids"])

    assert fitted_case_ids.isdisjoint(FINAL_CASE_IDS)
    assert artifact_payload["final_evaluation_accessed"] is False
    assert artifact_payload["runtime_control_eligible"] is False
