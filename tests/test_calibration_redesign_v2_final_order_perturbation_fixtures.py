"""Held-out V2 order-perturbation fixture integrity tests.

These tests validate only the third quarantined final-evaluation family. They do not
load a final-evaluation manifest, transform final confidences, score the frozen artifact,
or make any promotion decision.
"""

from __future__ import annotations

import json
from pathlib import Path

from specsafe.contracts.models import TraceDataRole, TraceSplit
from specsafe.traces.calibration_redesign_v2 import (
    assert_calibration_redesign_v2_calibration_manifest_fixture_root,
)
from specsafe.traces.calibration_redesign_v2_cases import (
    load_calibration_redesign_v2_replay_case,
)
from specsafe.traces.calibration_redesign_v2_manifest import (
    load_calibration_redesign_v2_calibration_manifested_fixture_set,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
ARTIFACT_PATH = (
    PROJECT_ROOT / "evidence" / "calibration" / "bounded-platt-scaling-v1" / "artifact.json"
)
FINAL_MANIFEST_PATH = V2_FIXTURE_ROOT / "final_evaluation_manifest.json"
EXPECTED_CASE_IDS = ("CRV2-207", "CRV2-208", "CRV2-209")
EXPECTED_FAMILY_ID = "CRV2-FINAL-ORDER-PERTURBATION"
EXPECTED_CALIBRATION_CASE_IDS = {f"CRV2-{case_number}" for case_number in range(101, 113)}


def test_final_order_perturbation_family_is_quarantined_and_preserves_fit_inputs() -> None:
    """Keep held-out cases typed, isolated, and absent from the frozen fit corpus."""

    assert_calibration_redesign_v2_calibration_manifest_fixture_root(V2_FIXTURE_ROOT)
    assert FINAL_MANIFEST_PATH.is_file()

    calibration_fixture_set = load_calibration_redesign_v2_calibration_manifested_fixture_set(
        V2_FIXTURE_ROOT
    )
    assert {
        case.runtime_input.case_id for case in calibration_fixture_set.cases
    } == EXPECTED_CALIBRATION_CASE_IDS
    assert all(
        entry.case_id not in EXPECTED_CASE_IDS for entry in calibration_fixture_set.manifest.entries
    )

    loaded_cases = tuple(
        load_calibration_redesign_v2_replay_case(V2_FIXTURE_ROOT, case_id)
        for case_id in EXPECTED_CASE_IDS
    )
    assert len(loaded_cases) == 3
    assert sum(len(case.runtime_input.contexts) for case in loaded_cases) == 12

    for case in loaded_cases:
        runtime = case.runtime_input
        outcomes = case.expected_outcomes
        assert runtime.split is TraceSplit.FINAL_EVALUATION
        assert runtime.data_role is TraceDataRole.HELD_OUT_EVALUATION
        assert runtime.scenario_family_id == EXPECTED_FAMILY_ID
        assert outcomes.split is TraceSplit.FINAL_EVALUATION
        assert outcomes.data_role is TraceDataRole.HELD_OUT_EVALUATION
        assert outcomes.scenario_family_id == EXPECTED_FAMILY_ID
        assert len(runtime.contexts) == 4
        assert len(outcomes.outcomes) == 4

        runtime_payload = json.loads(
            (V2_FIXTURE_ROOT / "inputs" / "cases" / f"{runtime.case_id}.json").read_text(
                encoding="utf-8"
            )
        )
        serialized_runtime = json.dumps(runtime_payload, sort_keys=True)
        assert "candidate_token_id" not in serialized_runtime
        assert "observed_acceptance" not in serialized_runtime
        assert "prefix_survival_label" not in serialized_runtime

    artifact_payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert artifact_payload["final_evaluation_accessed"] is False
    assert artifact_payload["runtime_control_eligible"] is False
    assert set(artifact_payload["fit_case_ids"]) == EXPECTED_CALIBRATION_CASE_IDS


def test_order_perturbation_preserves_pair_inventory_without_scoring() -> None:
    """Keep global pair inventory fixed while changing decode-order arrangement."""

    pair_sequences: list[tuple[tuple[float, bool], ...]] = []
    pair_inventories: list[frozenset[tuple[float, bool]]] = []

    for case_id in EXPECTED_CASE_IDS:
        replay_case = load_calibration_redesign_v2_replay_case(V2_FIXTURE_ROOT, case_id)
        outcomes_by_position = {
            outcome.block_position_index: outcome
            for outcome in replay_case.expected_outcomes.outcomes
        }
        pair_sequence = tuple(
            (
                context.conditional_survival_confidence,
                outcomes_by_position[context.block_position_index].observed_acceptance,
            )
            for context in replay_case.runtime_input.contexts
        )
        pair_sequences.append(pair_sequence)
        pair_inventories.append(frozenset(pair_sequence))

    assert len(set(pair_sequences)) == len(EXPECTED_CASE_IDS)
    assert len(set(pair_inventories)) == 1
