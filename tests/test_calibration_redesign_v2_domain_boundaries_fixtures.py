"""Regression coverage for the V2 confidence-domain boundary fixture family."""

from __future__ import annotations

import json
import math
from pathlib import Path

from specsafe.contracts.models import TraceDataRole, TraceSplit, WorkloadType
from specsafe.traces.calibration_redesign_v2_cases import (
    load_calibration_redesign_v2_replay_case,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = (
    PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
)
DOMAIN_BOUNDARY_CASE_IDS = ("CRV2-109", "CRV2-110", "CRV2-111", "CRV2-112")
CLIPPING_EPSILON = 0.000001


def test_v2_domain_boundary_assets_preserve_open_interval_and_separated_labels() -> (
    None
):
    confidences: list[float] = []
    outcome_count = 0

    for case_id in DOMAIN_BOUNDARY_CASE_IDS:
        runtime_payload = json.loads(
            (V2_FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(
                encoding="utf-8"
            )
        )
        replay_case = load_calibration_redesign_v2_replay_case(V2_FIXTURE_ROOT, case_id)
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes

        assert runtime.scenario_family_id == "CRV2-CAL-DOMAIN-BOUNDARIES"
        assert runtime.split is TraceSplit.CALIBRATION
        assert runtime.data_role is TraceDataRole.CALIBRATION
        assert len(runtime.contexts) == 4
        assert len(outcomes.outcomes) == 4
        assert all(
            context.workload_type is WorkloadType.STRUCTURED_TEXT
            for context in runtime.contexts
        )
        assert {
            context.capacity_snapshot.profile_id for context in runtime.contexts
        } == {"synthetic-v2-domain-boundary-neutral"}
        assert "observed_acceptance" not in runtime_payload
        assert "candidate_token_id" not in runtime_payload
        assert "prefix_survival_label" not in runtime_payload
        assert "clipped_confidence" not in runtime_payload
        assert "transformed_confidence" not in runtime_payload

        confidences.extend(
            context.conditional_survival_confidence for context in runtime.contexts
        )
        outcome_count += len(outcomes.outcomes)

    assert outcome_count == 16
    assert all(0.0 < confidence < 1.0 for confidence in confidences)
    assert any(confidence < CLIPPING_EPSILON for confidence in confidences)
    assert any(math.isclose(confidence, CLIPPING_EPSILON) for confidence in confidences)
    assert any(confidence > CLIPPING_EPSILON for confidence in confidences)
    assert any(confidence < 1.0 - CLIPPING_EPSILON for confidence in confidences)
    assert any(
        math.isclose(confidence, 1.0 - CLIPPING_EPSILON) for confidence in confidences
    )
    assert any(confidence > 1.0 - CLIPPING_EPSILON for confidence in confidences)
    assert not (V2_FIXTURE_ROOT / "calibration_manifest.json").exists()
    assert not (V2_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
